# PROGRESS.md: handoff log

Update at the end of every session. Newest entry on top of the Log section.

## Status (started 2026-10-26)
- [x] Step 1  Setup: venv, git + GitHub repo, requirements installed, notebook created
- [x] Step 2  EDA with charts and insight captions
- [ ] Step 3  Feature engineering and encoding
- [ ] Step 4  Modelling: baseline, then tree/boosting models, CV, tuning, imbalance handling
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
Start Step 3 (feature engineering): "Read CLAUDE.md and PROGRESS.md, then start Step 3."
Activate the venv first: .venv\Scripts\activate
Carry into Step 3 from the EDA: no step/hour/day features; no "is merchant" flag; build the
balance-error features (they capture "amount equals whole balance", the strongest signal, which
correlation cannot show); expect near-perfect scores and plan the with/without-balance comparison.

## Log
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
