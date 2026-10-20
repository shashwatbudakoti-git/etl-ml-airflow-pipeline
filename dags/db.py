# dags/db.py
import os
import sqlite3
from pathlib import Path

_default_db = Path(__file__).resolve().parent.parent / "etl.db"
DB_PATH = Path(os.getenv("ETL_DB_PATH", str(_default_db)))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn():
    """Return a SQLite connection with dict-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't already exist (idempotent)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS raw_data (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp    TEXT    NOT NULL UNIQUE,
        temperature  REAL,
        humidity     REAL,
        pressure     REAL,
        vibration    REAL,
        failure      INTEGER,
        ingested_at  TEXT    DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS processed_data (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp            TEXT    NOT NULL UNIQUE,
        temperature          REAL    NOT NULL,
        humidity             REAL    NOT NULL,
        pressure             REAL    NOT NULL,
        vibration            REAL    NOT NULL,
        failure              INTEGER NOT NULL,
        temperature_scaled   REAL    NOT NULL,
        humidity_scaled      REAL    NOT NULL,
        pressure_scaled      REAL    NOT NULL,
        vibration_scaled     REAL    NOT NULL,
        processed_at         TEXT    DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS predictions (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp           TEXT    NOT NULL UNIQUE,
        actual_failure      INTEGER,
        predicted_failure   INTEGER NOT NULL,
        failure_probability REAL    NOT NULL,
        predicted_at        TEXT    DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_processed_ts
        ON processed_data(timestamp);
    CREATE INDEX IF NOT EXISTS idx_predictions_ts
        ON predictions(timestamp);
    """)
    conn.commit()
    conn.close()
