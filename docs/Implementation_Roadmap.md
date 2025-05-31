# Implementation Roadmap – Fraud Detection Service

## Phase 0 – Project Bootstrap
0.1 Create Git repo & push blueprint  
0.2 Init Poetry / pip-tools & lock deps  
0.3 Add CI (GitHub Actions) – lint, type-check, tests  
0.4 Dockerize base images (API, worker)  
0.5 Compose local stack (Kafka, Redis, Postgres, Prometheus)

## Phase 1 – Core Domain & Persistence
1.1 Define Pydantic schemas (`TransactionIn`, `ScoreOut`)  
1.2 Design SQL model + Alembic migration  
1.3 Implement repository layer (CRUD, feature fetch)  
1.4 Seed demo data script

## Phase 2 – API Gateway
2.1 Scaffold FastAPI app & health route  
2.2 Integrate Auth0 JWT + FastAPI-Users  
2.3 Add `/score` endpoint – mock model  
2.4 Add rate limiting (slowapi)  
2.5 Expose `/metrics` via Prometheus instrumentation

## Phase 3 – ML Pipeline
3.1 Baseline Isolation Forest training script  
3.2 Wrap model inference util (`predict.py`)  
3.3 Celery retrain task + nightly schedule  
3.4 MLflow Model Registry integration  
3.5 Blue-green deployment helper

## Phase 4 – Streaming Scoring
4.1 Define Kafka topics  
4.2 Flink SQL job: enrich + score  
4.3 Redis feature cache & invalidation logic  
4.4 Kafka Connect sink to Elasticsearch (optional)

## Phase 5 – Observability & Alerting
5.1 Prometheus scrape configs  
5.2 Grafana dashboards  
5.3 Alertmanager → Slack integration

## Phase 6 – Kubernetes Deployment
6.1 Write Helm chart  
6.2 Configure HPA on CPU & Kafka lag  
6.3 GitHub Actions → build & push images → helm upgrade

## Phase 7 – Hardening & Add-Ons
7.1 Chaos testing (latency injection)  
7.2 Feature store TTL eviction metrics  
7.3 Concept-drift detector & auto-retrain
