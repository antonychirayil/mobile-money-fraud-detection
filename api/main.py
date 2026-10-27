"""FastAPI service: scores one mobile-money transaction and explains the decision.

Run from the project root:   uvicorn api.main:app --reload
Interactive docs:            http://localhost:8000/docs

The model file is created by the notebook (Section 9.1). It is a full scikit-learn Pipeline that
takes raw transaction fields, so this service runs exactly the same feature code as training.
"""

import json
from importlib.metadata import version
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
import shap
from fastapi import FastAPI
from pydantic import BaseModel, Field

# Importing model.features also lets joblib find the FraudFeatures class when unpickling
from model.features import KEPT_RAW_COLUMNS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "model" / "fraud_model.joblib"
METADATA_PATH = PROJECT_ROOT / "model" / "fraud_model_metadata.json"
TOP_REASONS = 3

# Loaded once at startup, not per request
pipeline = joblib.load(MODEL_PATH)
metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
THRESHOLD = metadata["decision_threshold"]
preprocessor = pipeline.named_steps["preprocess"]
explainer = shap.TreeExplainer(pipeline.named_steps["model"])

# A pickled model is only safe under the library versions it was saved with
VERSIONS_MATCH = all(
    version(package) == saved
    for package, saved in metadata["versions"].items()
    if package != "python"
)


class Transaction(BaseModel):
    """One transaction. Only the six fields the model uses are required."""

    type: Literal["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
    amount: float = Field(gt=0)
    oldbalanceOrg: float = Field(ge=0)
    newbalanceOrig: float = Field(ge=0)
    oldbalanceDest: float = Field(ge=0)
    newbalanceDest: float = Field(ge=0)
    # Accepted so callers can send a full record, but ignored: step is a sampling artefact and
    # the names are unique IDs (notebook 2.4 and 3.1)
    step: int | None = None
    nameOrig: str | None = None
    nameDest: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "type": "CASH_OUT", "amount": 581421.85,
                "oldbalanceOrg": 581421.85, "newbalanceOrig": 0.0,
                "oldbalanceDest": 407848.96, "newbalanceDest": 989270.81,
            }]
        }
    }


class Reason(BaseModel):
    feature: str
    value: float
    push: float  # SHAP value in log-odds: positive pushes towards fraud
    direction: Literal["towards fraud", "towards legit"]


class Prediction(BaseModel):
    fraud_probability: float
    decision: Literal["FLAG", "PASS"]
    threshold: float
    top_reasons: list[Reason]


def decide(probability: float, threshold: float = THRESHOLD) -> str:
    """FLAG when the fraud probability reaches the cost-based threshold (notebook 7.2)."""
    return "FLAG" if probability >= threshold else "PASS"


app = FastAPI(
    title="Mobile-money fraud detection",
    description="Scores a transaction with the tuned LightGBM pipeline and explains it with SHAP.",
    version="1.0",
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": metadata["model"],
        "threshold": THRESHOLD,
        "versions_match_training": VERSIONS_MATCH,
    }


@app.post("/predict", response_model=Prediction)
def predict(transaction: Transaction) -> Prediction:
    row = pd.DataFrame([transaction.model_dump(include=set(KEPT_RAW_COLUMNS))])[KEPT_RAW_COLUMNS]
    probability = float(pipeline.predict_proba(row)[0, 1])

    features = preprocessor.transform(row)
    pushes = pd.Series(explainer(features).values[0], index=features.columns)
    strongest = pushes.abs().sort_values(ascending=False).index[:TOP_REASONS]
    reasons = [
        Reason(
            feature=feature,
            value=float(features.at[0, feature]),
            push=round(float(pushes[feature]), 3),
            direction="towards fraud" if pushes[feature] > 0 else "towards legit",
        )
        for feature in strongest
    ]

    return Prediction(
        fraud_probability=probability,
        decision=decide(probability),
        threshold=THRESHOLD,
        top_reasons=reasons,
    )
