"""Streamlit demo: a form that sends one transaction to the fraud API and shows the result.

Start the API first (terminal 1):   uvicorn api.main:app
Then this app (terminal 2):         streamlit run app/streamlit_app.py

The app never loads the model: it only talks to the API over HTTP, so any other front end
(a mobile app, another service) would get exactly the same answers.
"""

import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.environ.get("FRAUD_API_URL", "http://127.0.0.1:8000")
TRANSACTION_TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
BALANCE_FIELDS = ["oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]

# Ready-made transactions taken from the test set (notebook 6.2 and 8.3)
EXAMPLES = {
    "Account drained in one go (fraud, caught)": {
        "type": "CASH_OUT", "amount": 581421.85, "oldbalanceOrg": 581421.85, "newbalanceOrig": 0.0,
        "oldbalanceDest": 407848.96, "newbalanceDest": 989270.81},
    "Everyday payment (legit)": {
        "type": "PAYMENT", "amount": 1200.0, "oldbalanceOrg": 50000.0, "newbalanceOrig": 48800.0,
        "oldbalanceDest": 0.0, "newbalanceDest": 0.0},
    "Zero-balance sender (fraud the model misses)": {
        "type": "TRANSFER", "amount": 202978.65, "oldbalanceOrg": 0.0, "newbalanceOrig": 0.0,
        "oldbalanceDest": 2122336.55, "newbalanceDest": 2325315.19},
}

# Plain-language meaning of each model input, for the reasons table
FEATURE_MEANINGS = {
    "drains_whole_balance": "the amount equals the sender's entire balance",
    "error_balance_orig": "gap between the sender's balance change and the amount (0 = adds up)",
    "error_balance_dest": "gap between the receiver's balance change and the amount (0 = adds up)",
    "dest_zero_before_after": "the receiver shows a zero balance before and after",
    "amount": "transaction amount",
    "oldbalanceOrg": "sender's balance before",
    "newbalanceOrig": "sender's balance after",
    "oldbalanceDest": "receiver's balance before",
    "newbalanceDest": "receiver's balance after",
    **{f"type_{name}": f"transaction type is {name}" for name in TRANSACTION_TYPES},
}


def call_api(method: str, path: str, **kwargs) -> requests.Response | None:
    """Call the API; show a clear message instead of a crash if it is not running."""
    try:
        return requests.request(method, f"{API_URL}{path}", timeout=10, **kwargs)
    except requests.ConnectionError:
        st.error(f"The fraud API is not reachable at {API_URL}. "
                 "Start it from the project folder with: `uvicorn api.main:app`")
        return None


st.set_page_config(page_title="Fraud check", page_icon=":mag:")
st.title("Mobile-money fraud check")
st.caption("Tuned LightGBM model with SHAP explanations, served by a FastAPI service.")

with st.sidebar:
    st.header("Model")
    health = call_api("GET", "/health")
    if health is not None and health.ok:
        info = health.json()
        st.write(info["model"])
        st.write(f"Decision threshold: **{info['threshold']:.2g}** (chosen by cost, not 0.5)")
        if not info["versions_match_training"]:
            st.warning("Library versions differ from training: predictions may not match.")
    example_name = st.selectbox("Start from an example", [*EXAMPLES, "Custom"])

defaults = EXAMPLES.get(example_name, EXAMPLES["Everyday payment (legit)"])

with st.form("transaction"):
    # Keys include the example name, so picking another example refills the form
    transaction_type = st.selectbox("Transaction type", TRANSACTION_TYPES,
                                    index=TRANSACTION_TYPES.index(defaults["type"]),
                                    key=f"type_{example_name}")
    amount = st.number_input("Amount", min_value=0.01, value=defaults["amount"],
                             key=f"amount_{example_name}")
    left, right = st.columns(2)
    balances = {}
    for column, field in zip([left, right, left, right], BALANCE_FIELDS):
        balances[field] = column.number_input(field, min_value=0.0, value=defaults[field],
                                              key=f"{field}_{example_name}")
    submitted = st.form_submit_button("Check transaction")

if submitted:
    payload = {"type": transaction_type, "amount": amount, **balances}
    response = call_api("POST", "/predict", json=payload)
    if response is not None and response.status_code == 422:
        st.error("The API rejected the input:")
        st.json(response.json()["detail"])
    elif response is not None and response.ok:
        result = response.json()
        if result["decision"] == "FLAG":
            st.error(f"FLAG: send for review (fraud probability {result['fraud_probability']:.4f})")
        else:
            st.success(f"PASS: process normally (fraud probability {result['fraud_probability']:.6f})")
        st.caption(f"A transaction is flagged when its fraud probability is at least "
                   f"{result['threshold']:.2g}.")

        st.subheader("Why")
        reasons = pd.DataFrame(result["top_reasons"])
        reasons["meaning"] = reasons["feature"].map(FEATURE_MEANINGS)
        st.dataframe(
            reasons[["feature", "meaning", "value", "direction", "push"]],
            hide_index=True,
            column_config={"push": st.column_config.NumberColumn(
                "push (log-odds)", help="SHAP value: positive pushes towards fraud", format="%+.2f")},
        )
