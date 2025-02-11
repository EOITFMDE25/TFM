import json
from confluent_kafka import Producer

class KafkaSender:
    def __init__(self, broker_url: str, topic: str):
        self.producer = Producer({'bootstrap.servers': broker_url})
        self.topic = topic

    def send_message(self, data: dict):
        try:
            value = json.dumps(data)
            self.producer.produce(self.topic, key="ticket", value=value)
            self.producer.flush()
        except Exception as e:
            print(f"Error enviando mensaje a Kafka: {e}")
