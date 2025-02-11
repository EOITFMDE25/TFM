# src/pipeline/launch_pipeline.py

import os
import sys
import subprocess
from src.ingestion.image_ingestion import ImageIngestion
from src.ocr.call_ocr import ocr_image
from src.kafka_producer.send_to_kafka import KafkaSender

# O podrías tener imágenes locales en data/raw_heic y hacer OCR directamente antes de subir a Kafka.

def main():
    # 1. Levantar docker-compose (opcional, si no lo tienes ya levantado)
    #    Descomentar si lo quieres automático:
    # try:
    #     subprocess.run(["docker-compose", "-f", "docker/docker-compose.yml", "up", "-d"], check=True)
    # except subprocess.CalledProcessError as e:
    #     print("Error al levantar docker-compose:", e)
    #     sys.exit(1)

    # 2. Ejemplo: Tomar un par de imágenes locales que quieras procesar
    images_to_process = [
        "data/raw_heic/IMG_7833.HEIC",
        "data/raw_heic/TEST_01.HEIC"
    ]

    # 3. Instanciar un producer Kafka
    kafka_broker = os.getenv("KAFKA_BROKER", "localhost:9092")
    kafka_topic = os.getenv("KAFKA_TOPIC", "tickets_ocr")
    producer = KafkaSender(broker_url=kafka_broker, topic=kafka_topic)

    # 4. Si queremos, guardamos las imágenes en Mongo (Capa Bronce),
    #    usando ImageIngestion, para tener un historial.
    mongo_uri = os.getenv("MONGO_URI", "mongodb://root:rootpass@localhost:27017")
    ingestion = ImageIngestion(mongo_uri, db_name="tickets_db")

    file_ids = []
    for img_path in images_to_process:
        file_id = ingestion.save_image_to_mongo(img_path, meta={"source": "pipeline"})
        file_ids.append(file_id)
        print(f"Imagen {img_path} guardada en Mongo con file_id {file_id}")

    # 5. Realizar OCR sobre cada imagen y enviar el JSON resultante a Kafka
    for i, img_path in enumerate(images_to_process):
        result_json = ocr_image(img_path)
        if result_json is not None:
            # Aquí puedes añadir cualquier metadato adicional,
            # como la referencia al file_id para trazar la imagen en Mongo
            result_json["mongo_file_id"] = file_ids[i]

            # 6. Publicar en Kafka
            producer.send_message(result_json)
            print(f"Enviado a Kafka el resultado OCR de {img_path}")
        else:
            print(f"No se obtuvo OCR para {img_path}, se omite el envío a Kafka.")

    # 7. Spark en modo Streaming:
    #    Si ya está en ejecución dentro de su contenedor, no hacemos nada más.
    #    De lo contrario, podríamos ejecutar remotamente:
    # try:
    #     subprocess.run(["docker", "exec", "spark_container",
    #                     "spark-submit", "--master", "local[*]",
    #                     "/app/src/spark_jobs/process_tickets.py"],
    #                    check=True)
    # except subprocess.CalledProcessError as e:
    #     print("Error al lanzar Spark job:", e)

    print("¡Pipeline completado! Revisa la carpeta data/plata o data/oro para los Parquet generados.")

if __name__ == "__main__":
    main()
