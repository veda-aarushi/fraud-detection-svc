from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Transaction, AsyncSessionLocal

# Dependency that yields an async DB session
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

# Insert a new transaction
async def create_transaction(db: AsyncSession, trx_data: dict) -> Transaction:
    trx = Transaction(**trx_data)
    db.add(trx)
    await db.commit()
    await db.refresh(trx)
    return trx

# Fetch a transaction by its ID
async def get_transaction(db: AsyncSession, trx_id: str) -> Transaction | None:
    result = await db.execute(select(Transaction).where(Transaction.transaction_id == trx_id))
    return result.scalar_one_or_none()
