import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, from_unixtime
from pyspark.sql.types import StructType, StructField, StringType, LongType, DecimalType
import logging

def parse_args():
    parser = argparse.ArgumentParser(description="Spark Streaming Consumer for Crypto Prices")
    parser.add_argument("--kafka-bootstrap-servers", required=True, help="Kafka bootstrap servers")
    parser.add_argument("--topic", required=True, help="Kafka topic name")
    parser.add_argument("--jdbc-url", required=True, help="PostgreSQL JDBC URL")
    parser.add_argument("--user", required=True, help="PostgreSQL username")
    parser.add_argument("--password", required=True, help="PostgreSQL password")
    return parser.parse_args()

def spark_consumer():
    args = parse_args()

    spark = SparkSession.builder \
        .appName("CryptoDataProcessor") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.4") \
        .config("spark.jars", "/opt/postgresql-42.2.23.jar") \
        .getOrCreate()

    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", args.kafka_bootstrap_servers) \
        .option("subscribe", args.topic) \
        .option("startingOffsets", 'latest') \
        .load()

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

    query = df_parsed.writeStream \
        .foreachBatch(lambda batch_df, batch_id: save_to_postgresql(batch_df, batch_id, args)) \
        .outputMode("append") \
        .start()

    query.awaitTermination()

def save_to_postgresql(batch_df, batch_id, args):
    logging.basicConfig(level=logging.DEBUG)

    jdbc_url = args.jdbc_url
    properties = {
        "user": args.user,
        "password": args.password,
        "driver": "org.postgresql.Driver"
    }

    try:
        logging.info(f"Writing batch {batch_id} to PostgreSQL.")
        batch_df.write.jdbc(url=jdbc_url, table="crypto_data", mode="append", properties=properties)
        logging.info(f"Batch {batch_id} successfully written to PostgreSQL.")
    except Exception as e:
        logging.error(f"Failed to write batch {batch_id} to PostgreSQL: {e}")


if __name__ == "__main__":
    spark_consumer()