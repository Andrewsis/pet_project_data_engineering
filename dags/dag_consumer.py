from datetime import timedelta, datetime
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow import DAG

default_args = {
    'owner': 'andrewsis',
    'retries': 5,
    'retry_delay': timedelta(seconds=10),
}

# Определяем DAG
with DAG(
        dag_id='spark_consumer_dag',
        default_args=default_args,
        start_date=datetime(2025, 1, 27),
        schedule_interval='@once',
        max_active_runs=1
) as consumer_dag:
    dag_spark_consumer = SparkSubmitOperator(
        task_id='spark_consumer',
        application='/opt/airflow/dags/spark_consumer.py',
        conf={
            "spark.jars.packages": "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4",
            "spark.jars": "/opt/postgresql-42.2.23.jar"
        },
        application_args=[
            "--kafka-bootstrap-servers", "kafka:9093",
            "--topic", "crypto_topic",
            "--jdbc-url", "jdbc:postgresql://postgres:5432/test",
            "--user", "airflow",
            "--password", "airflow",
        ],
        executor_cores=1,
        executor_memory='1g',
        driver_memory='512m',
        num_executors=1,
    )

    dag_spark_consumer
