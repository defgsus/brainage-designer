import json
import os
import glob
import dataclasses
import hashlib
import warnings
from pathlib import Path
from typing import Iterable, Generator, List, Dict, Optional, Union, Any, Tuple, Callable

import nibabel

from bad import config, logger
from bad.util.filenames import *
from .base import Module, SourceModuleBase, ProcessModuleBase
from .object import *


class ModuleGraph:
    class SkipPolicy:
        NEVER = "never"
        EXISTS = "exists"
        UNCHANGED = "unchanged"

    @dataclasses.dataclass
    class TargetFile:
        filename: Path
        data: dict
        mtime: int

        def __lt__(self, other):
            if isinstance(other, ModuleGraph.TargetFile):
                return self.filename.__lt__(other.filename)
            raise TypeError(f"Can't compare TargetFile to {type(other).__name__}")

    def __init__(
            self,
            modules: Iterable[Module],
            target_path: Optional[Union[str, Path]] = None,
            skip_policy: str = SkipPolicy.NEVER,
            log_skipping: bool = False,
    ):
        """
        Execution of a preprocessing module pipeline.

        High level entry is `process()`.

        All other functions are helpers to the process function.

        :param modules:
            iterable of loaded Module instances

        :param target_path: str/Path, optional,
            If supplied, object results are stored in `config.DATA_PATH / target_path`.

        :param skip_policy: str,
            One of the `ModuleGraph.SkipPolicy` constants

        """
        assert skip_policy in (self.SkipPolicy.NEVER, self.SkipPolicy.EXISTS, self.SkipPolicy.UNCHANGED)

        self.modules = list(modules)
        self.target_path = None
        if target_path is not None:
            self.target_path = Path(target_path)
        self.skip_policy = skip_policy
        self.log_skipping = logger.Logger("SKIP") if log_skipping else False

        self.report: Dict[str, Any] = {}
        self.clear_report()

        self.modules_by_group: Dict[str, List[Module]] = {}
        self.modules_by_uuid: Dict[str, Module] = {}
        self.storage_paths: Dict[Module, str] = {}

        for module in self.modules:
            assert module.uuid, f"Can't build graph of module without uuid: {module}"

            if module.uuid in self.modules_by_uuid:
                raise AssertionError(f"Duplicate module uuid: {module}")
            self.modules_by_uuid[module.uuid] = module

            if module.group[0] not in self.modules_by_group:
                self.modules_by_group[module.group[0]] = []
            self.modules_by_group[module.group[0]].append(module)

        if self.modules_by_group.get("process"):
            storage_path_count = {}
            for module_idx, module in enumerate(self.modules_by_group["process"]):
                is_last_module = module_idx + 1 == len(self.modules_by_group["process"])
                if module.get_parameter_value("module_store_result") or is_last_module:
                    storage_path = module.get_parameter_value("module_result_path") or module.name
                    storage_path = storage_path.rstrip("/")
                    if storage_path not in storage_path_count:
                        storage_path_count[storage_path] = 1
                    else:
                        storage_path_count[storage_path] += 1
                        storage_path = f"{storage_path}{storage_path_count[storage_path]}"

                    self.storage_paths[module] = storage_path

    @property
    def source_modules(self) -> List[SourceModuleBase]:
        return self.modules_by_group.get("source") or []

    @property
    def filter_modules(self) -> List[SourceModuleBase]:
        return self.modules_by_group.get("filter") or []

    @property
    def processing_modules(self) -> List[ProcessModuleBase]:
        return self.modules_by_group.get("process") or []

    def clear_report(self):
        self.report = {
            "source_objects": 0,
            "target_objects": 0,
            "skipped_objects": 0,
        }

    def prepare_modules(self):
        """
        Prepare all modules

        TODO: Currently this can take a long time,
            e.g. `dataset_ixi` will download 4.5GB of data without progress indication
        """
        for m in self.modules:
            m.prepare()

    def get_source_object_counts(self) -> dict:
        count_map = {}
        for module in self.source_modules:
            try:
                count = module.get_object_count()
            except NotImplementedError:
                count = 0
                
            count_map[module.uuid] = count

        return count_map

    def process(
            self,
            source_types: Optional[Iterable[str]] = None,
            interval: int = 1,
            offset: int = 0,
            existing_target_callback: Optional[Callable[[dict], None]] = None,
    ) -> Generator[ModuleObject, None, None]:
        """
        Process the whole graph from "source" -> "filter" -> "process"
        and store results if `target_path` is defined.

        :param source_types: optional list of `ModuleObjectType` constants
        :param interval: int,
            interval between one and the next processed source object.
            Used for multiprocessing of a module graph.
        :param offset: int,
             offset to the source object count before selecting the interval

        :param existing_target_callback: callable,
            If defined it will be called for each existing
            target object for which processing has been skipped.

        :return: generates the (stored) target `ModuleObject` instances
        """
        self.clear_report()

        if self.skip_policy == self.SkipPolicy.NEVER:
            yield from self.iter_graph_objects(
                source_types=source_types,
                interval=interval,
                offset=offset,
            )

        else:
            existing_source_target_map = self.get_existing_source_target_map()
            if not existing_source_target_map:
                if self.log_skipping:
                    self.log_skipping.info("no target files found")
                yield from self.iter_graph_objects(
                    source_types=source_types,
                    interval=interval,
                    offset=offset,
                )
                return

            # build a map of objects that would be created by this graph
            stub_source_target_map = self.get_object_source_target_map(
                self.iter_graph_objects(
                    source_types=source_types,
                    interval=interval,
                    offset=offset,
                    stub=True,
                )
            )
            self.clear_report()

            yield from self.iter_graph_objects(
                source_types=source_types,
                interval=interval,
                offset=offset,
                # filter the source objects for which all target objects exist
                source_filter=lambda objects: self.filter_existing_objects(
                    objects=objects,
                    existing_source_target_map=existing_source_target_map,
                    stub_source_target_map=stub_source_target_map,
                    existing_target_callback=existing_target_callback,
                )
            )

    def iter_graph_objects(
            self,
            source_types: Optional[Iterable[str]] = None,
            interval: int = 1,
            offset: int = 0,
            stub: bool = False,
            source_filter: Optional[Callable] = None,
    ) -> Generator[ModuleObject, None, None]:
        """
        Process the whole graph, either in "stub" or normal mode.
        """
        source_objects = self.iter_source_objects(
            output_types=source_types,
            interval=interval,
            offset=offset,
            stub=stub,
        )

        if source_filter:
            source_objects = source_filter(source_objects)

        filtered_objects = self.filter_objects(
            objects=source_objects,
            stub=stub,
        )

        yield from self.process_objects(
            objects=filtered_objects,
            stub=stub,
        )

    def iter_source_objects(
            self,
            output_types: Optional[Iterable[str]] = None,
            interval: int = 1,
            offset: int = 0,
            stub: bool = False,
    ) -> Generator[ModuleObject, None, None]:
        output_types = set(output_types) if output_types else None
        for m in self.source_modules:
            if not output_types or set(m.output_types) & output_types:
                for obj in m.iter_objects(interval=interval, offset=offset, stub=stub):
                    if not output_types or obj.data_type in output_types:
                        self.report["source_objects"] += 1
                        yield obj

    def filter_objects(
            self,
            objects: Iterable[ModuleObject],
            stub: bool = False,
    ) -> Generator[ModuleObject, None, None]:
        filter_modules = self.filter_modules
        if not filter_modules:
            yield from objects
            return

        filtered_objects = objects
        for module in filter_modules:
            filtered_objects = module.filter_objects(filtered_objects, stub=stub)

        yield from filtered_objects

    def process_objects(
            self,
            objects: Iterable[ModuleObject],
            stub: bool = False,
    ) -> Generator[ModuleObject, None, None]:
        """
        Process the iterable of objects through all processing-objects.

        :param objects: iterable of `ModuleObject`
        :param stub: bool,
            Enables "fake" processing to build the object graph
        :return: generator of the resulting `ModuleObject`s
        """
        processed_objects = objects

        for idx, module in enumerate(self.processing_modules):
            is_final_object = idx + 1 == len(self.processing_modules)
            processed_objects = self._process_and_store_objects(
                module=module,
                objects=processed_objects,
                store_bypassed_objects=is_final_object,
                stub=stub,
            )

        for obj in processed_objects:
            self.report["target_objects"] += 1
            yield obj

    def _process_or_bypass_objects(
            self,
            module: Module,
            objects: Iterable[ModuleObject],
            stub: bool,
    ) -> Generator[Tuple[ModuleObject, bool], None, None]:
        """
        Process or bypass the objects

        Yields (<bypassed_object>, False) or (<processed_object>, True)
        """
        input_objects = []

        for object in objects:
            # bypass if data_type doesn't match
            if object.data_type not in module.input_types:
                yield object, False
            else:
                # TODO: might specify a limit of objects that are collected here
                #   and process the batch once the limit is reached
                input_objects.append(object)

        for object in module.process_objects(input_objects, stub=stub):
            yield object, True

    def _process_and_store_objects(
            self,
            module: ProcessModuleBase,
            objects: Iterable[ModuleObject],
            store_bypassed_objects: bool,
            stub: bool,
    ):
        for object, do_store in self._process_or_bypass_objects(
                module=module,
                objects=objects,
                stub=stub,
        ):
            if self.target_path and self.storage_paths.get(module):
                if do_store or store_bypassed_objects:

                    object = self._store_result_object(
                        module,
                        object=object,
                        target_path=self.target_path / self.storage_paths[module],
                        stub=stub,
                    )

            yield object

    def _store_result_object(
            self,
            module: Module,
            target_path: Path,
            object: ModuleObject,
            stub: bool = False,
    ) -> ModuleObject:
        if isinstance(object, (FileObject, ImageObject)):
            filename, sub_path = object.filename, object.sub_path
        else:
            return object

        dest_filename = target_path / str(sub_path).lstrip(os.path.sep) / filename
        global_dest_filename = config.join_data_path(dest_filename)

        file_mod_time = None
        if not stub:
            os.makedirs(global_dest_filename.parent, exist_ok=True)

            if isinstance(object, FileObject):
                global_dest_filename.write_bytes(object.read_bytes())

            elif isinstance(object, ImageObject):
                # global_dest_filename = strip_compression_extension(global_dest_filename)
                object.src.to_filename(global_dest_filename)

            file_mod_time = global_dest_filename.stat().st_mtime_ns

        stored_object = object.replace(
            action=module.action_dict(
                action_name="stored",
                filename=str(dest_filename),
                mtime=file_mod_time,
            )
        )

        if not stub:
            gobal_data_filename = add_file_extension(global_dest_filename, "bad", "json")
            gobal_data_filename.write_text(self._to_json(stored_object.to_dict()))

        return stored_object

    def iter_target_files(self) -> Generator[TargetFile, None, None]:
        """
        Yield all filenames (recursively in the `target_directory`)
        for which a "<filename>.bad.json" file exists.

        :return: generator of `TargetFile`
            `TargetFile.filename` is the filename of the target file relative to the `target_path`.
        """
        global_directory = config.join_data_path(self.target_path)

        for filename in glob.iglob(str(global_directory / "**" / "*.bad.json"), recursive=True):
            object_filename = Path(filename[:-9])
            if object_filename.exists():
                target_filename = object_filename.relative_to(global_directory)
                target_data = json.loads(Path(filename).read_text())
                if target_data.get("actions"):
                    # only supported for objects with these actions:
                    if (target_data["actions"][0]["name"] == "loaded"
                            and target_data["actions"][-1]["name"] == "stored"
                    ):
                        # unusual but check if modification time of file matches data in .bad.json file
                        mtime = target_data["actions"][-1]["data"].get("mtime")
                        if (self.skip_policy == self.SkipPolicy.EXISTS
                                or mtime == object_filename.stat().st_mtime_ns
                        ):
                            yield self.TargetFile(
                                filename=target_filename,
                                data=target_data,
                                mtime=mtime,
                            )

    def _get_checksum(self, content: Union[bytes, Dict[str, Any]]) -> str:
        if not isinstance(content, bytes):
            content = self._to_json(content).encode()
        return hashlib.sha224(content).hexdigest()

    def _to_json(self, data: Dict[str, Any]) -> str:
        return json.dumps(data, indent=2)

    def filter_existing_objects(
            self,
            objects: Iterable[ModuleObject],
            existing_source_target_map: Dict[str, Dict[str, Dict]],
            stub_source_target_map: Dict[str, Dict[str, Dict]],
            existing_target_callback: Optional[Callable[[dict], None]] = None,
    ) -> Generator[ModuleObject, None, None]:
        """
        Filters the objects by comparing with existing source-target-map.

        Data of existing targets for skipped source objects are passed to the `existing_target_callback`
        function if provided.
        """
        def _yield_targets(source_object: ModuleObject, existing_targets: dict):
            if not existing_target_callback:
                return
            if self.log_skipping:
                self.log_skipping.info(
                    f"yielding {len(existing_targets)} existing targets for {source_object}"
                )
            for target in existing_targets.values():
                existing_target_callback(target)

        for obj in objects:
            source_filename = obj.actions[0]["data"]["filename"]
            source_mtime = obj.actions[0]["data"]["mtime"]

            if source_filename not in existing_source_target_map:
                if self.log_skipping:
                    self.log_skipping.info("new source", source_filename)
                yield obj
                continue

            if source_filename not in stub_source_target_map:
                warning = (
                    f"Source object which is not in stub-objects: {source_filename}"
                    f" Can not decide if target files are missing"
                )
                warnings.warn(warning)
                if self.log_skipping:
                    self.log_skipping.info(warning)

                yield obj
                continue

            existing_targets = existing_source_target_map[source_filename]
            stub_targets = stub_source_target_map[source_filename]

            if set(existing_targets.keys()) != set(stub_targets.keys()):
                # at least one target file is missing
                if self.log_skipping:
                    self.log_skipping.info("missing target file(s) for source", source_filename)
                yield obj
                continue

            if self.skip_policy == self.SkipPolicy.EXISTS:
                # it's enough the target files exist
                if self.log_skipping:
                    self.log_skipping.info("all targets exist for source", source_filename)
                self.report["skipped_objects"] += 1
                _yield_targets(obj, existing_targets)
                continue

            # compare source modification date
            changed = False
            for existing_target in existing_targets.values():
                if existing_target["actions"][0]["data"]["mtime"] != source_mtime:
                    changed = True
                    break
            if changed:
                if self.log_skipping:
                    self.log_skipping.info("source mtime changed", source_filename)
                yield obj
                continue

            # compare action path
            changed = False
            for target_filename, desired_target in stub_targets.items():
                existing_target = existing_targets[target_filename]

                if len(desired_target["actions"]) != len(existing_target["actions"]):
                    if self.log_skipping:
                        self.log_skipping.info(
                            f"{len(existing_target['actions'])} recorded"
                            f" vs. {len(desired_target['actions'])} stubbed actions"
                            f" for source {source_filename}"
                        )
                    changed = True
                    break

                for desired_action, existing_action in zip(
                        desired_target["actions"], existing_target["actions"]
                ):
                    if not self._compare_action(desired_action, existing_action):
                        if self.log_skipping:
                            self.log_skipping.info(
                                f"recorded and stub action differs for {source_filename}"
                                f"\nrecorded: {existing_action}"
                                f"\nstubbed:  {desired_action}")
                        changed = True
                        break

                if changed:
                    break

            if changed:
                yield obj
            else:
                if self.log_skipping:
                    self.log_skipping.info("all targets are unchanged for source", source_filename)
                self.report["skipped_objects"] += 1
                _yield_targets(obj, existing_targets)

    def _compare_action(self, stub_action: dict, recorded_action: dict) -> bool:
        if stub_action["name"] != recorded_action["name"]:
            return False

        if stub_action["module"] != recorded_action["module"]:
            # print("\n", stub_action["module"], "\n", recorded_action["module"])
            return False

        return True

    def get_existing_source_target_map(self) -> Dict[str, Dict[str, Dict]]:
        source_target_map = {}
        for tf in self.iter_target_files():
            source_filename = tf.data["actions"][0]["data"]["filename"]
            target_filename = tf.data["actions"][-1]["data"]["filename"]

            if source_filename not in source_target_map:
                source_target_map[source_filename] = {}
            source_target_map[source_filename][target_filename] = tf.data
        return source_target_map

    def get_object_source_target_map(self, objects: Iterable[ModuleObject]) -> Dict[str, Dict[str, Dict]]:
        source_target_map = {}
        for obj in objects:
            source_filename = obj.actions[0]["data"]["filename"]
            target_filename = obj.actions[-1]["data"]["filename"]

            if source_filename not in source_target_map:
                source_target_map[source_filename] = {}
            source_target_map[source_filename][target_filename] = obj.to_dict()
        return source_target_map

    def create_object_from_target_description(self, data: dict) -> ModuleObject:
        target_filename = data["actions"][-1]["data"]["filename"]
        global_target_filename = config.join_data_path(target_filename)

        if data["object_class"] == "FileObjectMemory":
            obj = FileObjectMemory(
                content=global_target_filename.read_bytes(),
                filename=data["filename"],
                sub_path=data["sub_path"],
                source_path=data["source_path"],
                actions=data["actions"],
                source=data["source"],
            )
        elif data["object_class"] == "FileObject":
            obj = FileObject(
                filename=data["filename"],
                sub_path=data["sub_path"],
                source_path=data["source_path"],
                actions=data["actions"],
                source=data["source"],
            )
        elif data["object_class"] == "ImageObject":
            obj = ImageObject(
                src=nibabel.load(global_target_filename),
                filename=data["filename"],
                sub_path=data["sub_path"],
                source_path=data["source_path"],
                actions=data["actions"],
                source=data["source"],
            )

        else:
            raise TypeError(f"Unknown target object type '{data['object_class']}'")

        return obj