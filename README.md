# Mobile-money fraud detection

A machine learning model that flags fraudulent mobile-money transactions, chooses its decision
threshold by money rather than by a default, explains every decision with SHAP, and is served as a
tested FastAPI service in Docker with a Streamlit demo.

The full analysis (EDA, features, model comparison, evaluation, financial impact, SHAP) is in
[`notebooks/fraud_detection.ipynb`](notebooks/fraud_detection.ipynb).

## Results (held-out test set: 2,229 transactions, 228 fraud)

| | Value |
|---|---|
| Final model | Tuned LightGBM in one scikit-learn Pipeline (raw transaction fields in) |
| PR-AUC / ROC-AUC | 0.994 / 0.996 |
| At threshold 0.5 | precision 0.996, recall 0.978 (223 of 228 frauds caught, 1 false alarm) |
| At the cost-based threshold (0.00032) | 226 of 228 caught, 14 false alarms |
| Profit on the test set* | +1.72M with the model vs -0.62M at threshold 0.5 vs -233.8M with no model |

\*Illustrative assumptions: 1% fee on legit transactions, 25 per manual review, no recovery of
missed fraud. The conclusion holds across all 18 scenarios tested.

**Important caveats.** The data is simulated (PaySim-style) and enriched to 10% fraud (real-world
fraud is usually under 1%). The near-perfect scores come from the simulator's balance columns: with
only transaction type and amount, the best model reaches PR-AUC 0.66. At a realistic 1% fraud rate,
precision would be about 0.95. The model would need validating on real data before any real use.

## Key findings

- Fraud occurs only in TRANSFER and CASH_OUT transactions; 97% of fraud empties the sender's whole
  balance in one transaction, versus 0% of legit transactions.
- Legit transactions exist only in the first 7 hours of the sample, so the time column was dropped
  (it would have let the model "cheat").
- A missed fraud costs far more than a false alarm, so the profit-maximising threshold is 0.00032,
  not 0.5.
- SHAP top drivers: account drained in one go; sender balance that adds up exactly; receiving account
  that was empty before (mule-account pattern).

## Project structure

```
fraud-detection/
├── notebooks/fraud_detection.ipynb   # the analysis; Section 9.1 creates the model files
├── model/
│   ├── features.py                   # FraudFeatures: the feature engineering, shared by training and API
│   ├── fraud_model.joblib            # saved pipeline (features + one-hot encoding + LightGBM)
│   └── fraud_model_metadata.json     # threshold, test results, library versions
├── api/
│   ├── main.py                       # FastAPI: /predict (probability, decision, top SHAP reasons), /health
│   └── requirements.txt              # pinned API dependencies (used by Docker)
├── app/streamlit_app.py              # Streamlit demo that calls the API
├── tests/                            # pytest: features, API, saved-model regression checks
├── reports/figures/                  # all charts from the notebook
├── data/Fraud_Analysis_Dataset.csv   # 11,142 transactions (see data/description.txt)
├── Dockerfile
├── requirements.txt                  # API + Streamlit runtime
└── requirements-dev.txt              # everything for the notebook and tests
```

## Run it

All commands from the project folder, with Python 3.12:

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate                     # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt

python -m pytest                           # 24 tests

uvicorn api.main:app                       # terminal 1: API at http://localhost:8000/docs
streamlit run app/streamlit_app.py --server.address localhost   # terminal 2: demo UI
```

The model files are already in `model/`. To recreate them, run the notebook top to bottom
(about 9 minutes, mostly hyperparameter tuning).

**With Docker (API only):**

```bash
docker build -t fraud-api .
docker run -p 8000:8000 fraud-api          # then open http://localhost:8000/docs
```

**Example request:**

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"type": "CASH_OUT", "amount": 581421.85, "oldbalanceOrg": 581421.85, "newbalanceOrig": 0,
       "oldbalanceDest": 407848.96, "newbalanceDest": 989270.81}'
```

Returns the fraud probability, `"decision": "FLAG"` or `"PASS"`, the threshold, and the top 3 reasons,
e.g. `drains_whole_balance` pushing towards fraud.

## Monitoring and retraining

Planned for a live deployment (details in notebook Section 9.2): monitor input drift (type mix,
amounts, share of zero-balance senders), the daily flag rate, precision of reviewed flags and
recall from later-confirmed fraud, and daily cost; retrain on a schedule or when an alert fires,
re-choose the threshold with current costs, and compare against the live model before replacing it.

## Tech stack

pandas, NumPy, matplotlib, seaborn · scikit-learn (Pipeline, ColumnTransformer) · LightGBM, XGBoost,
Random Forest, Gradient Boosting, Logistic Regression · imbalanced-learn (SMOTE) · Optuna · MLflow ·
SHAP · FastAPI · Streamlit · Docker · pytest
