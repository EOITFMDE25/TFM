# /src/kafka_producer/send_to_kafka.py (MODIFICADO para depurar)
import json
from confluent_kafka import Producer, KafkaError

class KafkaSender:
    def __init__(self, broker_url: str, topic: str):
        self.producer = Producer({'bootstrap.servers': broker_url})
        self.topic = topic

    def send_message(self, data: dict):
        try:
            value = json.dumps(data)
            print(f"[DEBUG - KafkaSender] Enviando a Kafka: {value}")
            self.producer.produce(self.topic, key="ticket", value=value)
            self.producer.flush()
            print(f"[DEBUG - KafkaSender] Mensaje enviado a Kafka.")
        except KafkaError as e:
            print(f"[ERROR - KafkaSender] Error específico de Kafka: {e}")
        except Exception as e:
            print(f"[ERROR - KafkaSender] Error general enviando a Kafka: {e}")