"""Tests for api/main.py: request validation, response shape and the threshold decision."""

import pytest
from fastapi.testclient import TestClient

from api.main import THRESHOLD, app, decide

FRAUD_LIKE = {  # the whole balance is drained (test-set row, caught in notebook 6.2)
    "type": "CASH_OUT", "amount": 581421.85, "oldbalanceOrg": 581421.85, "newbalanceOrig": 0.0,
    "oldbalanceDest": 407848.96, "newbalanceDest": 989270.81,
}
LEGIT_LIKE = {
    "type": "PAYMENT", "amount": 1200.0, "oldbalanceOrg": 50000.0, "newbalanceOrig": 48800.0,
    "oldbalanceDest": 0.0, "newbalanceDest": 0.0,
}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["threshold"] == THRESHOLD


def test_predict_response_shape(client):
    response = client.post("/predict", json=FRAUD_LIKE)
    assert response.status_code == 200
    body = response.json()
    assert 0.0 <= body["fraud_probability"] <= 1.0
    assert body["decision"] in {"FLAG", "PASS"}
    assert body["threshold"] == THRESHOLD
    assert len(body["top_reasons"]) == 3
    for reason in body["top_reasons"]:
        assert reason["direction"] == ("towards fraud" if reason["push"] > 0 else "towards legit")


def test_known_cases(client):
    fraud = client.post("/predict", json=FRAUD_LIKE).json()
    legit = client.post("/predict", json=LEGIT_LIKE).json()
    assert fraud["decision"] == "FLAG"
    assert fraud["top_reasons"][0]["feature"] == "drains_whole_balance"
    assert legit["decision"] == "PASS"


def test_optional_ids_change_nothing(client):
    with_ids = {**FRAUD_LIKE, "step": 40, "nameOrig": "C111", "nameDest": "C222"}
    assert (client.post("/predict", json=with_ids).json()["fraud_probability"]
            == client.post("/predict", json=FRAUD_LIKE).json()["fraud_probability"])


@pytest.mark.parametrize("change", [
    {"amount": -5.0},                 # amounts must be positive
    {"amount": 0.0},
    {"oldbalanceOrg": -1.0},          # balances cannot be negative
    {"type": "REFUND"},               # unknown transaction type
    {"amount": "a lot"},              # wrong data type
])
def test_rejects_invalid_input(client, change):
    assert client.post("/predict", json={**LEGIT_LIKE, **change}).status_code == 422


def test_rejects_missing_field(client):
    incomplete = {key: value for key, value in LEGIT_LIKE.items() if key != "newbalanceDest"}
    assert client.post("/predict", json=incomplete).status_code == 422


def test_decide_threshold_boundary():
    assert decide(THRESHOLD) == "FLAG"          # exactly at the threshold counts as fraud
    assert decide(THRESHOLD * 0.999) == "PASS"
    assert decide(1.0) == "FLAG"
    assert decide(0.0) == "PASS"
    assert decide(0.3, threshold=0.5) == "PASS"  # the rule works for any threshold
