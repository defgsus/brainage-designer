import csv
import datetime
from pathlib import Path
from typing import Union, List, Dict, Any

import xlrd


def read_table(
        filename: Union[str, Path],
        delimiter: str = ",",
        skip_initial_space: bool = True,
        sheet_index: int = 0,
) -> List[Dict[str, Any]]:
    filename_lower = str(filename).lower()

    if filename_lower.endswith(".csv"):
        return _read_csv(
            filename=filename,
            delimiter=delimiter,
            skip_initial_space=skip_initial_space,
        )

    elif filename_lower.endswith(".xls") or filename_lower.endswith(".xlsx"):
        return _read_xls(
            filename=filename,
            sheet_index=sheet_index,
        )

    else:
        raise ValueError(f"Unrecognized table filename '{Path(filename).name}'")


def _read_csv(
        filename: Union[str, Path],
        delimiter: str,
        skip_initial_space: bool,
) -> List[Dict[str, Any]]:
    with open(filename) as fp:
        reader = csv.DictReader(
            fp,
            delimiter=delimiter,
            skipinitialspace=skip_initial_space,
        )

        return list(reader)


def _read_xls(
        filename: Union[str, Path],
        sheet_index: int,
) -> List[Dict[str, Any]]:
    workbook = xlrd.open_workbook(filename, ragged_rows=True)
    sheet = workbook.sheet_by_index(sheet_index)

    rows = []
    headers = {}
    column_types = {}
    for y in range(sheet.nrows):
        row_dict = {}
        row = sheet.row(y)
        for x, cell in enumerate(row):
            if y == 0:
                headers[x] = cell.value
            else:
                column_name = headers[x]
                value = cell.value

                if cell.ctype == 2:  # number
                    column_types[column_name] = 2

                elif cell.ctype == 3:  # date
                    column_types[column_name] = 3
                    value = xlrd.xldate_as_datetime(cell.value, workbook.datemode).isoformat()

                row_dict[column_name] = value

        if y != 0:
            for key in headers.values():
                if key not in row_dict:
                    row_dict[key] = None
            rows.append(row_dict)

    for column_name, column_type in column_types.items():
        if column_type in (2, 3):
            for row in rows:
                if row[column_name] == "":
                    row[column_name] = None

    return rows
