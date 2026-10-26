# PROGRESS.md: handoff log

Update at the end of every session. Newest entry on top of the Log section.

## Status (started 2026-10-26)
- [x] Step 1  Setup: venv, git + GitHub repo, requirements installed, notebook created
- [x] Step 2  EDA with charts and insight captions
- [x] Step 3  Feature engineering and encoding
- [x] Step 4  Modelling: baseline, then tree/boosting models, CV, tuning, imbalance handling
- [ ] Step 5  Evaluation: precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, curves, calibration
- [ ] Step 6  Financial impact: cost-optimal threshold, with-model vs no-model, sensitivity table
- [ ] Step 7  Explainability with SHAP
- [ ] Step 8  Production-readiness: saved Pipeline, FastAPI, Streamlit, Dockerfile, tests, monitoring notes
- [ ] Step 9  Report (.docx or .pptx) + optional Power BI dashboard
- [ ] Step 10 Package: zip, README, GitHub cleanup, resume bullets

## Done so far (Cowork session, 2026-10-26)
- Dataset profiled; plan, stack and rules written (CLAUDE.md, docs/WORKFLOW.md).
- Folder structure, .gitignore, requirements-dev.txt created. Dataset copied into data/.
- No code written yet.

## Decisions made
- Stack as listed in CLAUDE.md.
- Main notebook: notebooks/fraud_detection.ipynb.
- Python 3.12 (venv made with `py -3.12 -m venv .venv`; 3.14 is the machine default, so call 3.12 explicitly).
- All analysis and training code lives in the notebook. Only the custom feature transformer class
  moves to model/features.py (Step 3), so the saved pipeline can be unpickled by the API.
- data/ stays tracked in git (CSV is under 1 MB and the notebook needs it to run).
- 2026-10-27 (EDA 2.4): all 10,000 legit rows are in steps 1-7; fraud spans steps 1-95, so steps
  8-95 are 100% fraud (sampling artefact). Decision A: drop `step`, create NO hour/day features.
  A time-based split is therefore impossible; Step 4 uses a stratified random split.
  Steps 1-7 (0.77% fraud, 78 cases) can serve as a realism check in Step 5.
- 2026-10-27 (EDA 2.6): merchants (nameDest starting with M) receive only PAYMENTs, so an
  "is merchant" flag duplicates `type`. Decision: leave the flag out.
- 2026-10-27 (Step 3): whole-balance drain as a yes/no flag (drains_whole_balance), not a ratio;
  no "origin emptied" flag. One-hot `type` with handle_unknown="ignore". No scaling in the shared
  preprocessor: scaling is added per model in Step 4 (LR needs it, trees don't).
- 2026-10-27 (Step 4 setup): stratified 80/20 train/test split; stratified 5-fold CV on the
  training set only; imbalance = class weights as main approach + one SMOTE / weights / none
  comparison on the baseline; PR-AUC (average precision) is the CV selection metric.
- 2026-10-27 (4.3 result): with balance features none/weights/SMOTE all PR-AUC ~0.994; without:
  SMOTE 0.930, weights 0.915, none 0.904 (gap within fold std). Decision A: class weights for all
  models (scale_pos_weight for XGBoost).
- 2026-10-27 (5.1): tree ensembles keep PR-AUC ~0.994 even without the 4 engineered features
  (they rebuild them from raw balances); type + amount only drops the best model to ~0.66.
  Decision: compare every model on 3 feature sets (all / no engineered / type + amount only;
  the third is notebook-only experiment code). Gradient Boosting = HistGradientBoostingClassifier
  (classic GradientBoostingClassifier has no class_weight).
- 2026-10-27 (5.2): tuned ALL six models (user choice), 30 Optuna trials each (TPE, seed 42),
  PR-AUC on 5-fold CV, all features; logged to MLflow (mlflow.db in project root, experiment
  "fraud-detection-tuning", 186 runs). Tuned CV PR-AUC: RF 0.9964, XGB 0.9961, LGBM 0.9960,
  HGB 0.9953, LogReg 0.9943 (no gain), DT 0.9926 (0.974 -> 0.993, overfitting removed).
  Ensemble gains (0.001-0.002) are within fold std. Full notebook run now takes ~8.5 min.
- 2026-10-27 (5.3): FINAL MODEL = tuned LightGBM (option A): tied on CV, best on type + amount
  only (0.662), fastest ensemble, good SHAP support, small file. Only this model touches the test set.
- Notebook editing: the Read/NotebookEdit tools can no longer open the notebook (too large);
  cells are inserted/edited with nbformat helper scripts instead.
- Git: no AI attribution lines in commits (CLAUDE.md rule + .claude/settings.local.json).
  Step 1/2 commits were rewritten and force-pushed on 2026-10-27; GitHub's Contributors box may
  still show "claude" until its cache refreshes.
- Not yet decided (decide in the step where it comes up): time-based split vs stratified split;
  cost assumptions for false positives; final model choice.

## Open items / reminders
- README.md and requirements.txt were already in the folder; they were left untouched.
  README lists api/, app/ and model/train_demo.py that don't exist yet.
- Suggested .gitignore additions, not yet applied (user to decide): mlflow.db, mlartifacts/,
  .streamlit/secrets.toml, .vscode/.
- Installed versions are unpinned; pin with pip freeze in Step 10. Note pandas is 3.x
  (text columns show dtype `str`, not `object`).
- Start applying for jobs in week 1; do not wait for the project to finish.

## Next action
Start Step 5 (evaluation, notebook Section 6): "Read CLAUDE.md and PROGRESS.md, then start Step 5."
Activate the venv first: .venv\Scripts\activate
Carry into Step 5: fit `final_pipeline` (5.3) on X_train, score ONCE on X_test: precision, recall,
F1, ROC-AUC, PR-AUC, confusion matrix, ROC + PR curves, calibration. Accuracy reported, never the
headline. Optional realism check: steps 1-7 subset (0.77% fraud). Threshold stays 0.5 here;
cost-based threshold is Step 6 (Section 7).

## Log
- 2026-10-27: Step 4 done (notebook 4.1-4.3, 5.1-5.3). Stratified 80/20 split (train 8,913 /
  914 fraud; test 2,229 / 228). LogReg baseline PR-AUC 0.994 (0.915 without engineered features).
  Imbalance: weights chosen. 6 models x 3 feature sets: ensembles ~0.995 with or without engineered
  features, ~0.51-0.66 with type + amount only -> balance columns drive the scores. Tuned all six
  (MLflow, 186 runs). Final model: tuned LightGBM. Figures 09, 10 saved. .gitignore: mlflow.db,
  mlartifacts/, docs/INTERVIEW_NOTES.md (private notes).
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
- 2026-10-26: Cowork session. Planning and scaffolding only.
