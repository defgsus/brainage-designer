import os
import math
import time
from pathlib import Path
from typing import Union, List

import numpy as np
from tqdm import tqdm

from bad import config
from bad.modules import AnalysisModelBase
from bad.modules.form import Form
from bad.modules.params import *
from .reduction import AnalysisReduction


class Analysis:

    def __init__(
            self,
            reduction: AnalysisReduction,
            analysis_model: AnalysisModelBase,
            form_values: dict,
            run_callback: Optional[Callable] = None,
            verbose: bool = False,
    ):
        self.reduction = reduction
        self.analysis_model = analysis_model
        self.form_values = form_values
        self.run_callback = run_callback
        self.verbose = verbose
        self._results: List[dict] = []

    @classmethod
    def get_form(cls):
        form = Form("analysis_prediction")
        form.set_parameters([
            ParameterString(
                name="name", default_value="",
                required=False,
            ),
            ParameterText(
                name="description", default_value="",
                required=False,
            ),
            ParameterFilepath(
                name="target_path",
            ),
            ParameterString(
                name="target_attribute",
            ),
            ParameterBool(
                name="clamp_output",
                default_value=False,
            ),
            ParameterFloat(
                name="clamp_output_min",
                default_value=0.,
                visible_js="clamp_output",
            ),
            ParameterFloat(
                name="clamp_output_max",
                default_value=100.,
                visible_js="clamp_output",
            ),
        ])
        return form

    def get_parameter_value(self, name: str):
        form = self.get_form()
        return self.form_values.get(name, form.get_default_value(name))

    @property
    def target_path(self) -> Path:
        return config.join_data_path(self.get_parameter_value("target_path"))

    def train(self):
        target_path = self.target_path
        target_attribute = self.get_parameter_value("target_attribute")

        os.makedirs(target_path, exist_ok=True)

        num_runs = self.reduction.num_runs()

        run_iterable = range(num_runs)
        if self.verbose:
            run_iterable = tqdm(run_iterable, desc="runs")
        for run_index in run_iterable:

            reduction_path = target_path / "reduction"

            time_start = time.time()
            self.reduction.run_reduction(
                target_path=reduction_path,
                run_index=run_index,
            )
            reduction_time = time.time() - time_start

            features_training, attributes_training, \
                features_validation, attributes_validation = self.reduction.load_reduction(reduction_path)

            attribute_training = attributes_training.loc[:, target_attribute].to_numpy()
            attribute_validation = attributes_validation.loc[:, target_attribute].to_numpy()

            time_start = time.time()
            self.analysis_model.prepare()
            self.analysis_model.fit(
                features_training, attribute_training, features_validation, attribute_validation
            )
            training_time = time.time() - time_start

            output = self.analysis_model.predict(features_validation)
            if self.get_parameter_value("clamp_output"):
                output = np.clip(
                    output,
                    self.get_parameter_value("clamp_output_min"),
                    self.get_parameter_value("clamp_output_max"),
                )

            self._results.append({
                "run_index": run_index,
                "num_training_samples": features_training.shape[0],
                "num_validation_samples": features_validation.shape[0],
                "feature_size": features_training.shape[1],
                "reduction_time": reduction_time,
                "training_time": training_time,
                "target_value": target_attribute,
                "validation_loss_l1": float(np.abs(attribute_validation - output).sum() / output.shape[0]),
                "validation_loss_l2": float(((attribute_validation - output) ** 2).sum() / output.shape[0]),
                "training_value_average": float(attribute_training.mean()),
                "training_value_std": float(attribute_training.std()),
                "validation_value_average": float(attribute_validation.mean()),
                "validation_value_std": float(attribute_validation.std()),
                "predicted_value_average": float(output.mean()),
                "predicted_value_std": float(output.std()),
                "predicted_values": {
                    attr["id"]: float(value)
                    for (idx, attr), value in zip(attributes_validation.iterrows(), output)
                },
                # Note: error is reversed here to match the sign of the "brainAGE score"
                "predicted_value_errors": {
                    attr["id"]: float(value - attr[target_attribute])
                    for (idx, attr), value in zip(attributes_validation.iterrows(), output)
                },
                "training_value_min": float(features_training.min()),
                "training_value_max": float(features_training.max()),
                "validation_value_min": float(features_training.min()),
                "validation_value_max": float(features_training.max()),
            })
            if self.run_callback:
                self.run_callback(self._results[-1])

            if self.verbose:
                print(f"\n-- run #{run_index} --")
                for key in ("validation_loss_l1", "validation_loss_l2"):
                    print(" ", key, self._results[-1][key])

    def report(self) -> dict:
        average = self.build_average_result(self._results)

        return {
            "average": average,
            "runs": self._results,
        }

    @classmethod
    def build_average_result(cls, results: Iterable[dict]) -> dict:
        average = {
            "num_runs": 0,
        }
        for result in results:
            average["num_runs"] += 1
            for key, value in result.items():
                if key != "run_index" and isinstance(value, int):
                    average[key] = average.get(key, 0) + value
                elif isinstance(value, float) and not math.isnan(value):
                    average[key] = average.get(key, 0) + value

                elif key in ("predicted_values", "predicted_value_errors"):
                    if key not in average:
                        average[key] = {}
                    for sub_key, sub_value in value.items():
                        if not math.isnan(sub_value):
                            if sub_key not in average[key]:
                                average[key][sub_key] = []
                            average[key][sub_key].append(sub_value)

        for key in ("predicted_values", "predicted_value_errors"):
            if key in average:
                average[key] = {
                    sub_key: sum(sub_value) / len(sub_value)
                    for sub_key, sub_value in average[key].items()
                }

        for key, value in average.items():
            if key != "num_runs" and isinstance(value, (int, float)):
                average[key] = value / max(1, average["num_runs"])

        return average
