# src/spark_jobs/process_tickets.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, ArrayType

def main():
    spark = SparkSession.builder \
        .appName("ProcessTickets") \
        .getOrCreate()

    # Define el esquema del JSON recibido desde Kafka
    schema = StructType([
        StructField("supermarket", StringType(), True),
        StructField("date", StringType(), True),
        StructField("time", StringType(), True),
        StructField("location", StringType(), True),
        StructField("items", ArrayType(StructType([
            StructField("name", StringType(), True),
            StructField("quantity", IntegerType(), True),
            StructField("unit_price", DoubleType(), True),
            StructField("total_price", DoubleType(), True),
            StructField("discount", DoubleType(), True),
            StructField("original_price", DoubleType(), True)
        ]), True), True),
        StructField("subtotal", DoubleType(), True),
        StructField("taxes", ArrayType(StructType([
            StructField("name", StringType(), True),
            StructField("amount", DoubleType(), True)
        ]), True), True),
        StructField("total", DoubleType(), True),
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

    # Selecciona los campos del JSON
    df_processed = df_json.select("data.*")

    # Escribe los datos procesados en formato Parquet
    query = df_processed.writeStream \
        .outputMode("append") \
        .format("parquet") \
        .option("path", "/app/data/processed") \
        .option("checkpointLocation", "/app/data/checkpoint") \
        .trigger(processingTime="10 seconds") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()