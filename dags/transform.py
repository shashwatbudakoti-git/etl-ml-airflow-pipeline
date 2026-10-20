import logging, tempfile
from pathlib import Path
import pandas as pd
from db import get_conn

logger = logging.getLogger(__name__)
FEATURES = ["temperature", "humidity", "pressure", "vibration"]
CRITICAL = ["timestamp"] + FEATURES + ["failure"]


def transform(output_path=None):
    if output_path is None:
        output_path = str(Path(tempfile.gettempdir()) / "processed_data.csv")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM raw_data", conn)
    conn.close()
    if df.empty:
        return ""
    before = len(df)
    df = df.dropna(subset=CRITICAL)
    logger.info("Transform: dropped %d null rows", before - len(df))
    df = df.drop_duplicates(subset=["timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for col in FEATURES:
        mean, std = df[col].mean(), df[col].std()
        if std == 0 or pd.isna(std):
            std = 1.0
        df[col + "_scaled"] = (df[col] - mean) / std
    df.to_csv(output_path, index=False)
    logger.info("Transform: wrote %d rows", len(df))
    return output_path
