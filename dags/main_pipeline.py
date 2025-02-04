import time
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import json
from kafka import KafkaProducer


def save_to_minio(**kwargs):
    s3_hook = S3Hook(aws_conn_id='minio_conn')

    crypto_url = "https://api4.binance.com/api/v3/ticker/24hr"
    response = requests.get(crypto_url)
    json_data = response.json()

    file_name = f"{kwargs['ds']}.json"
    bucket_name = 'crypto-currency'

    s3_hook.load_string(
        string_data=json.dumps(json_data),
        key=file_name,
        bucket_name=bucket_name,
        replace=True,
    )

def send_to_kafka(**kwargs):
    s3_hook = S3Hook(aws_conn_id='minio_conn')

    file_name = f"{kwargs['ds']}.json"
    bucket_name = 'crypto-currency'

    file_data = s3_hook.read_key(key=file_name, bucket_name=bucket_name)

    producer = KafkaProducer(
        bootstrap_servers=['kafka:9093'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    if file_data:
        print(f"Found {file_name} in MinIO")

        # Deserialize data
        json_data = json.loads(file_data)

        for chunk in json_data:
            # print(f"Send message: {chunk}")
            producer.send('crypto_topic', chunk)

        producer.flush()
    else:
        print(f"Didnt find {file_name} in MinIO")


default_args = {
    'owner': 'andrewsis',
    'retries': 5,
    'retry_delay': timedelta(seconds=10),
}


with DAG(
    dag_id='save_to_minio',
    default_args=default_args,
    start_date=datetime(2025, 1, 27),
    schedule_interval='@daily',
    max_active_runs = 1
) as dag:
    dag_save_to_minio = PythonOperator(
        task_id='save_to_minio',
        python_callable=save_to_minio,
        provide_context=True
    )
    dag_kafka_producer = PythonOperator(
        task_id='kafka_producer',
        python_callable=send_to_kafka,
        provide_context=True,
    )

    dag_save_to_minio >> dag_kafka_producer


