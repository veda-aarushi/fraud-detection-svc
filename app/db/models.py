from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Float, DateTime, func

# Use 127.0.0.1 to avoid any IPv6/localhost mismatch
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/fraud_db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    merchant_cat = Column(String, nullable=False)
    card_bin = Column(String, nullable=False)
    ts = Column(DateTime(timezone=True), server_default=func.now())
    label = Column(String, default="unknown")
    fraud_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
