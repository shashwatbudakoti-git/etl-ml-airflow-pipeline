from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from db import init_db
from extract import extract
from transform import transform
from load import load
from ml_model import train_and_predict

default_args = {
    "owner": "shashwat",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "email_on_failure": False,
    "depends_on_past": False,
}

with DAG(
    dag_id="etl_ml_pipeline",
    default_args=default_args,
    description="ETL + ML pipeline every 10 minutes",
    schedule_interval="*/10 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["etl", "ml", "demo"],
) as dag:

    t_init = PythonOperator(task_id="init_db", python_callable=init_db)

    t_extract = PythonOperator(
        task_id="extract",
        python_callable=extract,
        op_kwargs={"n": 20},
    )

    t_transform = PythonOperator(
        task_id="transform",
        python_callable=transform,
    )

    t_load = PythonOperator(
        task_id="load",
        python_callable=load,
        op_kwargs={"csv_path": "{{ ti.xcom_pull(task_ids='transform') }}"},
    )

    t_ml = PythonOperator(
        task_id="train_and_predict",
        python_callable=train_and_predict,
    )

    t_init >> t_extract >> t_transform >> t_load >> t_ml
