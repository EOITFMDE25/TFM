#!/bin/bash
set -e

# Función para esperar a que Kafka esté listo
wait_for_kafka() {
    echo "Esperando a que Kafka esté listo en $KAFKA_BROKER..."
    host=$(echo $KAFKA_BROKER | cut -d: -f1)
    port=$(echo $KAFKA_BROKER | cut -d: -f2)
    until nc -z $host $port; do
        echo "Kafka no está listo, esperando 5 segundos..."
        sleep 5
    done
    echo "Kafka está listo!"
}

# Esperar a Kafka
wait_for_kafka

# Ejecutar el job de Spark usando --packages
exec spark-submit \
    --master local[*] \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.1 \
    /app/src/spark_jobs/process_tickets.py