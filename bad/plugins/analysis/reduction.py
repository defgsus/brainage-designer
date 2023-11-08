import os
import random
import itertools
from pathlib import Path
from typing import List, Optional, Set, Tuple, Generator, Union, Iterable

import nibabel
import numpy as np
import pandas as pd

from bad import config
from bad.modules import *
from bad.util.image import nibabel_to_numpy_float
from bad.util.numpy_iterable import NumpyIterable


class AnalysisReduction:

    def __init__(
            self,
            modules: List[Module],
            separation_values: Optional[dict] = None,
            reduction_values: Optional[dict] = None,
    ):
        self.modules = modules
        self.separation_values = separation_values
        self.reduction_values = reduction_values
        self.files: List[dict] = []
        self.common_local_path = "/"
        self.attribute_names: List[str] = []

    @classmethod
    def get_separation_form(cls) -> Form:
        form = Form("analysis_separation")
        form.set_parameters([
            ParameterSelect(
                name="separation",
                default_value="keep",
                options=[
                    ParameterSelect.Option("keep", "training/validation as defined in source modules"),
                    ParameterSelect.Option("cross_validation", "random cross validation"),
                    ParameterSelect.Option("leave_n_out", "leave n out"),
                ]
            ),
            ParameterInt(
                name="split_number",
                human_name="validation size",
                default_value=10,
                min_value=1,
                visible_js="separation === 'cross_validation'",
            ),
            ParameterSelect(
                name="split_number_type",
                human_name="validation size type",
                default_value="percent",
                options=[
                    ParameterSelect.Option("percent", "percent"),
                    ParameterSelect.Option("absolute", "absolute number"),
                ],
                visible_js="separation === 'cross_validation'",
            ),
            ParameterInt(
                name="num_repeat",
                human_name="number of repetitions",
                default_value=1,
                min_value=1,
                visible_js="separation === 'cross_validation'",
            ),
            ParameterString(
                name="random_seed",
                human_name="random seed",
                description="Type anything for a fixed random seed",
                default_value="",
                required=False,
                visible_js="separation === 'cross_validation'",
            ),
            ParameterInt(
                name="num_leave_out",
                human_name="validation size",
                default_value=1,
                min_value=1,
                visible_js="separation === 'leave_n_out'",
            ),
        ])
        return form

    @classmethod
    def get_reduction_form(cls) -> Form:
        form = Form("analysis_reduction")
        form.set_parameters([
            ParameterSelect(
                name="normalize_single_image",
                default_value="no",
                options=[
                    ParameterSelect.Option("no", "no"),
                    ParameterSelect.Option("zero_one", "between 0 and 1"),
                    ParameterSelect.Option("plus_minus_one", "maximally +/-1"),
                ]
            ),
            ParameterSelect(
                name="normalize_features",
                default_value="zero_one",
                options=[
                    ParameterSelect.Option("no", "no"),
                    ParameterSelect.Option("zero_one", "between 0 and 1"),
                    ParameterSelect.Option("plus_minus_one", "maximally +/-1"),
                ]
            ),
            ParameterSelect(
                name="normalize_feature_sets",
                default_value="together",
                options=[
                    ParameterSelect.Option("together", "training & validation at once"),
                    ParameterSelect.Option("separate", "training & validation separately"),
                    ParameterSelect.Option("training", "normalize validation like training"),
                ],
                visible_js="normalize_features !== 'no'"
            ),
        ])
        return form

    def get_separation_value(self, name: str):
        form = self.get_separation_form()
        if self.separation_values:
            return self.separation_values.get(name, form.get_default_value(name))
        return form.get_default_value(name)

    def get_reduction_value(self, name: str):
        form = self.get_reduction_form()
        if self.reduction_values:
            return self.reduction_values.get(name, form.get_default_value(name))
        return form.get_default_value(name)

    @property
    def source_modules(self) -> List[AnalysisSourceModule]:
        return [m for m in self.modules if isinstance(m, AnalysisSourceModule)]

    @property
    def process_modules(self) -> List[ImageProcessModuleBase]:
        return [m for m in self.modules if isinstance(m, ImageProcessModuleBase)]

    @property
    def reduction_module(self) -> Optional[AnalysisReductionModuleBase]:
        for m in self.modules:
            if isinstance(m, AnalysisReductionModuleBase):
                return m

    def num_runs(self) -> int:
        separation_type = self.get_separation_value("separation")
        if separation_type == "keep":
            return 1

        elif separation_type == "cross_validation":
            return self.get_separation_value("num_repeat")

        elif separation_type == "leave_n_out":
            num_files = self.num_valid_files()
            return num_files // self.get_separation_value("num_leave_out")

        else:
            raise ValueError(f"Invalid separation type '{separation_type}'")

    def init(self, limit_files: Optional[int] = None):

        self.files = []
        attribute_names = set()
        do_break = False
        all_local_paths = []
        for module in self.source_modules:
            module_files: List[dict] = []
            for filename, attrs in module.iter_filenames_with_table_attributes(require_id=False):
                local_path = module.get_parameter_value("source_directory")
                all_local_paths.append(local_path)
                # global_path = config.join_data_path(local_path)

                module_files.append({"path": str(local_path / filename), "attributes": attrs})
                if attrs:
                    for key in attrs:
                        attribute_names.add(key)

                if limit_files is not None and len(self.files) >= limit_files:
                    do_break = True
                    break

            self.files += module_files

            if do_break:
                break

        self.attribute_names = sorted(attribute_names, key=lambda name: "" if name == "id" else name)
        self.files.sort(key=lambda f: f["path"])
        if all_local_paths:
            self.common_local_path = os.path.commonpath(all_local_paths)
        else:
            self.common_local_path = "/"
        for file in self.files:
            file["short_path"] = os.path.relpath(file["path"], self.common_local_path)

    def num_valid_files(self) -> int:
        count = 0
        for file in self.files:
            if file["attributes"].get("_status") == "ok":
                count += 1
        return count

    def valid_files(self) -> List[dict]:
        return [
            file
            for file in self.files
            if file["attributes"].get("_status") == "ok"
        ]

    def get_file_counts(self):
        counts = {
            "all": 0,
        }
        for file in self.files:
            counts["all"] += 1
            status = file["attributes"].get("_status") or "no_status"
            counts[status] = counts.get(status, 0) + 1

        return counts

    def split_files_to_train_and_validation(self, run_index: int = 0) -> Tuple[List[dict], List[dict]]:
        config = self.get_separation_form().get_values(self.separation_values)

        source_files = self.valid_files()

        return_files = ([], [])

        if config["separation"] == "keep":

            for file in source_files:
                if file["attributes"].get("_use_for") == "validation":
                    return_files[1].append(file)
                else:
                    return_files[0].append(file)

            return return_files

        if not config["random_seed"]:
            rng = random.SystemRandom()
        else:
            rng = random.Random(sum(ord(i) for i in config["random_seed"]) ^ run_index)

        if config["separation"] == "cross_validation":

            num_validation = config["split_number"]
            if config["split_number_type"] == "percent":
                num_validation = len(source_files) * num_validation / 100
            num_validation = int(num_validation)

            return_files[0].extend(source_files)
            while len(return_files[0]) and len(return_files[1]) < num_validation:
                return_files[1].append(
                    return_files[0].pop(rng.randrange(len(return_files[0])))
                )

        elif config["separation"] == "leave_n_out":
            num_leave_out = self.get_separation_value("num_leave_out")
            # TODO
            assert num_leave_out == 1

            for idx, file in enumerate(source_files):
                if run_index % len(source_files) == idx:
                    return_files[1].append(file)
                else:
                    return_files[0].append(file)

        else:
            raise ValueError(f"Unknown separation option '{config['separation']}'")

        return return_files

    def iter_image_objects(self, files: List[dict]) -> Generator[Tuple[ImageObject, dict], None, None]:
        for file in files:
            local_path = Path(file["path"])
            global_path = config.join_data_path(local_path)

            image = ImageObject(
                src=nibabel.load(global_path),
                filename=global_path.name,
                sub_path="",
                source_path=local_path.parent,
            )
            yield (
                image,
                file["attributes"],
            )

    def iter_processed_image_objects(self, files: List[dict]) -> Generator[Tuple[ImageObject, dict], None, None]:
        for image, attributes in self.iter_image_objects(files):
            for module in self.process_modules:
                image = next(module.process_objects([image]))

            yield image, attributes

    def run_reduction(self, target_path: Union[str, Path], run_index: int = 0):
        assert self.reduction_module, "Can not run reduction without reduction module"

        target_path = Path(target_path)

        training_files, validation_files = self.split_files_to_train_and_validation(run_index=run_index)
        #assert training_files, "Can not run reduction without training files"
        #assert validation_files, "Can not run reduction without validation files"

        training_iterable = self.iter_processed_image_objects(training_files)
        validation_iterable = self.iter_processed_image_objects(validation_files)

        os.makedirs(target_path, exist_ok=True)

        if self.reduction_module.get_parameter_value("reduce_sets_separately"):

            reduction_model_params = dict()
            features_t, attributes_t = self._reduce_images(
                images=training_iterable,
                num_images=len(training_files),
                reduction_model_params=reduction_model_params,
            )
            # reuse reduction model for validation
            features_v, attributes_v = self._reduce_images(
                images=validation_iterable,
                num_images=len(validation_files),
                reduction_model_params=reduction_model_params,
            )

        else:
            reduction_model_params = dict()
            features, attributes = self._reduce_images(
                images=itertools.chain(training_iterable, validation_iterable),
                num_images=len(training_files) + len(validation_files),
                reduction_model_params=reduction_model_params,
            )
            features_t = features[:len(training_files)]
            features_v = features[len(training_files):]
            attributes_t = attributes[:len(training_files)]
            attributes_v = attributes[len(training_files):]

        # -- set normalization --

        normalize_mode = self.get_reduction_value("normalize_features")
        normalze_set_mode = self.get_reduction_value("normalize_feature_sets")
        if normalize_mode != "no":

            if normalze_set_mode == "together":
                normalization_values = self._get_normalize_values(features_t, features_v, mode=normalize_mode)
                features_t = self._normalize(features_t, mode=normalize_mode, values=normalization_values)
                features_v = self._normalize(features_v, mode=normalize_mode, values=normalization_values)

            elif normalze_set_mode == "separate":
                features_t = self._normalize(features_t, mode=normalize_mode, values={})
                features_v = self._normalize(features_v, mode=normalize_mode, values={})

            elif normalze_set_mode == "training":
                normalization_values = {}
                features_t = self._normalize(features_t, mode=normalize_mode, values=normalization_values)
                # apply normalization to v with values of t
                features_v = self._normalize(features_v, mode=normalize_mode, values=normalization_values)

        np.save(str(target_path / "features-training.npy"), features_t)
        attributes_t.to_pickle(target_path / "attributes-training.pkl")
        np.save(str(target_path / "features-validation.npy"), features_v)
        attributes_v.to_pickle(target_path / "attributes-validation.pkl")

    def _reduce_images(
            self,
            images: Iterable[Tuple[ImageObject, dict]],
            num_images: int,
            reduction_model_params: dict,
    ) -> Tuple[np.ndarray, pd.DataFrame]:

        normalize_image_mode = self.get_reduction_value("normalize_single_image")

        attribute_table = []

        def _yield_images_and_collect_attributes() -> np.ndarray:
            for image, attributes in images:
                image = nibabel_to_numpy_float(image.src)

                if normalize_image_mode:
                    image = self._normalize(image, normalize_image_mode, {})

                if np.any(np.isnan(image)):
                    raise ValueError(f"NaN value in processed image id='{attributes['id']}'")

                yield image

                attribute_table.append(attributes)

        features = self.reduction_module.reduce_images(
            NumpyIterable(_yield_images_and_collect_attributes(), num_images),
            model_params=reduction_model_params,
        )

        return (
            features,
            pd.DataFrame(attribute_table).drop("_status", axis=1),
        )

    def _get_normalize_values(self, *datas: np.ndarray, mode: str) -> dict:
        values = {}
        for data in datas:
            min_v = data.min()
            if "min_v" not in values or min_v < values["min_v"]:
                values["min_v"] = min_v

            max_v = data.max()
            if "max_v" not in values or max_v > values["max_v"]:
                values["max_v"] = max_v

        return values

    def _normalize(self, data: np.ndarray, mode: str, values: dict) -> np.ndarray:
        if mode == "no":
            return data

        if not values:
            values.update(self._get_normalize_values(data, mode=mode))

        min_v, max_v = values["min_v"], values["max_v"]

        if mode == "zero_one":
            if min_v - max_v:
                data = (data - min_v) / (max_v - min_v)

        elif mode == "plus_minus_one":
            max_v = np.abs(data).max()
            if max_v:
                data /= max_v

        else:
            raise ValueError(f"Unknown normalization mode `{mode}`")

        return data

    def load_reduction(self, path: Union[str, Path]) -> Tuple[
        np.ndarray, pd.DataFrame, np.ndarray, pd.DataFrame,
    ]:
        path = Path(path)
        return (
            np.load(str(path / "features-training.npy")),
            pd.read_pickle(path / "attributes-training.pkl"),
            np.load(str(path / "features-validation.npy")),
            pd.read_pickle(path / "attributes-validation.pkl"),
        )

    def get_output_size(self) -> Optional[int]:
        size = None

        if self.reduction_module:

            for image, attrs in self.iter_image_objects(self.valid_files()):
                size = self.reduction_module.get_output_size(nibabel_to_numpy_float(image.src))
                break

        return size
