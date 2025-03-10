# src/ocr/ocr_pipeline.py
import os
import glob
import json
from src.kafka_producer.send_to_kafka import KafkaSender
from src.ocr.call_ocr import ocr_image

def main():
    images_path = "/app/data/raw_heic/*.HEIC"
    kafka_broker = os.getenv("KAFKA_BROKER", "kafka:9092")
    kafka_topic = os.getenv("KAFKA_TOPIC", "tickets_ocr")

    print(f"[OCR_PIPELINE] KAFKA_BROKER: {kafka_broker}")
    print(f"[OCR_PIPELINE] KAFKA_TOPIC: {kafka_topic}")
    print(f"[OCR_PIPELINE] Buscando imágenes en: {images_path}")

    producer = KafkaSender(kafka_broker, kafka_topic)

    image_list = glob.glob(images_path)
    print(f"[OCR_PIPELINE] Imágenes encontradas: {image_list}")
    if not image_list:
        print(f"[OCR_PIPELINE] No se encontraron imágenes HEIC en: {images_path}")
        return

    for img_path in image_list:
        print(f"[OCR_PIPELINE] Procesando imagen: {img_path}")
        result = ocr_image(img_path)
        if result:
            producer.send_message(result)
            print(f"[OCR_PIPELINE] JSON enviado a Kafka para: {img_path}")
        else:
            print(f"[OCR_PIPELINE] OCR falló o no devolvió JSON para: {img_path}")

if __name__ == "__main__":
    main()