# ETL + ML Pipeline with Apache Airflow

A production-style ETL pipeline that ingests mock sensor data every 10 minutes,
cleans and scales it, trains a machine learning model, and stores both the
cleaned data and predictions in SQLite.

## Architecture

    Mock Source  ->  Extract  ->  raw_data (SQLite)
                          |
                          v
                    Transform  ->  processed_data.csv
                          |
                          v
                       Load  ->  processed_data (SQLite)
                          |
                          v
                         ML  ->  predictions (SQLite)

All stages are orchestrated by Apache Airflow on a `*/10 * * * *` schedule.

## Tech stack

- Orchestration: Apache Airflow 2.9 (Docker Compose)
- Language: Python 3.10+
- Database: SQLite (no server required)
- ML: scikit-learn RandomForestClassifier
- Source: Mock API generator (case study permits mock data)

## Project layout

    dags/
      db.py            # SQLite connection + schema
      mock_api.py      # Mock sensor data source
      extract.py       # Extract step
      transform.py     # Clean + scale + write CSV
      load.py          # Load cleaned data into processed_data
      ml_model.py      # Train + predict + store in predictions

## Status

- Phase 1 (ETL + ML modules) — complete
- Phase 2 (repo structure) — complete
- Phase 3 (Airflow DAG + Docker) — pending
- Phase 4 (README + video) — pending
