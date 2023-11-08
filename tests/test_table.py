import json
import unittest
from pathlib import Path

from bad import config
from bad.util.table import read_table
from tests.base import BadTestCase


class TestTable(BadTestCase):

    def test_read_csv_comma(self):
        rows = read_table(self.DATA_PATH / "ixi32" / "IXI-comma.csv")
        print(json.dumps(rows[:2], indent=2))
        self.assertEqual(
            [
                {
                    "IXI_ID": "1",
                    "SEX_ID (1=m, 2=f)": "1",
                    "HEIGHT": "170",
                    "WEIGHT": "80",
                    "ETHNIC_ID": "2",
                    "MARITAL_ID": "3",
                    "OCCUPATION_ID": "5",
                    "QUALIFICATION_ID": "2",
                    "DOB": "1968-02-22",
                    "DATE_AVAILABLE": "0",
                    "STUDY_DATE": "",
                    "AGE": ""
                },
                {
                    "IXI_ID": "2",
                    "SEX_ID (1=m, 2=f)": "2",
                    "HEIGHT": "164",
                    "WEIGHT": "58",
                    "ETHNIC_ID": "1",
                    "MARITAL_ID": "4",
                    "OCCUPATION_ID": "1",
                    "QUALIFICATION_ID": "5",
                    "DOB": "1970-01-30",
                    "DATE_AVAILABLE": "1",
                    "STUDY_DATE": "2005-11-18",
                    "AGE": "35.80"
                }
            ],
            rows[:2]
        )

    def test_read_xls(self):
        rows = read_table(self.DATA_PATH / "ixi32" / "IXI.xls")
        # print(json.dumps(rows[:2], indent=2))
        self.assertEqual(
            [
                {
                    "IXI_ID": 1.0,
                    "SEX_ID (1=m, 2=f)": 1.0,
                    "HEIGHT": 170.0,
                    "WEIGHT": 80.0,
                    "ETHNIC_ID": 2.0,
                    "MARITAL_ID": 3.0,
                    "OCCUPATION_ID": 5.0,
                    "QUALIFICATION_ID": 2.0,
                    "DOB": "1968-02-22",
                    "DATE_AVAILABLE": 0.0,
                    "STUDY_DATE": None,
                    "AGE": None
                },
                {
                    "IXI_ID": 2.0,
                    "SEX_ID (1=m, 2=f)": 2.0,
                    "HEIGHT": 164.0,
                    "WEIGHT": 58.0,
                    "ETHNIC_ID": 1.0,
                    "MARITAL_ID": 4.0,
                    "OCCUPATION_ID": 1.0,
                    "QUALIFICATION_ID": 5.0,
                    "DOB": "1970-01-30",
                    "DATE_AVAILABLE": 1.0,
                    "STUDY_DATE": "2005-11-18T00:00:00",
                    "AGE": 35.800136892539356,
                }
            ],
            rows[:2]
        )