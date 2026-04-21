"""
Better Prompt — database models.
SQLAlchemy ORM definitions and matching Pydantic schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase


# ── SQLAlchemy base ───────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── ORM: prompt runs ──────────────────────────────────────────────────────────
class PromptRunORM(Base):
    """
    Records every single LLM call made through the runner.
    Stores the input, output, cost, latency, and success status.
    """
    __tablename__ = "prompt_runs"

    id            = Column(String,  primary_key=True,
                           default=lambda: str(uuid.uuid4()))
    prompt_name   = Column(String,  default="")
    model         = Column(String,  default="")
    provider      = Column(String,  default="")
    input_text    = Column(Text,    default="")
    output_text   = Column(Text,    default="")
    cost_usd      = Column(Float,   default=0.0)
    latency_ms    = Column(Float,   default=0.0)
    tokens_input  = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    success       = Column(Boolean, default=True)
    error         = Column(Text,    nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)


# ── ORM: evaluation results ───────────────────────────────────────────────────
class EvaluationResultORM(Base):
    """
    Stores the result of a single metric applied to a single run.
    One run can have many evaluation results (one per metric).
    """
    __tablename__ = "evaluation_results"

    id          = Column(String,  primary_key=True,
                         default=lambda: str(uuid.uuid4()))
    run_id      = Column(String,  default="")
    metric_name = Column(String,  default="")
    score       = Column(Float,   default=0.0)
    passed      = Column(Boolean, default=False)
    details     = Column(Text,    default="")
    created_at  = Column(DateTime, default=datetime.utcnow)


# ── ORM: test cases ───────────────────────────────────────────────────────────
class TestCaseORM(Base):
    """
    Stores individual test cases for reuse across evaluation runs.
    """
    __tablename__ = "test_cases"

    id              = Column(String, primary_key=True,
                             default=lambda: str(uuid.uuid4()))
    task_name       = Column(String, default="")
    input_text      = Column(Text,   default="")
    expected_output = Column(Text,   nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class PromptRunSchema(BaseModel):
    """
    Pydantic schema for PromptRunORM.
    Used for serialisation and API responses.
    """
    model_config = ConfigDict(from_attributes=True)

    id:            str
    prompt_name:   str            = ""
    model:         str            = ""
    provider:      str            = ""
    input_text:    str            = ""
    output_text:   str            = ""
    cost_usd:      float          = 0.0
    latency_ms:    float          = 0.0
    tokens_input:  int            = 0
    tokens_output: int            = 0
    success:       bool           = True
    error:         Optional[str]  = None
    created_at:    Optional[datetime] = None


class EvaluationResultSchema(BaseModel):
    """
    Pydantic schema for EvaluationResultORM.
    """
    model_config = ConfigDict(from_attributes=True)

    id:          str
    run_id:      str            = ""
    metric_name: str            = ""
    score:       float          = 0.0
    passed:      bool           = False
    details:     str            = ""
    created_at:  Optional[datetime] = None


class TestCaseSchema(BaseModel):
    """
    Pydantic schema for TestCaseORM.
    """
    model_config = ConfigDict(from_attributes=True)

    id:              str
    task_name:       str            = ""
    input_text:      str            = ""
    expected_output: Optional[str]  = None
    created_at:      Optional[datetime] = None
