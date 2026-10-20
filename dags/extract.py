import logging
from db import get_conn
from mock_api import fetch_new_records

logger = logging.getLogger(__name__)


def extract(n=20):
    records = fetch_new_records(n=n)
    conn = get_conn()
    cur = conn.cursor()
    inserted, skipped = 0, 0
    for r in records:
        try:
            cur.execute(
                "INSERT OR IGNORE INTO raw_data "
                "(timestamp, temperature, humidity, pressure, vibration, failure) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (r["timestamp"], r["temperature"], r["humidity"],
                 r["pressure"], r["vibration"], r["failure"]))
            inserted += cur.rowcount
            skipped  += (1 - cur.rowcount)
        except Exception as e:
            logger.error("Insert failed: %s", e)
    conn.commit(); conn.close()
    logger.info("Extract: inserted=%d skipped=%d", inserted, skipped)
    return inserted
