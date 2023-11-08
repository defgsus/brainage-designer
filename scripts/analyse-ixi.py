from pathlib import Path
import json
import math
import pickle
from typing import Optional, Iterable

from tqdm import tqdm

import numpy as np
import pandas as pd
import nibabel

from bad import config
from bad.modules import *
from bad.util.image import *
from bad.plugins.analysis.reduction import AnalysisReduction
from bad.plugins.analysis.analysis import Analysis


PATH = Path(__file__).resolve().parent


def run_analysis_ixi(
        extra_modules: Iterable[Module],
        analysis_model: AnalysisModelBase,
        image_path: Union[str, Path],
        table_file: Union[str, Path],
        target_path: Optional[Union[str, Path]] = None,
        filename_regex: str = r"rp1[^\d]*(?P<id>\d+)",
        target_attribute: str = "age",
        validation_percent: float = 10,
        num_repeat: int = 10,
        normalize_features: str = "zero_one",
        normalize_feature_sets: str = "both",
) -> dict:
    target_path = Path(target_path if target_path else "/tmp/brainage")

    reduction = AnalysisReduction(
        modules=[
            ModuleFactory.new_module("analysis_source", {
                "source_directory": str(image_path),
                "glob_pattern": "*.nii*",
                "filename_regex": filename_regex,
                "table_file": str(table_file),
                "table_mapping": {"IXI_ID": "id", "AGE": "age"},
            }, prepare=True),
            *extra_modules,
        ],
        separation_values={
            "separation": "cross_validation",
            "split_number": validation_percent,
            "split_number_type": "percent",
            "num_repeat": num_repeat,
        },
        reduction_values={
            "normalize_features": normalize_features,
            "normalize_feature_sets": normalize_feature_sets,
        }
    )
    reduction.init()

    analysis = Analysis(
        reduction=reduction,
        analysis_model=analysis_model,
        form_values={
            "target_path": str(target_path),
            "target_attribute": target_attribute,
        },
        verbose=True,
    )

    analysis.train()

    report = analysis.report()
    print(json.dumps(report["average"], indent=2))
    for key in ("validation_loss_l1", "validation_loss_l2"):
        print("average", key, report["average"][key])

    return report


def run_single():
    run_analysis_ixi(
        extra_modules=[
            #ModuleFactory.new_module("image_slice", {"slice_axis": 1, "slice_offset": 120}, prepare=True),
            ModuleFactory.new_module("reduction_pca", {
                "size": 100,
                "reduce_sets_separately": False,
            }, prepare=True),
        ],
        #analysis_model=ModuleFactory.new_module("analysis_linear"),
        analysis_model=ModuleFactory.new_module("analysis_rvr", {"n_iter": 1000}),
        image_path="prog/data/datasets/ixi/cat12_r1450/rp1/",
        table_file="prog/data/datasets/ixi/IXI.xls",
        validation_percent=10,
        num_repeat=5,
        normalize_feature_sets="training",
    )


def run_slices():
    img = nibabel.load("/home/bergi/prog/data/datasets/ixi/cat12_r1450/rp1/rp1IXI002-Guys-0828-T1_affine.nii")
    results = []
    for slice_axis in range(3):
        padding = 10 if slice_axis == 2 else 14
        for slice_offset in tqdm(range(padding, img.shape[slice_axis] - padding), desc="slice offset"):
            print(f"---- axis={slice_axis} offset={slice_offset} ----")

            report = run_analysis_ixi(
                extra_modules=[
                    ModuleFactory.new_module("image_slice", {
                        "slice_axis": slice_axis,
                        "slice_offset": slice_offset
                    }, prepare=True),
                    ModuleFactory.new_module("reduction_pca", {
                        "size": 100,
                        "reduce_sets_separately": False,
                    }, prepare=True),
                ],
                #analysis_model=ModuleFactory.new_module("analysis_linear"),
                analysis_model=ModuleFactory.new_module("analysis_rvr", {"n_iter": 1000}),
                image_path="prog/data/datasets/ixi/cat12_r1450/rp1/",
                table_file="prog/data/datasets/ixi/IXI.xls",
                validation_percent=10,
                num_repeat=3,
                normalize_feature_sets="training",
            )

            results.append({
                "slice_axis": slice_axis,
                "slice_offset": slice_offset,
                "average": report["average"],
            })

    Path("./slice-results.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":

    #run_single()
    run_slices()