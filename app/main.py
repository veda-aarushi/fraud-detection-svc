from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
import aioredis

from .db.models     import init_db, AsyncSessionLocal
from .db.repository import create_transaction, get_transaction
from .auth          import (
    get_db,
    create_user,
    get_user_by_username,
    create_access_token,
    get_current_user,
    verify_password
)

app = FastAPI(title="Fraud Detection Service")

@app.on_event("startup")
async def on_startup():
    await init_db()
    app.state.redis = await aioredis.from_url(
        "redis://localhost:6379", encoding="utf8", decode_responses=True
    )

@app.on_event("shutdown")
async def on_shutdown():
    await app.state.redis.close()

@app.get("/health")
async def health_check(db=Depends(get_db)):
    # Postgres
    try:
        async with db as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(500, f"Database unreachable ({e})")
    # Redis
    try:
        await app.state.redis.ping()
    except Exception as e:
        raise HTTPException(500, f"Redis unreachable ({e})")
    return JSONResponse({"status": "ok"})

@app.post("/auth/register", status_code=201)
async def register(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    if await get_user_by_username(db, form.username):
        raise HTTPException(400, "Username already taken")
    user = await create_user(db, form.username, form.password)
    return {"id": user.id, "username": user.username}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = await get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Incorrect credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me")
async def read_me(user=Depends(get_current_user)):
    return {"id": user.id, "username": user.username}

@app.post("/transactions")
async def add_transaction(trx: dict, user=Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        created = await create_transaction(session, trx)
        return created

@app.get("/transactions/{transaction_id}")
async def read_transaction(transaction_id: str, user=Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        trx = await get_transaction(session, transaction_id)
        if not trx:
            raise HTTPException(404, "Transaction not found")
        return trx
