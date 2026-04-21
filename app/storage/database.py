"""
Better Prompt — database layer.
Engine setup, session management, and CRUD helper functions.
"""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, EvaluationResultORM, PromptRunORM

# ── Engine setup ──────────────────────────────────────────────────────────────
_URL = "sqlite:///betterprompt.db"
try:
    from app.config import settings
    _URL = settings.database_url
except Exception:
    pass

engine = create_engine(
    _URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── Init ──────────────────────────────────────────────────────────────────────
def init_db() -> None:
    """
    Create all database tables if they do not already exist.
    Safe to call multiple times — will not drop existing data.
    Call this once at application startup.
    """
    Base.metadata.create_all(bind=engine)


# ── Session context manager ───────────────────────────────────────────────────
@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Provide a transactional database session.

    Usage:
        with get_session() as db:
            db.add(some_orm_object)

    Automatically commits on success and rolls back on exception.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Prompt run CRUD ───────────────────────────────────────────────────────────
def save_run(data: dict) -> PromptRunORM:
    """
    Save a new prompt run record to the database.

    Args:
        data: Dict matching PromptRunORM columns.

    Returns:
        The newly created PromptRunORM instance.
    """
    row = PromptRunORM(id=str(uuid.uuid4()), **data)
    with get_session() as db:
        db.add(row)
    return row


def get_runs(limit: int = 50) -> list[PromptRunORM]:
    """
    Retrieve the most recent prompt runs.

    Args:
        limit: Maximum number of runs to return. Default 50.

    Returns:
        List of PromptRunORM instances ordered by newest first.
    """
    with get_session() as db:
        return (
            db.query(PromptRunORM)
            .order_by(desc(PromptRunORM.created_at))
            .limit(limit)
            .all()
        )


def get_run_by_id(run_id: str) -> PromptRunORM | None:
    """
    Retrieve a single prompt run by its ID.

    Args:
        run_id: The UUID string of the run.

    Returns:
        PromptRunORM instance or None if not found.
    """
    with get_session() as db:
        return (
            db.query(PromptRunORM)
            .filter(PromptRunORM.id == run_id)
            .first()
        )


# ── Evaluation result CRUD ────────────────────────────────────────────────────
def save_evaluation(data: dict) -> EvaluationResultORM:
    """
    Save a new evaluation result record to the database.

    Args:
        data: Dict matching EvaluationResultORM columns.

    Returns:
        The newly created EvaluationResultORM instance.
    """
    row = EvaluationResultORM(id=str(uuid.uuid4()), **data)
    with get_session() as db:
        db.add(row)
    return row


def get_evaluations_for_run(run_id: str) -> list[EvaluationResultORM]:
    """
    Retrieve all evaluation results for a specific run.

    Args:
        run_id: The UUID string of the parent run.

    Returns:
        List of EvaluationResultORM instances for that run.
    """
    with get_session() as db:
        return (
            db.query(EvaluationResultORM)
            .filter(EvaluationResultORM.run_id == run_id)
            .all()
        )


def get_recent_evaluations(limit: int = 100) -> list[EvaluationResultORM]:
    """
    Retrieve the most recent evaluation results across all runs.

    Args:
        limit: Maximum number of results to return. Default 100.

    Returns:
        List of EvaluationResultORM instances ordered by newest first.
    """
    with get_session() as db:
        return (
            db.query(EvaluationResultORM)
            .order_by(desc(EvaluationResultORM.created_at))
            .limit(limit)
            .all()
        )
