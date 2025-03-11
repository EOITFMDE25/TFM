# src/spark_jobs/process_tickets.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, expr, to_json, struct
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, ArrayType

def main():
    spark = SparkSession.builder \
        .appName("ProcessTickets") \
        .getOrCreate()

    # Esquema inicial, todo como StringType
    schema = StructType([
        StructField("supermarket", StringType(), True),
        StructField("date", StringType(), True),
        StructField("time", StringType(), True),
        StructField("location", StringType(), True),
        StructField("items", ArrayType(StructType([
            StructField("name", StringType(), True),
            StructField("quantity", StringType(), True),
            StructField("unit_price", StringType(), True),
            StructField("total_price", StringType(), True),
            StructField("discount", StringType(), True),
            StructField("original_price", StringType(), True)
        ]), True), True),
        StructField("subtotal", StringType(), True),
        StructField("taxes", ArrayType(StructType([
            StructField("name", StringType(), True),
            StructField("amount", StringType(), True)
        ]), True), True),
        StructField("total", StringType(), True),
        StructField("payment_method", StringType(), True),
        StructField("currency", StringType(), True)
    ])

    # Lee el stream de Kafka
    df_raw = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "tickets_ocr") \
        .option("startingOffsets", "earliest") \
        .load()

    # Convierte el valor binario de Kafka a string y luego a JSON
    df_json = df_raw.select(
        from_json(col("value").cast("string"), schema).alias("data")
    )

    # Selecciona los campos del JSON y aplica casting
    df_processed = df_json.select(
        "data.supermarket",
        "data.date",
        "data.time",
        "data.location",
        to_json(struct("data.items")).alias("items"),  # Serializa items como JSON
        expr("cast(data.subtotal as double)").alias("subtotal"),
        to_json(struct("data.taxes")).alias("taxes"),  # Serializa taxes como JSON
        expr("cast(data.total as double)").alias("total"),
        "data.payment_method",
        "data.currency"
    )
    # Escribe los datos procesados en formato Parquet
    query = df_processed.writeStream \
        .outputMode("append") \
        .format("parquet") \
        .option("path", "/app/data/processed") \
        .option("checkpointLocation", "/app/data/checkpoint") \
        .trigger(processingTime="5 seconds") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()