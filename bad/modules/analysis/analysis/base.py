import numpy as np
import pandas as pd

from bad.modules.base import Module, ModuleGroup, ModuleTag


class AnalysisModelBase(Module):

    group = [ModuleGroup.PREDICTION]
    tags = [ModuleTag.ANALYSIS]

    def fit(
            self,
            features_training: np.ndarray,
            targets_training: np.ndarray,
            features_validation: np.ndarray,
            targets_validation: np.ndarray,
    ):
        raise NotImplementedError

    def predict(
            self,
            features: np.ndarray,
    ) -> np.ndarray:
        raise NotImplementedError


class RegressionModelBase(AnalysisModelBase):

    def prepare(self):
        """Override to define self.regression"""
        raise NotImplementedError

    def fit(
            self,
            features_training: np.ndarray,
            targets_training: np.ndarray,
            features_validation: np.ndarray,
            targets_validation: np.ndarray,
    ):
        self.regression.fit(features_training, targets_training)

    def predict(
            self,
            features: np.ndarray,
    ) -> np.ndarray:
        return self.regression.predict(features)
