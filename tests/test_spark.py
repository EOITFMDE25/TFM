import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, sum, count, to_json, struct
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, ArrayType
from src.spark_jobs.process_tickets import procesar_batch

@pytest.fixture(scope="session")
def spark():
    """Configura una sesión de Spark para pruebas."""
    return SparkSession.builder.master("local").appName("test").getOrCreate()


def test_spark_session(spark):
    """Verifica que la sesión de Spark se crea correctamente."""
    assert spark is not None
    assert isinstance(spark, SparkSession)


def test_process_tickets_transformation(spark):
    """Prueba la transformación de `process_tickets.py`."""
    schema = StructType([
        StructField("supermarket", StringType(), True),
        StructField("date", StringType(), True),
        StructField("time", StringType(), True),
        StructField("location", StringType(), True),
        StructField("items", ArrayType(StructType([
            StructField("name", StringType(), True),
            StructField("category", StringType(), True),
            StructField("total_price", StringType(), True)
        ])), True),
        StructField("total", StringType(), True)
    ])

    data = [("Super1", "2024-03-18", "12:30", "Madrid", 
             [{"name": "Apple", "category": "Fruits", "total_price": "2.5"},
              {"name": "Banana", "category": "Fruits", "total_price": "1.0"}], "3.5")]
    
    df = spark.createDataFrame(data, schema)
    
    # Simular batch ID para pruebas
    batch_id = 1
    procesar_batch(df, batch_id)
    
    # Leer los datos generados en /app/data/oro
    df_result = spark.read.parquet("/app/data/oro")
    result = df_result.collect()
    
    assert len(result) > 0
    assert result[0]["supermarket"] == "Super1"
    assert result[0]["total_spent"] == 3.5
    assert result[0]["num_items"] == 2