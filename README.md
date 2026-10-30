# Mobile-money fraud detection

A machine learning model that flags fraudulent mobile-money transactions, chooses its decision
threshold by money rather than by a default, explains every decision with SHAP, and is served as a
tested FastAPI service in Docker with a Streamlit demo.

The full analysis is in [`notebooks/fraud_detection.ipynb`](notebooks/fraud_detection.ipynb), which
runs top to bottom in about 9 minutes. All charts are in [`reports/figures/`](reports/figures/).

**Status:** model, analysis, API, Docker and tests complete. The final report (PowerPoint) is in
progress.

## Results (held-out test set: 2,229 transactions, 228 fraud)

| | Value |
|---|---|
| Final model | Tuned LightGBM in one scikit-learn Pipeline (raw transaction fields in) |
| PR-AUC / ROC-AUC | 0.994 / 0.996 |
| At threshold 0.5 | precision 0.996, recall 0.978 (223 of 228 frauds caught, 1 false alarm) |
| At the cost-based threshold (0.00032) | 226 of 228 frauds caught, 14 false alarms |
| Profit on the test set* | +1.72M with the model vs -0.62M at threshold 0.5 vs -233.8M with no model |

\*Illustrative assumptions: 1% fee on legit transactions, 25 per manual review, no recovery of
missed fraud. The conclusion holds across all 18 cost scenarios tested.

## The three business questions

1. **Precision and accuracy:** precision 99.6% and accuracy 99.7% at the 0.5 threshold. Accuracy is
   not the headline: predicting "legit" for everything would already score 89.8%.
2. **Reliability:** legit transactions pass correctly 99.95% of the time and 97.8% of fraud is
   caught; test scores match cross-validation. Weak spot: fraud from accounts that start at a zero
   balance, which looks legitimate in this data.
3. **Potential losses from model errors:** about 0.33M on the test set at the cost-based threshold
   (0.29M from 2 missed frauds, about 0.04M from false alarms), against 235.8M lost with no model.

## Key findings

- Fraud occurs only in TRANSFER and CASH_OUT. Within those, 97% of fraud moves the sender's whole
  balance in one go, versus 0% of legit transactions.
- Legit transactions exist only in the first 7 hours of the sample, so the time column was dropped:
  it would have let the model "cheat".
- Every tree ensemble scored about 0.995 PR-AUC; an ablation showed the signal comes from the balance
  columns (type + amount only: 0.66), not from the choice of model.
- A missed fraud costs far more than a false alarm, so the profit-maximising threshold is 0.00032,
  not 0.5.
- SHAP top drivers: account drained in one go; sender balance that adds up exactly; receiving
  account that was empty before (mule-account pattern).

## Limitations

- Simulated (PaySim-style) data, enriched to 10% fraud; real-world fraud is usually under 1%. At a
  1% fraud rate, precision would be about 0.95 (0.66 at 0.1%).
- The near-perfect scores rely on the simulator's balance patterns; the model would need validating
  on real data before any real use.
- One transaction per sender, so no customer-history features are possible.
- Money figures rest on illustrative cost assumptions. The threshold rule was settled after some
  test-set results had been seen during exploration; its justification uses training data only.

## Notebook guide

| Section | Content |
|---|---|
| 0-1 | Problem, business questions, data loading |
| 2 | EDA: class balance, fraud by type, amounts, time artefact, balance behaviour, destinations, correlations |
| 3 | Feature engineering (`FraudFeatures`) and one-hot encoding |
| 4 | Stratified split, Logistic Regression baseline, class weights vs SMOTE |
| 5 | Six classifiers on three feature sets, Optuna tuning tracked in MLflow, final model choice |
| 6 | Test-set evaluation, confusion matrix and errors, ROC/PR curves, calibration, realism check |
| 7 | Financial assumptions, cost-based threshold, policy comparison, sensitivity table |
| 8 | SHAP: global drivers and per-transaction explanations |
| 9 | Saving the pipeline, serving, monitoring and retraining notes |

## Project structure

```
fraud-detection/
├── notebooks/fraud_detection.ipynb   # the analysis; Section 9.1 creates the model files
├── model/
│   ├── features.py                   # FraudFeatures: feature engineering shared by training and API
│   ├── fraud_model.joblib            # saved pipeline (features + one-hot encoding + LightGBM)
│   └── fraud_model_metadata.json     # threshold, required inputs, test results, library versions
├── api/
│   ├── main.py                       # FastAPI: /predict (probability, decision, top SHAP reasons), /health
│   └── requirements.txt              # pinned API dependencies (used by Docker)
├── app/streamlit_app.py              # Streamlit demo that calls the API
├── tests/                            # pytest: features, API, saved-model regression checks
├── reports/figures/                  # 20 charts from the notebook
├── data/                             # Fraud_Analysis_Dataset.csv (11,142 rows) + description.txt
├── Dockerfile, .dockerignore         # API image
├── pytest.ini
├── requirements.txt                  # API + Streamlit runtime (pinned)
└── requirements-dev.txt              # adds everything for the notebook and tests
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

The model files are already in `model/`. To recreate them, run the notebook top to bottom.

**With Docker (API only):**

```bash
docker build -t fraud-api .
docker run -p 8000:8000 fraud-api          # then open http://localhost:8000/docs
```

The Streamlit demo works with the Docker API unchanged (it calls `http://127.0.0.1:8000`); set the
`FRAUD_API_URL` environment variable to point it elsewhere.

**Example request:**

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"type": "CASH_OUT", "amount": 581421.85, "oldbalanceOrg": 581421.85, "newbalanceOrig": 0,
       "oldbalanceDest": 407848.96, "newbalanceDest": 989270.81}'
```

Returns the fraud probability, `"decision": "FLAG"` or `"PASS"`, the threshold, and the top 3
reasons, here led by `drains_whole_balance` pushing towards fraud. Invalid input (an unknown type,
a negative amount, a missing field) is rejected with HTTP 422.

## Monitoring and retraining

Planned for a live deployment (details in notebook Section 9.2): monitor input drift (type mix,
amounts, share of zero-balance senders), the daily flag rate, precision of reviewed flags and recall
from later-confirmed fraud, and daily cost; retrain on a schedule or when an alert fires, re-choose
the threshold with current costs, and compare against the live model before replacing it.

## Tech stack

pandas, NumPy, matplotlib, seaborn · scikit-learn (Pipeline, ColumnTransformer) · LightGBM, XGBoost,
Random Forest, Gradient Boosting, Logistic Regression · imbalanced-learn (SMOTE) · Optuna · MLflow ·
SciPy · SHAP · FastAPI · Streamlit · Docker · pytest
