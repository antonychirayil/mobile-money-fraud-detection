# PROGRESS.md: handoff log

Update at the end of every session. Newest entry on top of the Log section.

## Status (started 2026-10-26)
- [ ] Step 1  Setup: venv, git + GitHub repo, requirements installed, notebook created
- [ ] Step 2  EDA with charts and insight captions
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
- Not yet decided (decide in the step where it comes up): time-based split vs stratified split;
  cost assumptions for false positives; final model choice.

## Open items / reminders
- README.md and requirements.txt were already in the folder; they were left untouched.
  README lists api/, app/ and model/train_demo.py that don't exist yet.
- Run git init, make a first commit and create the GitHub repo (Step 1).
- Start applying for jobs in week 1; do not wait for the project to finish.

## Next action
Start Step 1 in Claude Code: "Read CLAUDE.md and PROGRESS.md, then start Step 1 (setup)."
Walk through venv, git init, installing requirements-dev.txt, and creating the notebook.

## Log
- 2026-10-26: Cowork session. Planning and scaffolding only.
