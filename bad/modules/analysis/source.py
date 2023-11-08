import glob
import re
from pathlib import Path
from typing import Generator, List, Dict, Any

from bad import config
from bad.util.filenames import is_image_filename
from bad.util.table import read_table
from bad.modules.base import SourceModuleBase, ModuleGroup, ModuleTag
from bad.modules.object import *
from bad.modules.params import *
from bad.modules.source import FileSourceDirectoryModule


class AnalysisSourceModule(FileSourceDirectoryModule):

    name = "analysis_source"
    tags = [ModuleTag.ANALYSIS]
    output_types = [ImageObject.data_type]
    group = [*SourceModuleBase.group, ModuleGroup.IMAGE]
    help = """
    This module loads existing (preprocessed) images for the analysis stage.
    
    The filenames should contain each subject's ID which can be extracted via regular expressions.
    
    Attributes belonging to each subject can be read from a table file (CSV or XLS) and will be 
    associated with each image.
    """

    parameters = [
        ParameterSelect(
            name="use_for",
            human_name="use for",
            description="Option to directly limit the usage to the training set, the validation set or both",
            default_value="any",
            options=[
                ParameterSelect.Option("any", "train & validation"),
                ParameterSelect.Option("train", "train", ),
                ParameterSelect.Option("validation", "validation"),
            ]
        ),
        ParameterFilepath(
            name="source_directory",
            human_name="source directory",
            description="The directory containing the source files",
            default_value="/",
        ),
        ParameterString(
            name="glob_pattern",
            human_name="file glob pattern",
            description="The globbing pattern to search for files",
            default_value="*",
        ),
        ParameterBool(
            name="recursive",
            description="Recursively scan sub-directories",
            default_value=False,
        ),
        ParameterString(
            name="filename_regex",
            human_name="filename regular expression",
            description="A [regular expression](https://en.wikipedia.org/wiki/Regex) to extract"
                        " the subject id from each filename",
            default_value=r"[^\d]*(?P<id>\d+)",
            help="""            
            Various values can be extracted from the filename with 
            [named capturing groups](https://www.regular-expressions.info/named.html). 
            The one **required** group is `id` for the subject id.
            
            For example, the following regex extracts the subject id from the first sequence of digits
            found in the filename:
            ```
            [^\\d]*(?P<id>\\d+)
            ```
            - The first part `[^\d]*` matches everything **except** digits
            - The second part `(?P<id>\\d+)` is the named capturing group, extracting one or more digits
            
            If the filenames look like `image-001.nii`, `image-002.nii`, ... then the extracted IDs will
            be `001`, `002`, etc..
            """,
        ),
        ParameterFilename(
            name="table_file",
            human_name="attribute table",
            description="A table (CSV/XLS) file containing attributes for each image",
            default_value="",
            required=False,
        ),
        ParameterInt(
            name="table_file_sheet",
            human_name="table sheet",
            description="The index of the sheet inside an excel table, starting at zero",
            default_value=0,
            min_value=0,
            required=False,
            help="This is only required for excel files (XLS/XLSX)",
            visible_js="table_file",
        ),
        ParameterSelect(
            name="table_file_delimiter",
            human_name="table delimiter",
            description="Delimiter in CSV table file",
            default_value=",",
            options=[
                ParameterSelect.Option(",", "comma"),
                ParameterSelect.Option(";", "semicolon"),
                ParameterSelect.Option("\t", "tab"),
                ParameterSelect.Option(" ", "space"),
            ],
            help="""
            The character that is used to separate each column.
            
            Only required for CSV files.
            """,
            required=False,
            visible_js="table_file",
        ),
        ParameterStringMapping(
            name="table_mapping",
            human_name="attribute mapping",
            description="Mapping between attribute columns and own attribute names",
            visible_js="table_file",
            required=False,
        )
    ]

    def iter_filenames(
            self,
            require_id: bool = True,
    ) -> Generator[Tuple[Path, Dict[str, Any]], None, None]:
        """
        Yields all filenames with attributes from the filename regex.

        The filename is relative to `self.get_parameter_value("source_directory")`.

        :param require_id: bool
            If True, only filenames with the attribute `id` are yielded.
            If False, all filenames are yielded, even without `id` attribute or any attribute at all

        :return: generator of (Path, dict)
        """
        use_for = self.get_parameter_value("use_for")
        local_path = self.get_parameter_value("source_directory")
        global_path = config.join_data_path(local_path)
        recursive = self.get_parameter_value("recursive")
        glob_pattern = self.get_parameter_value("glob_pattern")
        id_regex = self.get_parameter_value("filename_regex")
        id_regex = re.compile(id_regex)

        if recursive and "**" not in glob_pattern:
            glob_pattern = Path("**") / glob_pattern

        base_attributes = {}
        if use_for != "any":
            base_attributes["_use_for"] = use_for

        for global_filename in glob.iglob(str(global_path / glob_pattern), recursive=recursive):
            # ignore own status files
            if global_filename.endswith(".bad.json"):
                continue

            if is_image_filename(global_filename):

                local_filename = Path(global_filename).relative_to(global_path)
                match = id_regex.match(str(local_filename))
                if match:
                    attributes = match.groupdict()
                    if attributes.get("id") or (not require_id):
                        yield local_filename, {**base_attributes, **attributes}

                elif not require_id:
                    yield local_filename, base_attributes

    def iter_filenames_with_table_attributes(
            self,
            require_id: bool = True,
            with_status: bool = True,
    ) -> Generator[Tuple[Path, Dict[str, Any]], None, None]:
        """
        Yields all filenames with the filename attributes and the
        table attributes matched via the `id`.

        The filename is relative to `self.get_parameter_value("source_directory")`.

        :return: generator of (Path, dict)
        """
        subject_attributes = self.get_table_mapping()

        for filename, attributes in self.iter_filenames(require_id=require_id):

            status = "no_id"

            if attributes.get("id") is not None:
                status = "not_in_table" if subject_attributes else "ok"

                file_id = self.normalize_id(attributes["id"])
                if file_id in subject_attributes:
                    status = "ok"
                    for key, value in subject_attributes[file_id].items():
                        attributes[key] = value
                        if not value and value != 0:
                            status = "no_attribute_value"

            if with_status:
                attributes["_status"] = status

            yield filename, attributes

    def open_table_file(self) -> List[Dict[str, Any]]:
        local_path = self.get_parameter_value("table_file")
        global_path = config.join_data_path(local_path)
        if not global_path.exists():
            raise IOError("Table file does not exist")
        if not global_path.is_file():
            raise IOError("Table filename is no file")
        return read_table(
            filename=global_path,
            delimiter=self.get_parameter_value("table_file_delimiter"),
            sheet_index=self.get_parameter_value("table_file_sheet")
        )

    def get_table_mapping(self) -> Dict[str, Dict[str, Any]]:
        """
        :return: dict of subject-id -> mapped attributes
        """
        table_mapping = {}
        if (
                self.get_parameter_value("table_file")
                and self.get_parameter_value("table_mapping")
        ):
            attribute_mapping = self.get_parameter_value("table_mapping")
            table_rows = self.open_table_file()

            id_column = None
            for key, value in attribute_mapping.items():
                if value == "id":
                    id_column = key
                    break

            if id_column:
                for row in table_rows:
                    row_id = self.normalize_id(row[id_column])
                    if row_id not in table_mapping:

                        table_mapping[row_id] = {
                            attribute_key: row.get(table_key)
                            for table_key, attribute_key in attribute_mapping.items()
                            if attribute_key != "id"
                        }

        return table_mapping

    @classmethod
    def normalize_id(cls, value: Union[int, str]) -> str:
        if value is None:
            return ""

        if isinstance(value, float):
            value = int(value)

        elif isinstance(value, str):
            if not value:
                return ""

            try:
                value = int(value.lstrip("0") or "0")
            except ValueError:
                pass

        return str(value)
