import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from db import get_conn

logger = logging.getLogger(__name__)
MODEL_FEATURES = ["temperature_scaled", "humidity_scaled",
                  "pressure_scaled", "vibration_scaled"]


def train_and_predict():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM processed_data", conn)
    conn.close()
    if len(df) < 10:
        return 0
    X = df[MODEL_FEATURES].values
    y = df["failure"].astype(int).values
    try:
        if len(np.unique(y)) == 2 and min(np.bincount(y)) >= 2:
            X_tr, X_te, y_tr, y_te = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y)
            m = RandomForestClassifier(n_estimators=50, random_state=42,
                                       class_weight="balanced").fit(X_tr, y_tr)
            yh = m.predict(X_te)
            logger.info("ML: holdout acc=%.3f f1=%.3f",
                        accuracy_score(y_te, yh),
                        f1_score(y_te, yh, zero_division=0))
    except Exception as e:
        logger.warning("ML: holdout skipped: %s", e)
    model = RandomForestClassifier(n_estimators=50, random_state=42,
                                   class_weight="balanced").fit(X, y)
    probs = model.predict_proba(X)[:, 1]
    preds = (probs >= 0.5).astype(int)
    conn = get_conn(); cur = conn.cursor()
    inserted = 0
    for i, row in df.reset_index(drop=True).iterrows():
        cur.execute(
            "INSERT OR IGNORE INTO predictions "
            "(timestamp, actual_failure, predicted_failure, failure_probability) "
            "VALUES (?, ?, ?, ?)",
            (row["timestamp"], int(row["failure"]),
             int(preds[i]), float(probs[i])))
        inserted += cur.rowcount
    conn.commit(); conn.close()
    logger.info("ML: inserted=%d predictions", inserted)
    return inserted
