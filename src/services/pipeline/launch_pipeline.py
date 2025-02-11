# src/pipeline/launch_pipeline.py

import os
import sys
import subprocess

# (Opcional) import de ingestion si quieres guardar en Mongo
from src.ingestion.image_ingestion import ImageIngestion

from src.ocr.call_ocr import ocr_image
from src.kafka_producer.send_to_kafka import KafkaSender

def main():
    # 1. (Opcional) Levantar docker-compose automático:
    # try:
    #     subprocess.run(["docker-compose", "-f", "docker/docker-compose.yml", "up", "-d"], check=True)
    # except subprocess.CalledProcessError as e:
    #     print("Error al levantar docker-compose:", e)
    #     sys.exit(1)

    # 2. Lista de imágenes locales
    images_to_process = [
        "data/raw_heic/IMG_7833.HEIC"
    ]

    # 3. Instanciar el productor de Kafka
    kafka_broker = os.getenv("KAFKA_BROKER", "localhost:9092")
    kafka_topic = os.getenv("KAFKA_TOPIC", "tickets_ocr")
    producer = KafkaSender(broker_url=kafka_broker, topic=kafka_topic)

    # 4. (Opcional) Subir las imágenes a Mongo (Capa Bronce).
    #    Si no quieres usar Mongo, comenta estas líneas. o cambialo a False
    use_mongo = True
    file_ids = []
    if use_mongo:
        mongo_uri = os.getenv("MONGO_URI", "mongodb://root:rootpass@localhost:27017")
        ingestion = ImageIngestion(mongo_uri, db_name="tickets_db")
        for img_path in images_to_process:
            file_id = ingestion.save_image_to_mongo(img_path, meta={"source": "pipeline"})
            file_ids.append(file_id)
            print(f"Imagen {img_path} guardada en Mongo con file_id {file_id}")
    else:
        file_ids = [None] * len(images_to_process)

    # 5. Realizar OCR y enviar a Kafka
    for i, img_path in enumerate(images_to_process):
        result_json = ocr_image(img_path)
        if result_json is not None:
            if use_mongo:
                # Añadir la referencia al file_id si se subió a Mongo
                result_json["mongo_file_id"] = file_ids[i]

            producer.send_message(result_json)
            print(f"OCR enviado a Kafka para {img_path}")
        else:
            print(f"Fallo OCR para {img_path}")

    # 6. (Opcional) Lanzar Spark en streaming si no está corriendo
    # try:
    #     subprocess.run(["docker", "exec", "spark_container",
    #                     "spark-submit", "--master", "local[*]",
    #                     "/app/src/spark_jobs/process_tickets.py"],
    #                    check=True)
    # except subprocess.CalledProcessError as e:
    #     print("Error lanzando Spark job:", e)

    print("Pipeline completado. Revisa data/plata para los Parquet.")

if __name__ == "__main__":
    main()
