ETL + ML Pipeline with Apache Airflow

A production-style ETL pipeline that ingests sensor data every 10 minutes, cleans and scales it, trains a machine learning model, and stores both the cleaned data and predictions in SQLite.

Demo video: YOUR_VIDEO_LINK_HERE

------------------------------------------------------------
ARCHITECTURE
------------------------------------------------------------

Mock Source  -->  Extract  -->  raw_data (SQLite)
                        |
                        v
                  Transform  -->  processed_data.csv
                        |
                        v
                     Load  -->  processed_data (SQLite)
                        |
                        v
                       ML  -->  predictions (SQLite)

All stages are orchestrated by Apache Airflow on a "*/10 * * * *" schedule (every 10 minutes).

------------------------------------------------------------
DATA FLOW
------------------------------------------------------------

1. Extract (extract.py + mock_api.py)
   Pulls 20 mock sensor records and inserts them into raw_data using INSERT OR IGNORE with a UNIQUE(timestamp) constraint. This is the deduplication guarantee.

2. Transform (transform.py)
   Reads raw_data, drops rows with null values on critical fields, deduplicates timestamps, converts to UTC ISO-8601, and applies z-score scaling to the four numeric features. Writes a CSV for the next stage.

3. Load (load.py)
   Reads the CSV and inserts into processed_data with the same idempotency guarantee. Schema stores both raw and scaled feature values for analytical queries.

4. ML (ml_model.py)
   Trains a RandomForestClassifier on the four scaled features with class_weight="balanced" to handle the imbalanced failure labels. Evaluates with a holdout split, refits on all rows, and writes predictions with probabilities to the separate predictions table.

------------------------------------------------------------
DATABASE SCHEMA
------------------------------------------------------------

Three tables, all with UNIQUE(timestamp) for idempotency:

raw_data
  Purpose: Untouched source records
  Key columns: timestamp, temperature, humidity, pressure, vibration, failure

processed_data
  Purpose: Cleaned + scaled features
  Key columns: All raw columns plus 4 *_scaled columns

predictions
  Purpose: Model output
  Key columns: timestamp, actual_failure, predicted_failure, failure_probability

Indexes on timestamp in processed_data and predictions support time-range analytical queries.

------------------------------------------------------------
SCHEDULING
------------------------------------------------------------

Cron: */10 * * * *  (every 10 minutes)
Retries: 2 with 1-minute delay (automatic recovery on transient failures)
Max active runs: 1 (prevents overlapping runs)
Catchup: false (no backfill of historical 10-minute slots)

------------------------------------------------------------
WHY CLASSIFICATION
------------------------------------------------------------

The target "failure" is a binary outcome (0 or 1), so classification is the correct model type. RandomForestClassifier was chosen because it handles small, imbalanced datasets well and produces probabilities useful for threshold-based alerting downstream.

class_weight="balanced" compensates for the approximately 20% positive rate, trading precision for recall - the right trade-off when a missed failure is costlier than a false alarm. The failure_probability column in the predictions table lets downstream systems tune the threshold without retraining.

------------------------------------------------------------
PROJECT STRUCTURE
------------------------------------------------------------

dags/
  db.py            SQLite connection + schema (3 tables)
  mock_api.py      Mock sensor data source
  extract.py       Extract: mock source -> raw_data
  transform.py     Transform: clean + scale -> CSV
  load.py          Load: CSV -> processed_data
  ml_model.py      ML: train + predict -> predictions
  etl_ml_dag.py    Airflow DAG (5 tasks, */10 * * * *)

requirements.txt   Python dependencies
docker-compose.yaml  Airflow (compose-based deployment)
README.md
.gitignore

------------------------------------------------------------
RUNNING
------------------------------------------------------------

Option A - Airflow (Docker)

docker compose up -d

Then open http://localhost:8080 (admin / airflow). Toggle etl_ml_pipeline ON, then click Trigger DAG.

Option B - Standalone container (single command)

docker run -d --name airflow -p 8080:8080 \
  -v "$(pwd)/dags:/opt/airflow/dags" \
  -v "$(pwd)/etl.db:/opt/airflow/etl.db" \
  -e ETL_DB_PATH=/opt/airflow/etl.db \
  apache/airflow:2.9.0 standalone

Option C - Run one pipeline pass directly

pip install pandas scikit-learn

python -c "
from dags.db import init_db
from dags.extract import extract
from dags.transform import transform
from dags.load import load
from dags.ml_model import train_and_predict
init_db(); extract(); p=transform(); load(p); train_and_predict()
"

------------------------------------------------------------
VERIFICATION
------------------------------------------------------------

After a run, check the database:

python3 -c "import sqlite3; c=sqlite3.connect('etl.db'); [print(t, c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]) for t in ['raw_data','processed_data','predictions']]; c.close()"

Expected after one run:

raw_data 20
processed_data 17
predictions 17

The 3-row difference between raw and processed is the null-humidity rows intentionally injected into the mock source and dropped by the transform.

------------------------------------------------------------
ASSUMPTIONS AND LIMITATIONS
------------------------------------------------------------

- Source is mock data. Permitted by the case study. Swapping to a real API or CSV drop requires changing only mock_api.py and the acquisition line in extract.py; all downstream code is unchanged.

- Failure labels are synthetic and assumed available at ingestion time. In a production setting they would arrive later via a maintenance log (which would require a separate labeling DAG).

- SQLite is used for simplicity. All database access is isolated in db.py behind a thin connection layer, so migrating to PostgreSQL is a one-line change.

- Airflow metadata runs on SQLite inside a single container for the demo. Production would use Postgres-backed metadata in a managed Airflow (MWAA, Composer) or a Kubernetes deployment; the DAGs and application code are unchanged.

------------------------------------------------------------
DELIVERABLES
------------------------------------------------------------

[x] Airflow DAG (Python) - dags/etl_ml_dag.py
[x] ETL & ML code - 6 modules in dags/
[x] Database schema - documented above
[x] README (architecture, data flow, scheduling)
[x] Video demo - link at the top
