import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (StructType, StructField, StringType, FloatType,
                               ArrayType, IntegerType, MapType)

def main():
    spark = SparkSession.builder \
        .appName("ProcessTickets") \
        .getOrCreate()

    kafka_broker = os.getenv("KAFKA_BROKER", "kafka:9092")
    kafka_topic = os.getenv("KAFKA_TOPIC", "tickets_ocr")

    # 1) Leer en streaming desde Kafka
    df_raw = spark.readStream.format("kafka") \
        .option("kafka.bootstrap.servers", kafka_broker) \
        .option("subscribe", kafka_topic) \
        .option("startingOffsets", "latest") \
        .load()

    # 2) Convertir value de Kafka en string
    df_str = df_raw.selectExpr("CAST(value AS STRING) as json_str")

    # 3) Definir el esquema JSON acorde al prompt
    #    {
    #       "supermarket": "Name",
    #       "date": "YYYY-MM-DD",
    #       "time": "HH:MM:SS",
    #       "location": "Somewhere",
    #       "items": [
    #         {
    #           "name": "Product",
    #           "quantity": 1,
    #           "unit_price": 2.99,
    #           "total_price": 2.99,
    #           "discount": 0.50,
    #           "original_price": 3.49
    #         }
    #       ],
    #       "subtotal": 15.99,
    #       "taxes": [
    #         {"name": "VAT", "amount": 1.60}
    #       ],
    #       "total": 17.59,
    #       "payment_method": "Card",
    #       "currency": "EUR"
    #    }
    item_schema = StructType([
        StructField("name", StringType(), True),
        StructField("quantity", IntegerType(), True),
        StructField("unit_price", FloatType(), True),
        StructField("total_price", FloatType(), True),
        StructField("discount", FloatType(), True),
        StructField("original_price", FloatType(), True)
    ])

    tax_schema = StructType([
        StructField("name", StringType(), True),
        StructField("amount", FloatType(), True)
    ])

    receipt_schema = StructType([
        StructField("supermarket", StringType(), True),
        StructField("date", StringType(), True),
        StructField("time", StringType(), True),
        StructField("location", StringType(), True),
        StructField("items", ArrayType(item_schema), True),
        StructField("subtotal", FloatType(), True),
        StructField("taxes", ArrayType(tax_schema), True),
        StructField("total", FloatType(), True),
        StructField("payment_method", StringType(), True),
        StructField("currency", StringType(), True)
    ])

    df_parsed = df_str.select(from_json(col("json_str"), receipt_schema).alias("data")) \
                      .select("data.*")

    # 4) (Opcional) Transformaciones o limpiezas
    df_final = df_parsed

    # 5) Escritura en formato Parquet (data/plata). Se ejecuta cada 30s
    query = df_final.writeStream \
        .format("parquet") \
        .option("path", "/app/data/plata") \
        .option("checkpointLocation", "/app/data/plata/_checkpoints") \
        .trigger(processingTime="30 seconds") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
