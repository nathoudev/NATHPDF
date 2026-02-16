


# billing/models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey,UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import secrets

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)

    # relation user → api_keys
    api_keys = relationship("ApiKey", back_populates="user")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    quota_remaining = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    stripe_session_id = Column(String, unique=True, nullable=True)

    # relation api_key → user
    user = relationship("User", back_populates="api_keys")


def generate_api_key() -> str:
    """Génère une API key sécurisée en hexadécimal."""
    return secrets.token_hex(32)

class StripeEvent(Base):
    __tablename__ = "stripe_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    event_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
