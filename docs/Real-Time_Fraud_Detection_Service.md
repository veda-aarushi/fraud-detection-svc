# Real-Time Fraud Detection Service

This microservice flags suspicious transactions in **< 150 ms** by combining streaming feature aggregation, an Isolation Forest model, and rule-based heuristics. It is designed to demo *production-grade* system design patterns—event-driven ingestion, elastic scaling, robust observability, and secure, quota-controlled APIs.

Key ideas:

| Pillar                   | Design Choice                                                               |
|--------------------------|------------------------------------------------------------------------------|
| **Streaming Ingestion**  | Kafka topic `transactions.raw` → Kafka Connect → PostgreSQL feature-store    |
| **Online Scoring**       | FastAPI HTTP endpoint for single calls *(P99 < 150 ms)*                      |
| **Stream Scoring**       | Flink job reads `transactions.raw`, enriches from Redis feature-cache, writes `transactions.scored` |
| **Model Lifecycle**      | Celery + Redis queue retrains nightly & A/B deploys via MLflow models registry |
| **Security**             | JWT Auth (Auth0) + IP-aware rate limiting (50 req/min)                       |
| **Observability**        | Prometheus metrics + OpenTelemetry traces, Grafana dashboards, Slack alerts  |

---

## 🚀 Features

### 1. Asynchronous Model Retraining  
`POST /train` *(admin only)*  
* **Auth** – Basic `admin:secret`  
* **Rate limit** – 5 req/min  
* **Return** – Celery task-ID & `/status/<id>` polling

### 2. Score a Transaction  
`POST /score` *(real-time)*

**Request**:
```json
{
  "transaction_id": "9f172…",
  "amount": 125.50,
  "card_bin": "4136…",
  "merchant_cat": "5732",
  "ts": "2025-05-30T16:02:17Z"
}
