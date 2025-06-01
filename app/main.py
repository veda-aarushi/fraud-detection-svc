from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
import aioredis

from .db.models import init_db
from .db.repository import get_db_session, create_transaction, get_transaction
from .auth import get_current_user, create_access_token

app = FastAPI(
    title="Fraud Detection Service",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Add Prometheus instrumentation on every request
Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)

redis = None  # will hold our Redis client

@app.on_event("startup")
async def on_startup():
    # 1) Ensure Postgres tables exist
    await init_db()

    # 2) Create a Redis client (singleton)
    global redis
    redis = await aioredis.from_url("redis://localhost:6379", encoding="utf8", decode_responses=True)

@app.on_event("shutdown")
async def on_shutdown():
    global redis
    if redis:
        await redis.close()

@app.get("/health")
async def health_check():
    # Quick SELECT 1 on Postgres
    try:
        async for session in get_db_session():
            await session.execute("SELECT 1")
            break
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Database unreachable")

    # Ping Redis
    try:
        await redis.ping()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Redis unreachable")

    return JSONResponse({"status": "ok"})

@app.post("/token")
async def token_endpoint():
    # Demo-only: returns a bearer JWT for a “demo_user”
    access_token = create_access_token({"sub": "demo_user"})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/transactions")
async def add_transaction(trx: dict, user: dict = Depends(get_current_user)):
    async for session in get_db_session():
        created = await create_transaction(session, trx)
        return created

@app.get("/transactions/{transaction_id}")
async def read_transaction(transaction_id: str, user: dict = Depends(get_current_user)):
    async for session in get_db_session():
        trx = await get_transaction(session, transaction_id)
        if not trx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return trx
