"""Tests for model/features.py: each engineered feature against hand-calculated values."""

import pandas as pd
import pytest

from model.features import BALANCE_FEATURES, KEPT_RAW_COLUMNS, RAW_COLUMNS, FraudFeatures


def make_row(**overrides):
    """One raw transaction (all 9 raw columns) with sensible defaults."""
    row = {
        "step": 1, "type": "TRANSFER", "amount": 100.0, "nameOrig": "C1",
        "oldbalanceOrg": 100.0, "newbalanceOrig": 0.0, "nameDest": "C2",
        "oldbalanceDest": 0.0, "newbalanceDest": 0.0,
    }
    row.update(overrides)
    return pd.DataFrame([row])[RAW_COLUMNS]


def transform(**overrides):
    return FraudFeatures().fit_transform(make_row(**overrides)).iloc[0]


def test_output_columns_drop_step_and_ids():
    out = FraudFeatures().fit_transform(make_row())
    assert list(out.columns) == KEPT_RAW_COLUMNS + BALANCE_FEATURES
    assert not {"step", "nameOrig", "nameDest"} & set(out.columns)


def test_switch_off_leaves_only_kept_raw_columns():
    features = FraudFeatures(include_balance_features=False)
    out = features.fit_transform(make_row())
    assert list(out.columns) == KEPT_RAW_COLUMNS
    assert list(features.get_feature_names_out()) == KEPT_RAW_COLUMNS


def test_error_balance_formulas():
    out = transform(amount=50.0, oldbalanceOrg=200.0, newbalanceOrig=120.0,
                    oldbalanceDest=10.0, newbalanceDest=40.0)
    assert out["error_balance_orig"] == pytest.approx(120.0 + 50.0 - 200.0)  # -30
    assert out["error_balance_dest"] == pytest.approx(10.0 + 50.0 - 40.0)    # 20


def test_drain_flag_when_amount_equals_whole_balance():
    assert transform(amount=100.0, oldbalanceOrg=100.0)["drains_whole_balance"] == 1


def test_drain_flag_off_for_partial_transfer():
    assert transform(amount=60.0, oldbalanceOrg=100.0)["drains_whole_balance"] == 0


def test_drain_flag_compares_to_the_cent():
    assert transform(amount=100.004, oldbalanceOrg=100.0)["drains_whole_balance"] == 1
    assert transform(amount=100.02, oldbalanceOrg=100.0)["drains_whole_balance"] == 0


def test_drain_flag_off_for_zero_balance_sender():
    # Sending from an empty account is the legit-looking quirk, not a drain (notebook 2.5, 6.2)
    assert transform(amount=100.0, oldbalanceOrg=0.0)["drains_whole_balance"] == 0


def test_dest_zero_flag():
    assert transform(oldbalanceDest=0.0, newbalanceDest=0.0)["dest_zero_before_after"] == 1
    assert transform(oldbalanceDest=0.0, newbalanceDest=100.0)["dest_zero_before_after"] == 0


def test_fit_learns_nothing():
    # Stateless: fitting on different data must not change the output for the same row
    row = make_row(amount=70.0, oldbalanceOrg=70.0)
    fitted_on_row = FraudFeatures().fit(row).transform(row)
    fitted_on_other = FraudFeatures().fit(make_row(amount=5.0, oldbalanceOrg=999.0)).transform(row)
    pd.testing.assert_frame_equal(fitted_on_row, fitted_on_other)
