# CLAUDE.md: Fraud Detection portfolio project

Read this file and PROGRESS.md at the start of every session. Full plan: docs/WORKFLOW.md
(local only: the docs/ folder is git-ignored and not on GitHub).

## Who this is for, and the goal
The user is building this as a portfolio project to get hired as a data analyst / data scientist
within about a month (started 2026-10-26). He is LEARNING WHILE HE CODES, so he must understand
every step well enough to explain it in an interview. Teaching matters as much as the output.

## The project (do not change the scope)
Build a machine learning model that predicts fraudulent mobile-money transactions, with analysis
of model performance and expected financial impact.

Deliverables:
1. A production-ready fraud detection model.
2. A comprehensive analysis of model performance and expected financial impact.

Required activities (from the brief):
- Data Exploration: thorough EDA with visualisations (patterns, fraud indicators).
- Feature Engineering: relevant features + appropriate encoding for categoricals.
- Model Selection: evaluate several classifiers (Logistic Regression, Random Forest,
  Gradient Boosting, and others).
- Performance Evaluation: precision, recall, F1-score, ROC-AUC.
- Financial Impact Analysis: expected revenue, losses and profit from model performance.
- Visualisation: clear charts for insights and model performance.

Business questions the final report MUST answer directly:
1. What is the model's precision and accuracy in detecting fraudulent transactions?
2. How reliable is the model in classifying transactions as legitimate or fraudulent?
3. What are the potential losses due to model errors?

Submission (one zip): the Jupyter notebook (.ipynb: analysis, preprocessing, model training),
the final report (.docx or PowerPoint), and optionally a Power BI / Tableau dashboard.

## The data (data/Fraud_Analysis_Dataset.csv; column meanings in data/description.txt)
- 11,142 rows, 10 columns, no missing values. 1 step = 1 hour (step 1 to 95, about 4 days).
- Columns: step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, nameDest,
  oldbalanceDest, newbalanceDest, isFraud (target).
- Type values in the file use an underscore: CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER.
- Fraud rate is 10.25% (1,142 fraud vs 10,000 legit). Real-world fraud is usually far below 1%,
  so this sample is heavily enriched. Always say so in the report.
- Fraud occurs ONLY in TRANSFER (564) and CASH_OUT (578). CASH_IN, DEBIT, PAYMENT have zero fraud.
- Fraud amounts are much larger (median about 353K vs about 12.7K for legit).
- Every nameOrig is unique (11,142 unique), so per-customer history features are NOT possible.
- Destination names starting with M are merchants; they have no balance information.
- Data is simulated (PaySim-style). Fraud pattern: take over an account, TRANSFER the funds out,
  then CASH_OUT. State this limitation in the report.

## How to teach (standing rules for every step)
1. Before coding a step, explain in 3-5 plain-language lines what we are about to do and WHY.
2. Write code in small cells. After each, explain what it does and what the output means.
3. At real decision points (metric, split method, threshold) give the options and trade-offs,
   then let the user choose. Do not silently decide.
4. End each step with: a 2-line summary, one "interview takeaway" (how he would say it out loud),
   and a suggested git commit message.
5. Prefer simple, readable code over clever code. Comment the why, not the what.
6. Never do a whole step in one go. Stop at the end of each step and wait for the user.
7. Update PROGRESS.md at the end of every session: what was done, decisions, what is next.

## Technical rules
- Python 3.12. Create the venv with `py -3.12 -m venv .venv`; activate with .venv\Scripts\activate.
- Install with: pip install -r requirements-dev.txt
- Set random_state=42 everywhere.
- Git commits and PR descriptions: NO "Co-Authored-By: Claude" trailer or other AI attribution
  lines. The user is the sole author on GitHub.
- The main submission notebook is notebooks/fraud_detection.ipynb. It must run top to bottom
  (Restart and Run All) before any commit.
- The notebook is the main submission. All EDA, preprocessing, training, evaluation, financial
  analysis and SHAP live in notebooks/fraud_detection.ipynb as readable cells that run top to
  bottom. The ONLY code that moves out is the custom feature transformer class, which goes in
  model/features.py (created in Step 3) and is imported into the notebook, so the saved pipeline
  can be unpickled by the API later.
- The saved artifact (model/fraud_model.joblib) must be one full sklearn Pipeline
  (feature engineering + encoding + classifier) that takes RAW transaction columns. The API then
  stays simple and cannot drift from training. Fit on a pandas DataFrame so column names are kept.
- NO LEAKAGE: split before fitting anything. Scalers, encoders, SMOTE and threshold selection are
  fitted on training data only (use imbalanced-learn's Pipeline for SMOTE inside CV).
  Drop raw nameOrig / nameDest IDs from the model inputs.
- Do not use accuracy as the headline metric (imbalanced data). Lead with precision, recall, F1,
  PR-AUC and ROC-AUC, and always show the confusion matrix.
- Pick the decision threshold by minimising expected cost, not by defaulting to 0.5.
- Financial assumptions (review cost per flagged transaction, fee revenue %, etc.) must be explicit,
  named variables in one place, with a sensitivity table. Never bury them in code.
- Charts: label axes, give each a title and a one-sentence insight caption. Save final figures to
  reports/figures/.
- README.md must describe only files that exist (rewritten in Step 8; there is no train_demo.py:
  the notebook, Section 9.1, creates the model files).
- Before any commit, also run the tests: `python -m pytest` (24 tests, all must pass).
- Runtime dependencies are pinned in api/requirements.txt (used by Docker) to the versions the
  model was saved with (see model/fraud_model_metadata.json). If a library is upgraded, re-save the
  model from the notebook and update the pins together.
- The notebook is too large for the Read/NotebookEdit tools: insert or edit cells with small
  nbformat scripts, then re-run it with
  `jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 notebooks/fraud_detection.ipynb`
  (about 9 minutes, mostly Optuna tuning).

## Stack (keep to this; do not add heavy extras)
pandas, NumPy, matplotlib, seaborn, Plotly; scikit-learn (Pipeline, ColumnTransformer);
Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, XGBoost, LightGBM;
imbalanced-learn; Optuna; SHAP; MLflow (light experiment tracking); FastAPI + Streamlit demo;
Docker; pytest; Git/GitHub; Power BI for the optional dashboard.
Out of scope: deep learning, Kafka, cloud deployment.

## Repo layout
data/        raw data + description (never edit the raw CSV)
notebooks/   fraud_detection.ipynb (main submission notebook)
model/       features.py (custom feature transformer only), fraud_model.joblib,
             fraud_model_metadata.json (threshold, inputs, test results, library versions)
api/         main.py: FastAPI service (/predict returns probability, decision, top reasons;
             /health); requirements.txt (pinned, used by Docker)
app/         streamlit_app.py: Streamlit demo UI (calls the API over HTTP)
reports/     report draft (.docx/.pptx) and figures/ (01-20)
dashboard/   optional Power BI / Tableau file
tests/       pytest tests (features, API, saved-model regression); config in pytest.ini
docs/        local only (git-ignored): WORKFLOW.md (full plan), PROJECT_WALKTHROUGH.md,
             INTERVIEW_NOTES.md
Root files:  Dockerfile + .dockerignore (API image), requirements.txt (API + Streamlit, pinned),
             requirements-dev.txt (notebook + tests), pytest.ini
