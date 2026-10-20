# dags/load.py
import logging
import pandas as pd
from db import get_conn

logger = logging.getLogger(__name__)


def load(csv_path):
    """Read transform output CSV and insert into processed_data."""
    logger.info("Load: reading %s", csv_path)
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        logger.warning("Load: CSV not found at %s", csv_path)
        return 0

    if df.empty:
        logger.warning("Load: CSV empty")
        return 0

    conn = get_conn()
    cur = conn.cursor()
    inserted, skipped = 0, 0

    for _, row in df.iterrows():
        try:
            cur.execute("""
                INSERT OR IGNORE INTO processed_data
                (timestamp, temperature, humidity, pressure, vibration, failure,
                 temperature_scaled, humidity_scaled, pressure_scaled, vibration_scaled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["timestamp"], row["temperature"], row["humidity"],
                row["pressure"], row["vibration"], int(row["failure"]),
                row["temperature_scaled"], row["humidity_scaled"],
                row["pressure_scaled"], row["vibration_scaled"],
            ))
            if cur.rowcount == 1:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            logger.error("Load insert failed for timestamp %s: %s",
                         row["timestamp"], e)

    conn.commit()
    conn.close()
    logger.info("Load: inserted=%d skipped=%d", inserted, skipped)
    return inserted
