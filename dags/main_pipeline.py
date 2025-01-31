from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import json
from kafka import KafkaProducer, KafkaAdminClient
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, from_unixtime
from pyspark.sql.types import StructType, StructField, StringType, LongType, DecimalType
from kafka.admin import NewTopic


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

def send_to_kafka(topic_name, **kwargs):
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
            producer.send(topic_name, chunk)

        producer.flush()
    else:
        print(f"Didnt find {file_name} in MinIO")

def spark_consumer(topic_name):
    spark = SparkSession.builder \
        .appName("CryptoDataProcessor") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4") \
        .getOrCreate()

    df = spark.read \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9093") \
        .option("subscribe", topic_name) \
        .load()

    df = df.selectExpr("CAST(value AS STRING)")

    schema = StructType([
        StructField("symbol", StringType(), False),
        StructField("priceChange", DecimalType(20, 8), False),  
        StructField("priceChangePercent", DecimalType(20, 8), False),  
        StructField("weightedAvgPrice", DecimalType(20, 8), False),  
        StructField("prevClosePrice", DecimalType(20, 8), False),  
        StructField("lastPrice", DecimalType(20, 8), False),  
        StructField("lastQty", DecimalType(20, 8), False),  
        StructField("bidPrice", DecimalType(20, 8), False),  
        StructField("bidQty", DecimalType(20, 8), False),  
        StructField("askPrice", DecimalType(20, 8), False),  
        StructField("askQty", DecimalType(20, 8), False),  
        StructField("openPrice", DecimalType(20, 8), False),  
        StructField("highPrice", DecimalType(20, 8), False),  
        StructField("lowPrice", DecimalType(20, 8), False),  
        StructField("volume", DecimalType(20, 8), False),  
        StructField("quoteVolume", DecimalType(20, 8), False),  
        StructField("openTime", LongType(), False),
        StructField("closeTime", LongType(), False),
        StructField("firstId", LongType(), False),
        StructField("lastId", LongType(), False),
        StructField("count", LongType(), False)
    ])

    df_parsed = df \
        .selectExpr("CAST(value AS STRING) as json_value") \
        .select(from_json(col("json_value"), schema).alias("data")) \
        .select("data.*")

    df_parsed = df_parsed.withColumn(
        "trend",
        when(col("priceChange") > 0, True).otherwise(False)
    )

    df_parsed = df_parsed.drop('openTime')

    df_parsed = df_parsed.withColumn(
        "closeTime",
        from_unixtime(col("closeTime") / 1000).cast("timestamp")
    )

    write_to_postgres(df_parsed)

def create_topic(topic_name, kafka_server="kafka:9093"):
    admin_client = KafkaAdminClient(bootstrap_servers=kafka_server)
    topic = NewTopic(name=topic_name, num_partitions=1, replication_factor=1)
    admin_client.create_topics([topic])
    admin_client.close()

def delete_topic(topic_name, kafka_server="kafka:9093"):
    admin_client = KafkaAdminClient(bootstrap_servers=kafka_server)
    admin_client.delete_topics([topic_name])
    admin_client.close()

def write_to_postgres(dataFrame):
    hook = PostgresHook(postgres_conn_id='postgres_localhost')

    rows = [tuple(row) for row in dataFrame.collect()]

    columns = ['symbol', 'price_change', 'price_change_percent',
               'weighted_avg_price', 'prev_close_price', 'last_price',
               'last_qty', 'bid_price', 'bid_qty', 'ask_price',
               'ask_qty', 'open_price', 'high_price', 'low_price',
               'volume', 'quote_volume', 'close_time', 'first_id',
               'last_id', 'count', 'trend']

    hook.insert_rows(
        table="crypto_data",
        rows=rows,
        target_fields=columns,
        commit_every=1000
    )


default_args = {
    'owner': 'andrewsis',
    'retries': 5,
    'retry_delay': timedelta(seconds=10),
}

with DAG(
    dag_id='save_to_minio',
    default_args=default_args,
    start_date=datetime(2025, 1, 25),
    schedule_interval='@daily',
    catchup=False
) as dag:
    create_topic_task = PythonOperator(
        task_id="create_topic",
        python_callable=create_topic,
        op_kwargs={"topic_name": "crypto_topic_{{ ts_nodash }}"},
    )

    delete_topic_task = PythonOperator(
        task_id="delete_topic",
        python_callable=delete_topic,
        op_kwargs={"topic_name": "crypto_topic_{{ ts_nodash }}"},
    )

    dag_save_to_minio = PythonOperator(
        task_id='save_to_minio',
        python_callable=save_to_minio,
        provide_context=True
    )
    dag_kafka_producer = PythonOperator(
        task_id='kafka_producer',
        python_callable=send_to_kafka,
        provide_context=True,
        op_kwargs = {"topic_name": "crypto_topic_{{ ts_nodash }}"}
    )
    dag_spark_consumer = PythonOperator(
        task_id='spark_consumer',
        python_callable=spark_consumer,
        op_kwargs={"topic_name": "crypto_topic_{{ ts_nodash }}"}
    )

    dag_save_to_minio >> create_topic_task >> dag_kafka_producer >> dag_spark_consumer >> delete_topic_task