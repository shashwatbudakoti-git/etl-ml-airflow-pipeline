# dags/extract.py
import logging
from db import get_conn
from mock_api import fetch_new_records

logger = logging.getLogger(__name__)


def extract(n=20):
    """Fetch n new records from the source and insert into raw_data."""
    logger.info("Extract: fetching %d new records from source", n)
    records = fetch_new_records(n=n)

    conn = get_conn()
    cur = conn.cursor()
    inserted, skipped = 0, 0

    for r in records:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO raw_data
                (timestamp, temperature, humidity, pressure, vibration, failure)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                r["timestamp"], r["temperature"], r["humidity"],
                r["pressure"], r["vibration"], r["failure"],
            ))
            if cur.rowcount == 1:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            logger.error("Insert failed for %s: %s", r, e)

    conn.commit()
    conn.close()
    logger.info("Extract: inserted=%d skipped=%d", inserted, skipped)
    return inserted
