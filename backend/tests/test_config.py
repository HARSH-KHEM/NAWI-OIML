"""Tests for configuration and environment variable loading."""

import os
from app.core.config import Settings


def test_default_settings():
    """Verify default settings instantiation and property computation."""
    cfg = Settings(
        POSTGRES_SERVER="db.metrology.internal",
        POSTGRES_PORT=5432,
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD="test_password",
        POSTGRES_DB="test_db",
    )
    expected_uri = "postgresql+psycopg://test_user:test_password@db.metrology.internal:5432/test_db"
    assert cfg.SQLALCHEMY_DATABASE_URI == expected_uri


def test_database_url_override():
    """Verify explicit DATABASE_URL overrides individual credentials."""
    cfg = Settings(
        DATABASE_URL="postgresql://custom_user:custom_pass@custom_host:5433/custom_db"
    )
    assert cfg.SQLALCHEMY_DATABASE_URI.startswith("postgresql+psycopg://custom_user:custom_pass@custom_host:5433/custom_db")


def test_settings_metadata():
    """Verify application metadata in settings."""
    cfg = Settings()
    assert cfg.PROJECT_NAME
    assert cfg.VERSION
    assert cfg.API_V1_STR == "/api/v1"
