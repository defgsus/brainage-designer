import numpy as np
import pandas as pd
from skrvm import RVR

from bad.modules.params import *
from .base import RegressionModelBase


class RVRModel(RegressionModelBase):

    name = "analysis_rvr"

    parameters = [
        ParameterSelect(
            name="kernel",
            default_value="rbf",
            options=[
                ParameterSelect.Option("linear", "Linear"),
                ParameterSelect.Option("rbf", "Gaussian"),
                ParameterSelect.Option("poly", "Polynomial"),
            ],
        ),
        ParameterInt(
            name="degree",
            human_name="Degree of polynomial kernel",
            default_value=3,
            visible_js="kernel === 'poly'",
        ),
        ParameterInt(
            name="n_iter",
            human_name="Number of iterations",
            default_value=3000,
        ),
        ParameterBool(
            name="bias",
            human_name="Use bias",
            default_value=True,
        ),
    ]

    def prepare(self):
        self.regression = RVR(
            kernel=self.get_parameter_value("kernel"),
            degree=self.get_parameter_value("degree"),
            n_iter=self.get_parameter_value("n_iter"),
            bias_used=self.get_parameter_value("bias"),
        )
