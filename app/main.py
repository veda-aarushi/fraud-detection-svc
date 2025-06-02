# app/main.py
from __future__ import annotations

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
import aioredis
import asyncpg

from .auth import get_current_user, create_access_token
from .db.models import AsyncSessionLocal
from .db.repository import create_transaction, get_transaction

app = FastAPI(
    title="Fraud Detection Service",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)

redis: aioredis.Redis | None = None

@app.on_event("startup")
async def on_startup():
    # Create Redis client
    global redis
    redis = await aioredis.from_url(
        "redis://localhost:6379", encoding="utf8", decode_responses=True
    )

@app.on_event("shutdown")
async def on_shutdown():
    global redis
    if redis:
        await redis.close()

@app.get("/health")
async def health_check():
    # 1) Check Postgres via asyncpg.connect on port 5433
    try:
        conn = await asyncpg.connect(
            user="postgres",
            password="postgres",
            database="fraud_db",
            host="127.0.0.1",
            port=5433,
        )
        await conn.execute("SELECT 1;")
        await conn.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database unreachable ({e})"
        )

    # 2) Check Redis
    try:
        if not redis:
            raise RuntimeError("Redis client not initialized")
        await redis.ping()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Redis unreachable ({e})"
        )

    return JSONResponse({"status": "ok"})

@app.post("/token")
async def token_endpoint():
    # Demo‐only: always returns a “demo_user” token
    access_token = create_access_token({"sub": "demo_user"})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/transactions")
async def add_transaction(trx: dict, user: dict = Depends(get_current_user)):
    # Use SQLAlchemy to save the incoming JSON into Postgres
    async with AsyncSessionLocal() as session:
        new = await create_transaction(session, trx)
        return new

@app.get("/transactions/{transaction_id}")
async def read_transaction(transaction_id: str, user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        trx = await get_transaction(session, transaction_id)
        if not trx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return trx
