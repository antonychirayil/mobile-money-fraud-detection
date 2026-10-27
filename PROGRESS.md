# PROGRESS.md: handoff log

Read with CLAUDE.md at the start of every session. Update at the end of every session.
Newest entry on top of the Log section.

## Current state (2026-10-27)

- Steps 1-8 done and pushed to GitHub (main at `7319e3b`). Next: Step 9 (report + optional dashboard).
- Final model: tuned LightGBM inside one scikit-learn Pipeline, saved as `model/fraud_model.joblib`
  with `model/fraud_model_metadata.json`; decision threshold 0.00032 (chosen by cost).
- Test set (2,229 rows, 228 fraud): PR-AUC 0.994, ROC-AUC 0.996; at 0.5: precision 0.996, recall
  0.978 (TP 223, FN 5, FP 1, TN 2,000); at 0.00032: 226 caught, 2 missed, 14 false alarms.
- Money (test set, base assumptions): +1.72M at 0.00032 vs -0.62M at 0.5 vs -233.8M with no model.
- Serving: FastAPI (`api/main.py`), Streamlit (`app/streamlit_app.py`), Docker image `fraud-api`
  (tested, healthy); 24 pytest tests pass.
- Verify everything: `.venv\Scripts\activate`, then `python -m pytest` (seconds) and, before a
  commit that touches the notebook, a full nbconvert run (about 9 minutes; command in CLAUDE.md).

## Status (started 2026-10-26)
- [x] Step 1  Setup: venv, git + GitHub repo, requirements installed, notebook created
- [x] Step 2  EDA with charts and insight captions (notebook Section 2)
- [x] Step 3  Feature engineering and encoding (Section 3, model/features.py)
- [x] Step 4  Modelling: baseline, tree/boosting models, CV, tuning, imbalance handling (Sections 4-5)
- [x] Step 5  Evaluation: metrics, confusion matrix, curves, calibration, realism check (Section 6)
- [x] Step 6  Financial impact: cost-based threshold, with/without model, sensitivity table (Section 7)
- [x] Step 7  Explainability with SHAP (Section 8)
- [x] Step 8  Production-readiness: saved Pipeline, FastAPI, Streamlit, Docker, tests, monitoring (Section 9)
- [ ] Step 9  Report (.docx or .pptx) + optional Power BI dashboard
- [ ] Step 10 Package: zip, README, GitHub cleanup, resume bullets

## Decisions made

**Project setup**
- Stack as listed in CLAUDE.md. Main notebook: notebooks/fraud_detection.ipynb.
- Python 3.12 (`py -3.12 -m venv .venv`; 3.14 is the machine default, so call 3.12 explicitly).
- All analysis and training code lives in the notebook. Only the FraudFeatures class lives in
  model/features.py, so the saved pipeline can be unpickled by the API. api/, app/ and tests/ are the
  serving layer around the saved model.
- data/ stays tracked in git (CSV under 1 MB; the notebook needs it to run).
- docs/ is local only (git-ignored; WORKFLOW.md untracked on 2026-10-27): WORKFLOW.md,
  PROJECT_WALKTHROUGH.md (section-by-section record + commit messages), INTERVIEW_NOTES.md.
- Git: no AI attribution lines in commits (CLAUDE.md rule + .claude/settings.local.json). Step 1/2
  commits were rewritten and force-pushed on 2026-10-27 to remove an old trailer.

**Step 2 (EDA)**
- 2.4: all 10,000 legit rows are in steps 1-7; steps 8-95 are 100% fraud (sampling artefact).
  Drop `step`, create NO hour/day features; a time-based split is impossible, so stratified split.
- 2.6: merchants receive only PAYMENTs, so an "is merchant" flag duplicates `type`: left out.

**Step 3 (features)**
- Whole-balance drain as a yes/no flag (drains_whole_balance), not a ratio; no "origin emptied"
  flag (91% of legit too). One-hot `type` with handle_unknown="ignore". No scaling in the shared
  preprocessor: scaling is added per model (Logistic Regression needs it, trees don't).

**Step 4 (modelling)**
- Stratified 80/20 split; stratified 5-fold CV on the training set only; PR-AUC selects.
- Imbalance: class weights for all models (scale_pos_weight for XGBoost); SMOTE / weights / none
  compared on the baseline and tied within noise.
- 5.1: every model compared on 3 feature sets (all / no engineered / type + amount only; the third
  is notebook-only experiment code). Gradient Boosting = HistGradientBoostingClassifier (the classic
  one has no class_weight).
- 5.2: tuned all six models (user choice), 30 Optuna trials each (TPE, seed 42), logged to MLflow
  (mlflow.db, experiment "fraud-detection-tuning", 186 runs).
- 5.3: final model = tuned LightGBM (tied on CV; best on type + amount only, 0.662; fastest; good
  SHAP support). Only this model touches the test set.

**Steps 5-7 (taken as defaults when the user asked to run them end to end; for user review)**
- 6.5: precision at lower fraud rates from test recall/FPR, with 95% Clopper-Pearson bounds (only 1
  false positive in test), plus the steps 1-7 test slice (~1% fraud).
- 7.1: FEE_RATE 1%, REVIEW_COST 25 per flag, FRAUD_RECOVERY_RATE 0; a flagged transaction is
  reviewed and blocked (legit loses its fee, fraud is stopped); fraud earns no fee.
  Profit = fee revenue - fraud losses - review costs.
- 7.2: threshold from out-of-fold training predictions; grid 1e-6..0.56 (4 steps per decade); each
  fold picks its most profitable threshold, the MEDIAN of the five is used -> 0.00032 (the plain
  "most profitable on all training rows" pick, 1e-5, rests on one fold with a single large fraud).
  CAVEAT: test-set results for several thresholds were seen in scratch exploration before the rule
  was fixed; the justification uses training folds only, but it was not chosen blind. The
  alternative rule's results are shown in 7.4. Also stated in README "Limitations".
- 7.3: added a business-rule baseline (flag whole-balance drains) and a perfect-model reference.
- 8: SHAP TreeExplainer on the test set (log-odds); top_reasons() helper, reused by the API.

**Step 8 (production; user choices)**
- Save the train-set pipeline (the evaluated one); threshold, inputs, test results and versions in a
  separate metadata JSON. No train_demo.py: the notebook creates the model files.
- API requires the 6 fields the model uses (type, amount, 4 balances); step/nameOrig/nameDest
  optional and ignored. Docker packages the API only.
- Runtime versions pinned (api/requirements.txt, requirements.txt); lightgbm is a runtime
  dependency, xgboost moved to requirements-dev.txt.
- Step 8 committed as six separate commits, one per part (80e0fe4 ... 7319e3b).

## Open items / reminders
- Notebook Section 10 (Conclusions) is still a header only: fill it in Step 9 or 10.
- requirements-dev.txt extras (jupyter, optuna, mlflow, xgboost, ...) are unpinned: pin in Step 10.
  pandas is 3.x (text columns show dtype `str`, not `object`).
- .gitignore suggestion still open (user to decide): .vscode/.
- Notebook run time ~9 min (Optuna tuning of all six models); it slowed to 12-25 min when other
  programs (a busy java process, Docker Desktop) competed for the CPU. Capping LightGBM at 4 threads
  or caching the tuning results were offered, not applied.
- FastAPI's TestClient prints a deprecation warning (httpx -> httpx2); harmless, left visible.
- GitHub's Contributors box may still show "claude" until GitHub refreshes its cache.
- Start applying for jobs now; do not wait for the project to finish.

## Next action
Step 9 (report + optional Power BI dashboard): "Read CLAUDE.md and PROGRESS.md, then start Step 9."
Activate the venv first: .venv\Scripts\activate
Carry into Step 9: 6-8 page report (.docx) or PowerPoint answering the three business questions
directly (answers drafted in README "The three business questions" and docs/PROJECT_WALKTHROUGH.md);
reuse reports/figures/; state all caveats (simulated, enriched 10% fraud, balance-column dependence,
illustrative cost assumptions, threshold-rule caveat). Decide: .docx vs .pptx; Power BI or not.

## Log
- 2026-10-27: Docs tidy. README (business-question answers, limitations, notebook guide), CLAUDE.md
  (repo layout, test and pinning rules, notebook-editing note), PROGRESS.md restructured, docs/
  updated (WORKFLOW as-built notes and real resume bullets, walkthrough step map, interview notes Q&A
  and pitch).
- 2026-10-27: Step 8 done and pushed as six commits. Notebook 9.1 saves the train-set pipeline
  (model/fraud_model.joblib, 0.8 MB) + model/fraud_model_metadata.json; reload reproduces test
  predictions exactly. 9.2 = serving + monitoring/retraining notes. api/main.py (FastAPI: /health,
  /predict with Pydantic validation -> 422, decide() threshold rule, top 3 SHAP reasons);
  app/streamlit_app.py (calls the API over HTTP; FRAUD_API_URL env var); tests/ (24 pytest tests:
  features, API, saved-model regression) all pass; pytest.ini. Dockerfile (python:3.12.10-slim +
  libgomp1, non-root, HEALTHCHECK) + .dockerignore; image fraud-api built (750 MB) and tested:
  healthy, identical predictions to local. README rewritten to match real files. .gitignore:
  .streamlit/secrets.toml. Beeswarm figure now seeded.
- 2026-10-27: Steps 5-7 done (notebook 6.1-6.5, 7.1-7.4, 8.1-8.3; figures 11-20), pushed as b1a9ea6.
  Test set (tuned LightGBM, threshold 0.5): PR-AUC 0.994, ROC-AUC 0.996, precision 0.996,
  recall 0.978, F1 0.987, accuracy 0.997; TP 223, FN 5, FP 1, TN 2000. 4 of 5 missed frauds come
  from zero-balance senders (59% of legit TRANSFER/CASH_OUT senders also start at 0). Brier 0.0025;
  99.9% of probabilities are <0.01 or >0.99. Realism: precision ~0.95 at 1% fraud (pessimistic
  0.78), ~0.66 at 0.1%; steps 1-7 slice 19/20 caught, 1 false alarm. Money (test, base
  assumptions): no model -233.8M; simple rule -1.12M; model@0.5 -0.62M; model@0.00032 +1.72M
  (226 caught, 2 missed, 14 false alarms; 84% of perfect model's 2.05M). Errors cost ~0.33M.
  Sensitivity (18 scenarios): threshold 0.00032 or 0.00056, profit always positive.
  SHAP top drivers: drains_whole_balance (3.18), error_balance_orig (1.61), oldbalanceDest (1.24).
- 2026-10-27: Step 4 done (notebook 4.1-4.3, 5.1-5.3). Stratified 80/20 split (train 8,913 /
  914 fraud; test 2,229 / 228). LogReg baseline PR-AUC 0.994 (0.915 without engineered features).
  Imbalance: weights chosen (4.3: with balance features none/weights/SMOTE all ~0.994; without:
  SMOTE 0.930, weights 0.915, none 0.904, gap within fold std). 6 models x 3 feature sets:
  ensembles ~0.995 with or without engineered features, ~0.51-0.66 with type + amount only ->
  balance columns drive the scores. Tuned CV PR-AUC: RF 0.9964, XGB 0.9961, LGBM 0.9960,
  HGB 0.9953, LogReg 0.9943 (no gain), DT 0.9926 (0.974 -> 0.993, overfitting removed). Final
  model: tuned LightGBM. Figures 09, 10 saved. .gitignore: mlflow.db, mlartifacts/.
- 2026-10-27: Step 3 done. model/features.py (FraudFeatures: keeps type, amount, 4 balances;
  drops step/nameOrig/nameDest; adds error_balance_orig, error_balance_dest, drains_whole_balance,
  dest_zero_before_after). Notebook 3.1-3.3: build_preprocessor() = FraudFeatures + one-hot type
  -> 14 inputs (10 without balance features). Single-feature AUC (TRANSFER+CASH_OUT):
  drains 0.986, error_balance_orig 0.944, oldbalanceOrg 0.914 (quirk), amount 0.629. Strongest
  feature pair: old/new dest balance 0.81, so no duplicates; all kept. Figure 08 saved.
- 2026-10-27: Step 2 (EDA) done, notebook Section 2.1-2.7, 7 figures in reports/figures/.
  Findings: 10.25% fraud (accuracy misleading); fraud only in TRANSFER (38.5%) and CASH_OUT
  (30.9%); within those, fraud median amount ~2x legit (353K vs 167K), every amount above 3.78M is
  fraud, 14 fraud rows at exactly 10M (simulator cap); legit rows exist only in steps 1-7 (steps
  8-95 are 100% fraud -> drop step); 97.1% of fraud moves the whole origin balance vs 0.0% of legit;
  legit balances often don't add up (60% start at 0) = simulator quirk; 96% of fraud TRANSFERs go
  to a zero-balance destination; merchants receive only PAYMENTs (flag redundant); Spearman used
  for correlations (Pearson distorted by huge values: 0.93 vs 0.34).
- 2026-10-26: Claude Code session, Step 1 done. CLAUDE.md updated (Python 3.12; code-placement
  rule). Created .venv on Python 3.12.10 and installed requirements-dev.txt (first attempt stalled
  on a network drop; re-ran with --timeout 60 --retries 10). Created notebooks/fraud_detection.ipynb:
  Section 0 problem statement + business questions, Section 1 loads the data (11,142 x 10),
  Sections 2-10 as headers. Ran top to bottom with nbconvert --execute, outputs saved.
  First commit and GitHub remote (antonychirayil/mobile-money-fraud-detection) already existed.
- 2026-10-26: Cowork session. Planning and scaffolding only: dataset profiled; plan, stack and rules
  written (CLAUDE.md, docs/WORKFLOW.md); folder structure, .gitignore and requirements-dev.txt
  created; dataset copied into data/.
