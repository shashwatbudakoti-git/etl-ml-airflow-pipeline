import logging
import pandas as pd
from db import get_conn

logger = logging.getLogger(__name__)


def load(csv_path):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        return 0
    if df.empty:
        return 0
    conn = get_conn(); cur = conn.cursor()
    inserted = 0
    for _, row in df.iterrows():
        cur.execute(
            "INSERT OR IGNORE INTO processed_data "
            "(timestamp, temperature, humidity, pressure, vibration, failure, "
            "temperature_scaled, humidity_scaled, pressure_scaled, vibration_scaled) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (row["timestamp"], row["temperature"], row["humidity"],
             row["pressure"], row["vibration"], int(row["failure"]),
             row["temperature_scaled"], row["humidity_scaled"],
             row["pressure_scaled"], row["vibration_scaled"]))
        inserted += cur.rowcount
    conn.commit(); conn.close()
    logger.info("Load: inserted=%d", inserted)
    return inserted
