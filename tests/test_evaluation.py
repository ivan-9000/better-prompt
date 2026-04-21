"""
Tests for app/evaluation/metrics/deterministic.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.evaluation.metrics.deterministic import (
    exact_match,
    json_validity,
    keyword_presence,
    length_constraint,
)


# ── Exact match ───────────────────────────────────────────────────────────────
def test_em_pass():
    r = exact_match("hello", "hello")
    assert r.score == 1.0
    assert r.passed is True


def test_em_fail():
    r = exact_match("hello", "world")
    assert r.score == 0.0
    assert r.passed is False


def test_em_case_insensitive():
    r = exact_match("HELLO", "hello", case_sensitive=False)
    assert r.score == 1.0
    assert r.passed is True


def test_em_case_sensitive():
    r = exact_match("HELLO", "hello", case_sensitive=True)
    assert r.score == 0.0
    assert r.passed is False


# ── JSON validity ─────────────────────────────────────────────────────────────
def test_jv_valid():
    r = json_validity('{"name": "Ivan", "age": 30}')
    assert r.score == 1.0
    assert r.passed is True


def test_jv_invalid():
    r = json_validity("this is not json")
    assert r.score == 0.0
    assert r.passed is False


def test_jv_markdown_block():
    r = json_validity('```json\n{"key": "value"}\n```')
    assert r.score == 1.0
    assert r.passed is True


def test_jv_required_keys_pass():
    r = json_validity('{"name": "Ivan", "email": "ivan@example.com"}',
                      required_keys=["name", "email"])
    assert r.score == 1.0
    assert r.passed is True


def test_jv_required_keys_fail():
    r = json_validity('{"name": "Ivan"}',
                      required_keys=["name", "email", "phone"])
    assert r.score < 1.0
    assert r.passed is False


# ── Keyword presence ──────────────────────────────────────────────────────────
def test_kp_all_found():
    r = keyword_presence("the cat sat on the mat", ["cat", "mat"])
    assert r.score == 1.0
    assert r.passed is True


def test_kp_partial():
    r = keyword_presence("only cat here", ["cat", "dog"])
    assert r.score == 0.5
    assert r.passed is False


def test_kp_none_found():
    r = keyword_presence("nothing relevant", ["cat", "dog"])
    assert r.score == 0.0
    assert r.passed is False


def test_kp_case_insensitive():
    r = keyword_presence("The CAT sat down", ["cat"])
    assert r.score == 1.0
    assert r.passed is True


# ── Length constraint ─────────────────────────────────────────────────────────
def test_lc_within_bounds():
    r = length_constraint("hello world", min_len=5, max_len=50)
    assert r.score == 1.0
    assert r.passed is True


def test_lc_too_short():
    r = length_constraint("hi", min_len=10)
    assert r.score == 0.0
    assert r.passed is False


def test_lc_too_long():
    r = length_constraint("a" * 200, max_len=100)
    assert r.score == 0.0
    assert r.passed is False
