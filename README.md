# Proyecto: MVP Análisis de Tickets de Supermercado
## 1. Descripción General
Este proyecto consiste en un pipeline local y dockerizado que:

- Ingesta imágenes de tickets de supermercado en formato HEIC/JPG/PNG.
- Aplica OCR usando la API de Google Generative AI (Gemini 2.0 Flash).
- Publica el JSON resultante en Kafka.
- Spark (en modo streaming) consume de Kafka y genera ficheros Parquet en la Capa Plata.
- (Opcional) Se almacenan las imágenes en MongoDB (GridFS) como “Capa Bronce” para backup.
- (Opcional) Se visualizan los datos en un dashboard con Streamlit.

## 2. Arquitectura General
La arquitectura se basa en varios contenedores Docker orquestados con docker-compose:

- Zookeeper y Kafka: Para la mensajería de datos.
- Spark: Lectura en streaming de Kafka, transformaciones y persistencia en Parquet.
- OCR: Contenedor Python que procesa las imágenes (OCR con Gemini) y envía el JSON a Kafka.
- Mongo (opcional): Guarda copias de las imágenes o metadatos si se desea.
- Streamlit (opcional): Interfaz web para visualizar los Parquet (estadísticas, dashboards).

## 3. Estructura de Directorios
```
├─ docker/
│  ├─ Dockerfile.spark       
│  ├─ Dockerfile.ocr         
│  ├─ Dockerfile.streamlit   
│  ├─ docker-compose.yml     
│  ├─ requirements_spark.txt
│  ├─ requirements_ocr.txt
│  ├─ requirements_streamlit.txt
│  ...
├─ src/
│  ├─ ingestion/
│  │  └─ image_ingestion.py
│  ├─ ocr/
│  │  ├─ call_ocr.py         
│  │  └─ ocr_pipeline.py
│  ├─ kafka_producer/
│  │  └─ send_to_kafka.py
│  ├─ spark_jobs/
│  │  └─ process_tickets.py
│  ├─ services/
│  │  └─ streamlit_app/
│  │     └─ main_streamlit.py
│  └─ pipeline/
│     └─ launch_pipeline.py
├─ data/
│  ├─ raw_heic/    # Imágenes HEIC
│  ├─ plata/       # Ficheros Parquet generados por Spark
│  └─ oro/         # (Opcional) Capa Oro si la implementas
├─ notebooks/
├─ .env            # Variables de entorno (opcional)
├─ README.md
└─ requirements.txt  # Requisitos globales (para dev local)

```
## 4. Requisitos de Instalación
- Docker >= 20.10
- docker-compose >= 1.29 (o Docker Compose V2)
- (Opcional) Python >= 3.8 si deseas lanzar scripts localmente.

## 5. Pasos de Ejecución
- Clona este repositorio:
```
git clone https://github.com/EOITFMDE25/TFM.git
```
- Construye las imágenes Docker:

```
docker-compose build
```

- Levanta los servicios en el orden deseado (ejemplo):

```
docker-compose up -d zookeeper
docker-compose up -d kafka
docker-compose up -d spark
docker-compose up -d ocr
docker-compose up -d streamlit
```
- Comprueba con docker-compose ps que estén “Up”.

- Coloca tus imágenes (.HEIC, .jpg, .png) en la carpeta data/raw_heic/.

- Tienes un script ocr_pipeline.py que se ejecuta automáticamente en el contenedor ocr, éste tomará esas imágenes y enviará JSON a Kafka.

- (Opcional) ejecuta manualmente tu script de OCR (por ejemplo launch_pipeline.py) en tu máquina local o en el contenedor.
Spark en streaming leerá de Kafka y escribirá ficheros Parquet en data/plata/.

- (Opcional) Accede a http://localhost:8501 para ver la aplicación de Streamlit con los datos.

## 6. Encendido y Apagado Manual
- Encender un servicio: 
```
- docker-compose up -d <servicio>
```
- Apagar un servicio: 

```
docker-compose stop <servicio>
```

- Ver logs en tiempo real: 
```docker-compose logs -f <servicio>
```
- Parar y borrar contenedores: 

 ```docker-compose down (ojo, elimina contenedores, no volúmenes si no usas -v)
 ```

## 7. Uso de MongoDB (Opcional)
Define 
```use_mongo = True ```
en launch_pipeline.py para subir las imágenes a GridFS como backup.
El contenedor mongo debe estar levantado.

Esto no afecta al pipeline esencial si decides no usarlo.

## 8. Personalización
- Puedes modificar process_tickets.py para aplicar transformaciones adicionales.
- Ajusta el esquema JSON según tus necesidades de OCR.
- Añade un segundo job para Capa Oro (por ejemplo, agregaciones finales) si lo requieres.