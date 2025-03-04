import os
import glob
from src.ocr.call_ocr import ocr_image
from src.kafka_producer.send_to_kafka import KafkaSender

def main():
    # Directorio local en el contenedor donde están montadas las imágenes
    # (corresponde a ./data/raw_heic en el host)
    images_path = "/app/data/raw_heic/*.HEIC"

    # Config de Kafka (puedes usar variables de entorno)
    kafka_broker = os.getenv("KAFKA_BROKER", "kafka:9092")
    kafka_topic = os.getenv("KAFKA_TOPIC", "tickets_ocr")

    producer = KafkaSender(kafka_broker, kafka_topic)

    image_list = glob.glob(images_path)
    if not image_list:
        print(f"No se encontraron imágenes HEIC en: {images_path}")
        return

    for img_path in image_list:
        print(f"[OCR_PIPELINE] Procesando imagen: {img_path}")
        result = ocr_image(img_path)
        if result:
            # Enviar el JSON resultante a Kafka
            producer.send_message(result)
            print(f"[OCR_PIPELINE] JSON enviado a Kafka para: {img_path}")
        else:
            print(f"[OCR_PIPELINE] OCR falló o no devolvió JSON para: {img_path}")

if __name__ == "__main__":
    main()
