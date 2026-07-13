# FinTwin AI

An AI Digital Twin Platform for Intelligent MSME Loan Risk Assessment.

## Project Structure
- `backend/`: FastAPI application, AI models, Celery tasks.
- `frontend/`: Next.js web application.
- `k8s/`: Kubernetes manifests for production deployment.
- `.github/workflows/`: CI/CD pipelines.
- `prometheus/` & `grafana/`: Observability configurations.

## Development Setup

1. Copy `.env.example` to `.env` and fill in the required keys.
2. Run `docker-compose up --build -d` to start the PostgreSQL, Redis, Qdrant, backend, and frontend services locally.

## Production Deployment

FinTwin AI is designed to run on a Kubernetes cluster.

### 1. Configure Secrets
Before applying the manifests, update the `Secret` in `k8s/configmap-secrets.yaml` with your actual production credentials (encoded in base64 if applying via kubectl, or simply update stringData).

### 2. Apply Manifests
Deploy to your cluster using `kubectl`:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap-secrets.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/celery-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/services.yaml
```

### 3. Monitoring
Ensure Prometheus is configured to scrape the `fintwin-backend-svc` endpoints using the provided `prometheus.yml`. Import the `fintwin_dashboard.json` into Grafana to monitor API latency and ML prediction times.
