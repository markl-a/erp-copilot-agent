"""Read-only ERP access for the AI layer.

Guardrails enforced here (not in the prompt):
- only the v_* views are reachable; base tables are not
- only a single SELECT statement; no DDL/DML, no PRAGMA/ATTACH
- a row cap on every query
The same contract maps to Oracle: a read-only DB user granted SELECT on the views only.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = {"v_customer", "v_part", "v_available", "v_price", "v_inbound", "v_customer_parts", "v_pcn"}
_FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum)\b", re.I)
_TABLE_REF = re.compile(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)", re.I)
MAX_ROWS = 200


class QueryRejected(ValueError):
    pass


def connect(path: str = ":memory:") -> sqlite3.Connection:
    db = sqlite3.connect(path, check_same_thread=False)
    db.executescript((ROOT / "sql" / "schema.sql").read_text() + (ROOT / "sql" / "seed.sql").read_text())
    db.row_factory = sqlite3.Row
    return db


def guard(sql: str) -> str:
    s = sql.strip().rstrip(";")
    if ";" in s:
        raise QueryRejected("one statement only")
    if not s.lower().startswith(("select", "with")):
        raise QueryRejected("SELECT only")
    if _FORBIDDEN.search(s):
        raise QueryRejected("write/DDL keyword not allowed")
    tables = {t.lower() for t in _TABLE_REF.findall(s)}
    bad = tables - ALLOWED
    if bad:
        raise QueryRejected(f"not an allowed view: {sorted(bad)}")
    return s


def query(db: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    rows = db.execute(guard(sql), params).fetchmany(MAX_ROWS)
    return [dict(r) for r in rows]
