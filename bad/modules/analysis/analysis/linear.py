import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline

from bad.modules.params import *
from .base import RegressionModelBase


class LinearRegressionModel(RegressionModelBase):

    name = "analysis_linear"

    parameters = [
        ParameterSelect(
            name="regression",
            default_value="linear",
            options=[
                ParameterSelect.Option("linear", "Linear"),
                ParameterSelect.Option("ridge", "Ridge"),
            ],
        ),
        ParameterFloat(
            name="ridge_alpha",
            human_name="Alpha",
            default_value=1.,
            visible_js="regression === 'ridge'",
        ),
        ParameterBool(
            name="polynomial_features",
            default_value=False,
        ),
        ParameterInt(
            name="degree",
            human_name="Polynomial degree",
            default_value=3,
            visible_js="polynomial_features",
        ),
    ]

    def prepare(self):
        regression_name = self.get_parameter_value("regression")
        if regression_name == "linear":
            regression = LinearRegression()
        elif regression_name == "ridge":
            regression = Ridge(alpha=self.get_parameter_value("ridge_alpha"))
        else:
            raise ValueError(f"Unknown regression '{regression_name}'")

        if self.get_parameter_value("polynomial_features"):
            regression = Pipeline([
                ("poly", PolynomialFeatures(degree=self.get_parameter_value("degree"))),
                ("regression", regression)
            ])

        self.regression = regression
