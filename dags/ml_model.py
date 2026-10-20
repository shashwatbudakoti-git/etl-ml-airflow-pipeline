# dags/ml_model.py
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
    """Train RandomForestClassifier on processed_data, store predictions."""
    logger.info("ML: reading processed_data")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM processed_data", conn)
    conn.close()

    if len(df) < 10:
        logger.warning("ML: only %d rows, need >=10 — skipping", len(df))
        return 0

    X = df[MODEL_FEATURES].values
    y = df["failure"].astype(int).values
    class_dist = dict(pd.Series(y).value_counts().sort_index())
    logger.info("ML: %d rows, class distribution %s", len(df), class_dist)

    try:
        if len(np.unique(y)) == 2 and min(np.bincount(y)) >= 2:
            X_tr, X_te, y_tr, y_te = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            eval_model = RandomForestClassifier(
                n_estimators=50, random_state=42, class_weight="balanced"
            )
            eval_model.fit(X_tr, y_tr)
            y_hat = eval_model.predict(X_te)
            logger.info(
                "ML: holdout accuracy=%.3f f1=%.3f",
                accuracy_score(y_te, y_hat),
                f1_score(y_te, y_hat, zero_division=0),
            )
    except Exception as e:
        logger.warning("ML: holdout eval skipped: %s", e)

    model = RandomForestClassifier(
        n_estimators=50, random_state=42, class_weight="balanced"
    )
    model.fit(X, y)
    logger.info("ML: final model trained on %d rows", len(df))

    probabilities = model.predict_proba(X)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    conn = get_conn()
    cur = conn.cursor()
    inserted, skipped = 0, 0
    for i, row in df.reset_index(drop=True).iterrows():
        try:
            cur.execute("""
                INSERT OR IGNORE INTO predictions
                (timestamp, actual_failure, predicted_failure, failure_probability)
                VALUES (?, ?, ?, ?)
            """, (
                row["timestamp"], int(row["failure"]),
                int(predictions[i]), float(probabilities[i]),
            ))
            if cur.rowcount == 1:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            logger.error("ML insert failed for %s: %s", row["timestamp"], e)

    conn.commit()
    conn.close()
    logger.info("ML: predictions inserted=%d skipped=%d", inserted, skipped)
    return inserted
