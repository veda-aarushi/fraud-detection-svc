# app/db/user_models.py

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as Uuid
from sqlalchemy.orm import declarative_base

# Shared Base for all models (so that Transaction and User share metadata)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    email = Column(
        String(length=320),
        unique=True,
        index=True,
        nullable=False
    )
    username = Column(
        String(length=32),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password = Column(
        String(length=128),
        nullable=False
    )
    is_active = Column(
        Boolean(),
        default=True,
        nullable=False
    )
    is_superuser = Column(
        Boolean(),
        default=False,
        nullable=False
    )
    is_verified = Column(
        Boolean(),
        default=False,
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )
