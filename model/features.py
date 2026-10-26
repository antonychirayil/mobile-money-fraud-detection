"""Feature engineering for the fraud model.

This is the only code kept outside the notebook. The saved pipeline stores a
FraudFeatures object, and joblib can only load it again if this class can be
imported, so the notebook and the API both import it from here.
"""

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

# Raw columns the pipeline expects: the CSV columns without the isFraud label
RAW_COLUMNS = [
    "step", "type", "amount", "nameOrig", "oldbalanceOrg", "newbalanceOrig",
    "nameDest", "oldbalanceDest", "newbalanceDest",
]

# Dropped on purpose: the names are unique IDs with no signal, and step only
# separates the classes because of how the sample was built (EDA 2.4)
DROPPED_COLUMNS = ["step", "nameOrig", "nameDest"]

KEPT_RAW_COLUMNS = [
    "type", "amount", "oldbalanceOrg", "newbalanceOrig",
    "oldbalanceDest", "newbalanceDest",
]

BALANCE_FEATURES = [
    "error_balance_orig", "error_balance_dest",
    "drains_whole_balance", "dest_zero_before_after",
]


class FraudFeatures(BaseEstimator, TransformerMixin):
    """Turn raw transaction columns into model features.

    Every feature is computed from its own row only, so fit() learns nothing
    and test data cannot leak into training through this step.

    include_balance_features=False leaves out the engineered balance features,
    so we can measure how much of the model's score depends on them.
    """

    def __init__(self, include_balance_features=True):
        self.include_balance_features = include_balance_features

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        features = X[KEPT_RAW_COLUMNS].copy()

        if self.include_balance_features:
            # 0 when a balance moved by exactly the amount sent; legit rows in
            # this simulation often don't add up (EDA 2.5)
            features["error_balance_orig"] = (
                X["newbalanceOrig"] + X["amount"] - X["oldbalanceOrg"]
            )
            features["error_balance_dest"] = (
                X["oldbalanceDest"] + X["amount"] - X["newbalanceDest"]
            )
            # Account drained exactly: 97% of fraud, 0% of legit (EDA 2.5).
            # Compared to the cent, because floats carry tiny rounding errors.
            drains = np.isclose(X["amount"], X["oldbalanceOrg"], rtol=0, atol=0.01)
            features["drains_whole_balance"] = (drains & (X["oldbalanceOrg"] > 0)).astype(int)
            features["dest_zero_before_after"] = (
                (X["oldbalanceDest"] == 0) & (X["newbalanceDest"] == 0)
            ).astype(int)

        return features

    def get_feature_names_out(self, input_features=None):
        names = KEPT_RAW_COLUMNS + (BALANCE_FEATURES if self.include_balance_features else [])
        return np.array(names, dtype=object)
