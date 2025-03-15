# /src/spark_jobs/process_tickets.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, expr, to_json
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, ArrayType

def main():
    spark = SparkSession.builder \
        .appName("ProcessTickets") \
        .getOrCreate()

    # Esquema para los items, incluyendo la categoría
    item_schema = StructType([
        StructField("name", StringType(), True),
        StructField("quantity", StringType(), True),
        StructField("unit_price", StringType(), True),
        StructField("total_price", StringType(), True),
        StructField("discount", StringType(), True),
        StructField("original_price", StringType(), True),
        StructField("category", StringType(), True)  # Categoría incluida
    ])

    # Esquema completo del ticket
    schema = StructType([
        StructField("supermarket", StringType(), True),
        StructField("date", StringType(), True),
        StructField("time", StringType(), True),
        StructField("location", StringType(), True),
        StructField("items", ArrayType(item_schema), True),
        StructField("subtotal", StringType(), True),
        StructField("taxes", ArrayType(StructType([
            StructField("name", StringType(), True),
            StructField("amount", StringType(), True)
        ])), True),
        StructField("total", StringType(), True),
        StructField("payment_method", StringType(), True),
        StructField("currency", StringType(), True)
    ])

    # Lectura desde Kafka
    df_raw = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "tickets_ocr") \
        .option("startingOffsets", "earliest") \
        .load()

    df_json = df_raw.select(
        from_json(col("value").cast("string"), schema).alias("data")
    )

    # Procesamiento: mantener items y taxes como JSON
    df_processed = df_json.select(
        "data.supermarket",
        "data.date",
        "data.time",
        "data.location",
        to_json(col("data.items")).alias("items"),  # Convertir items a JSON
        expr("cast(data.subtotal as double)").alias("subtotal"),
        to_json(col("data.taxes")).alias("taxes"),  # Convertir taxes a JSON
        expr("cast(data.total as double)").alias("total"),
        "data.payment_method",
        "data.currency"
    )

    # Escritura en Parquet
    query = df_processed.writeStream \
        .outputMode("append") \
        .format("parquet") \
        .option("path", "/app/data/plata") \
        .option("checkpointLocation", "/app/data/checkpoint") \
        .trigger(processingTime="5 seconds") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()