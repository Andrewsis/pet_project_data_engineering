from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, from_unixtime
from pyspark.sql.types import StructType, StructField, StringType, LongType, DecimalType
import logging

def spark_consumer():
    spark = SparkSession.builder \
        .appName("CryptoDataProcessor") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4") \
        .config("spark.jars", "/opt/postgresql-42.2.23.jar") \
        .getOrCreate()

    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9093") \
        .option("subscribe", 'crypto_topic') \
        .option("startingOffsets", 'latest') \
        .load()

    # df = df.selectExpr("CAST(value AS STRING)")

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

    column_mapping = {
        "symbol": "symbol",
        "priceChange": "price_change",
        "priceChangePercent": "price_change_percent",
        "weightedAvgPrice": "weighted_avg_price",
        "prevClosePrice": "prev_close_price",
        "lastPrice": "last_price",
        "lastQty": "last_qty",
        "bidPrice": "bid_price",
        "bidQty": "bid_qty",
        "askPrice": "ask_price",
        "askQty": "ask_qty",
        "openPrice": "open_price",
        "highPrice": "high_price",
        "lowPrice": "low_price",
        "volume": "volume",
        "quoteVolume": "quote_volume",
        "closeTime": "close_time",
        "firstId": "first_id",
        "lastId": "last_id",
        "count": "count",
        "trend": "trend"
    }

    for old_col, new_col in column_mapping.items():
        df_parsed = df_parsed.withColumnRenamed(old_col, new_col)

    if df_parsed.isStreaming:
        logging.info("df_parsed является потоком")
    else:
        logging.info("df_parsed не является потоком")


    query = df_parsed.writeStream \
        .foreachBatch(save_to_postgresql) \
        .outputMode("append") \
        .start()

    query.awaitTermination()

def save_to_postgresql(batch_df, batch_id):
    logging.basicConfig(level=logging.DEBUG)

    jdbc_url = "jdbc:postgresql://postgres:5432/test"

    properties = {
        "user": "airflow",
        "password": "airflow",
        "driver": "org.postgresql.Driver"
    }

    if batch_df.isEmpty():
        logging.info(f"Batch {batch_id} пустой.")
    else:
        logging.info(f"Запись пакета {batch_id} с данными: {batch_df.head()} в PostgreSQL.")

    try:
        logging.info(f"Writing batch {batch_id} to PostgreSQL.")
        logging.info(f"Writing batch with data: {batch_df.head()} to PostgreSQL.")
        batch_df.write.jdbc(url=jdbc_url, table="crypto_data", mode="append", properties=properties)
        logging.info(f"Batch {batch_id} successfully written to PostgreSQL.")
    except Exception as e:
        logging.error(f"Failed to write batch {batch_id} to PostgreSQL: {e}")