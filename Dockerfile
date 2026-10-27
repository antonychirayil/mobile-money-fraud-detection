# Fraud API: the FastAPI service with the saved model. (The Streamlit demo runs outside Docker.)
# Build:  docker build -t fraud-api .
# Run:    docker run -p 8000:8000 fraud-api     -> http://localhost:8000/docs

# Same Python version the model was saved with (model/fraud_model_metadata.json)
FROM python:3.12.10-slim

# LightGBM needs the OpenMP runtime, which the slim image does not include
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies first: this layer stays cached when only the code changes
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY model/__init__.py model/features.py model/fraud_model.joblib model/fraud_model_metadata.json model/
COPY api/ api/

# Do not run the service as root
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
