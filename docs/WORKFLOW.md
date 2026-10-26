# WORKFLOW.md: full plan for the Fraud Detection portfolio project

Goal: a portfolio project that gets the user hired in about a month, while he learns as he codes.
Everything here follows the project brief (see CLAUDE.md for the brief and the rules).

## 1. What hiring managers look for
1. Business framing: turn model errors into money, not just F1 scores. The brief asks for this.
2. Correct handling of class imbalance and data leakage.
3. Explainability (SHAP): why was this transaction flagged?
4. Reproducible, production-style code: GitHub repo, sklearn Pipeline, saved model, small API.
5. A clear story: short report, dashboard, and a README readable in 2 minutes.

## 2. Stack
| Purpose | Tool |
|---|---|
| Data and EDA | pandas, NumPy, matplotlib, seaborn, Plotly |
| Preprocessing | scikit-learn Pipeline + ColumnTransformer |
| Models | Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, XGBoost, LightGBM |
| Imbalance | class_weight / scale_pos_weight; SMOTE inside the CV pipeline (imbalanced-learn) for comparison |
| Tuning | Optuna, or RandomizedSearchCV |
| Explainability | SHAP |
| Experiment tracking | MLflow (light) |
| Serving | FastAPI (/predict), Streamlit demo UI, Dockerfile, joblib |
| Quality | Git/GitHub, a few pytest tests, requirements files |
| Dashboard (optional) | Power BI (matches the target roles) |
Skip: deep learning, Kafka, cloud deployment.

## 3. Steps

### Step 1: Setup (Day 1)
Create venv, install requirements-dev.txt, git init + GitHub repo, create the notebook, write the
problem statement and the three business questions at the top of the notebook.

### Step 2: EDA (brief: "thorough EDA with visualisation")
- Fraud rate by transaction type.
- Amount distributions on a log scale, fraud vs legit.
- Fraud by step (hour of day and day).
- Balance behaviour: how often newbalanceOrig = 0 and oldbalanceOrg = amount.
- Merchant (M) vs customer (C) destinations.
- Correlation heatmap; class imbalance chart.
One insight sentence under every chart.

### Step 3: Feature engineering and encoding
- errorBalanceOrig = newbalanceOrig + amount - oldbalanceOrg
- errorBalanceDest = oldbalanceDest + amount - newbalanceDest
- Flags: origin account emptied; destination balance zero; amount-to-balance ratio.
  (No "destination is a merchant" flag: EDA 2.6 showed it duplicates type == PAYMENT.)
- Time: NONE. EDA 2.4 showed legit rows exist only in steps 1-7, so step/hour/day would leak the
  label through a sampling artefact. `step` is dropped (decision A, 2026-10-27).
- Encoding: one-hot for type. Drop raw name IDs (every nameOrig is unique, so no signal).
Put the feature code in model/features.py so training and the API share it.

### Step 4: Modelling (brief: "evaluate various classifiers")
- Split: stratified train/test split + stratified 5-fold CV. Time-based split is ruled out (EDA 2.4:
  later steps contain only fraud).
- Baseline Logistic Regression first, then Decision Tree, Random Forest, Gradient Boosting,
  XGBoost, LightGBM.
- Everything inside one Pipeline so scaling and SMOTE are fitted on training folds only.
- Tune the best 1-2 models (Optuna / RandomizedSearchCV). Track runs in MLflow.

### Step 5: Evaluation
Precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix; a comparison table across all models;
ROC and Precision-Recall curves; calibration plot; threshold tuning (not the 0.5 default).
Accuracy is reported but never the headline.

### Step 6: Financial impact (brief: expected revenue, losses and profit)
Use the actual amount values:
- Missed fraud (false negative) costs the full transaction amount.
- False alarm (false positive) costs a review cost or lost fee. Make it an explicit, adjustable
  assumption (e.g. 1-2% of amount or a flat review cost).
- Caught fraud saves its amount.
- Choose the threshold that minimises total expected cost.
- Show revenue, losses and profit with the model vs with no model.
- Add a sensitivity table over several cost assumptions.

### Step 7: Explainability
SHAP summary plot; explain the top 3 drivers in business language.

### Step 8: Make it "production-ready"
- Save the full Pipeline with joblib (raw columns in, probability out).
- FastAPI endpoint: transaction in, fraud probability + decision + top reasons out.
- Streamlit demo calling the API.
- Dockerfile, a few pytest tests (feature code, API schema, threshold logic).
- Short "monitoring and retraining" section: data drift, recall tracking, retrain triggers.

### Step 9: Report and dashboard
6-8 page report (.docx) or PowerPoint answering the three business questions directly.
Optional Power BI page: fraud by type and time, KPIs, threshold-vs-cost view.

### Step 10: Package
Zip: notebook (.ipynb) + report (.docx/.pptx) + optional dashboard. The GitHub repo is the richer
version. Clean README, requirements pinned (pip freeze), figures in reports/figures/.

## 4. Traps (interviewers probe these)
- Near-perfect scores are a red flag. Balance-based features may push tree models to very high
  ROC-AUC. Explain why (simulated data, balance mismatch) and show results with and without the
  engineered balance features.
- Prevalence is unrealistic (10% vs usually under 1% in real life). Add an experiment that
  downsamples fraud to about 0.5-1% and shows how precision and PR-AUC drop.
- No leakage: split first; fit scalers, encoders, SMOTE and thresholds on training data only.
- State the limits: simulated data, one transaction per origin account, so no customer-history
  features are possible.

## 5. Four-week schedule (planned pace: about 3-4 focused hours per day)
| Week | Dates | Focus | Learn while doing |
|---|---|---|---|
| 1 | Oct 26 - Nov 1 | Setup, EDA, features | pandas groupby, plotting, sklearn Pipelines. START APPLYING NOW. |
| 2 | Nov 2 - Nov 8 | Models, CV, tuning, metrics | Imbalance, PR-AUC, Optuna, MLflow |
| 3 | Nov 9 - Nov 15 | Cost analysis, SHAP, FastAPI, Docker | Threshold optimisation, SHAP, API basics |
| 4 | Nov 16 - Nov 22 | Report, dashboard, README, resume, LinkedIn | Storytelling, 2-minute pitch, mock interviews |
Apply to jobs from week 1, not week 4. Hiring takes weeks.

## 6. Resume bullets (fill in the real numbers at the end)
- "Built a fraud detection pipeline (XGBoost/LightGBM) on 11K mobile-money transactions; reached X
  recall at Y precision and cut simulated fraud losses by Z% with a cost-optimised threshold."
- "Deployed the model as a FastAPI service in Docker with SHAP-based explanations."
