import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, coalesce, lit, to_timestamp, concat_ws
)
from pyspark.sql.types import (
    StructType, StructField, StringType, FloatType,
    ArrayType, IntegerType
)

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

    # 2) value de Kafka a string
    df_str = df_raw.selectExpr("CAST(value AS STRING) as json_str")

    # 3) Esquema JSON
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

    df_parsed = df_str.select(
        from_json(col("json_str"), receipt_schema).alias("data")
    ).select("data.*")

    # 4) Ejemplo de transformaciones/limpiezas
    df_final = (df_parsed
        # Rellenar discount nulo con 0 en la lista items
        # (nota: items es un array, necesitarías transformaciones más avanzadas si quisieras
        #  modificar cada elemento del array. Como ejemplo simple, hacemos un coalesce global:
        .withColumn("subtotal", coalesce(col("subtotal"), lit(0.0)))
        .withColumn("total", coalesce(col("total"), lit(0.0)))
        # Combinar date + time en un timestamp
        .withColumn(
            "timestamp_purchase",
            to_timestamp(concat_ws(" ", col("date"), col("time")), "yyyy-MM-dd HH:mm:ss")
        )
        .drop("date", "time")  # si ya no necesitas date y time por separado
    )

    # 5) Escritura en Parquet (cada 30s)
    query = df_final.writeStream \
        .format("parquet") \
        .option("path", "/app/data/plata") \
        .option("checkpointLocation", "/app/data/plata/_checkpoints") \
        .trigger(processingTime="30 seconds") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
