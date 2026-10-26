# Fraud Detection: FastAPI + Streamlit

```
fraud-detection/
├── model/
│   ├── train_demo.py        # trains a demo model -> fraud_model.joblib
│   └── fraud_model.joblib   # created when you run train_demo.py
├── api/
│   └── main.py              # FastAPI: loads model, /predict returns score + SHAP reasons
├── app/
│   └── streamlit_app.py     # Streamlit UI: form -> calls the API -> shows result
└── requirements.txt
```

## Run it

```bash
pip install -r requirements.txt
python model/train_demo.py              # 1. create the model file

uvicorn api.main:app --reload           # 2. terminal 1: start the API
                                        #    open http://localhost:8000/docs to test it

streamlit run app/streamlit_app.py      # 3. terminal 2: start the frontend
```

Run all commands from the `fraud-detection/` folder.

## Using your real model

1. Train in your notebook, then save it: `joblib.dump(model, "model/fraud_model.joblib")`
   (fit on a pandas DataFrame so the column names are stored in the model).
2. Change the fields in the `Transaction` class in `api/main.py` to match your columns.
3. Change the form inputs and `payload` in `app/streamlit_app.py` to match.
4. Tune `FRAUD_THRESHOLD` using precision/recall on validation data.

## How it works

Streamlit sends the form data as JSON to `POST /predict`. FastAPI validates it,
runs the model, computes SHAP values, and returns the fraud probability plus the
top 3 reasons. The frontend never touches the model, so you can swap the UI
(React, a mobile app, another service) without changing the API.
