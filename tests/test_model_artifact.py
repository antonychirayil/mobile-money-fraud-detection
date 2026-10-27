"""Tests for the saved model: it exists, matches its metadata, and reproduces the test results."""

import json
from pathlib import Path

import joblib
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

from model.features import RAW_COLUMNS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "model" / "fraud_model.joblib"
METADATA_PATH = PROJECT_ROOT / "model" / "fraud_model_metadata.json"
DATA_PATH = PROJECT_ROOT / "data" / "Fraud_Analysis_Dataset.csv"

# Must match the split in notebook 4.1
TEST_SIZE = 0.20
RANDOM_STATE = 42


@pytest.fixture(scope="module")
def metadata():
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def test_predictions():
    df = pd.read_csv(DATA_PATH)
    _, X_test, _, y_test = train_test_split(df[RAW_COLUMNS], df["isFraud"], test_size=TEST_SIZE,
                                            stratify=df["isFraud"], random_state=RANDOM_STATE)
    probabilities = joblib.load(MODEL_PATH).predict_proba(X_test)[:, 1]
    return y_test.to_numpy(), probabilities


def test_files_exist():
    assert MODEL_PATH.exists(), "run notebook Section 9.1 to create the model file"
    assert METADATA_PATH.exists()


def test_threshold_is_cost_based(metadata):
    # Chosen by cost in notebook 7.2: far below the 0.5 default
    assert 0 < metadata["decision_threshold"] < 0.5


def test_reproduces_test_pr_auc(metadata, test_predictions):
    y_test, probabilities = test_predictions
    assert average_precision_score(y_test, probabilities) == pytest.approx(
        metadata["test_metrics_threshold_0.5"]["pr_auc"], abs=1e-4)


def test_reproduces_counts_at_cost_threshold(metadata, test_predictions):
    y_test, probabilities = test_predictions
    flagged = probabilities >= metadata["decision_threshold"]
    expected = metadata["test_counts_cost_threshold"]
    assert int((flagged & (y_test == 1)).sum()) == expected["fraud_caught"]
    assert int((~flagged & (y_test == 1)).sum()) == expected["fraud_missed"]
    assert int((flagged & (y_test == 0)).sum()) == expected["false_alarms"]
