import streamlit as st
import pandas as pd
import glob
import json
import os
from io import BytesIO
import google.generativeai as genai
from src.ocr.call_ocr import ocr_image, process_image_file, categorize_product
from src.kafka_producer.send_to_kafka import KafkaSender
import plotly.express as px

# Configuración de la API key de Gemini
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    st.error("Error: La variable GEMINI_API_KEY no está configurada.")
    st.stop()
genai.configure(api_key=api_key)

# Configuración de Kafka
kafka_broker = os.getenv("KAFKA_BROKER", "kafka:9092")
kafka_topic = os.getenv("KAFKA_TOPIC", "tickets_ocr")

st.title("Dashboard de Tickets de Supermercado")

# --- Subida de Imágenes ---
uploaded_files = st.file_uploader("Sube tus tickets", type=["jpg", "jpeg", "png", "heic"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        bytes_data = uploaded_file.read()
        st.write("Procesando:", uploaded_file.name)

        # 1. Preprocesar la imagen
        temp_file_path = process_image_file(BytesIO(bytes_data))
        if not temp_file_path:
            st.error(f"No se pudo procesar la imagen: {uploaded_file.name}")
            continue

        # 2. Realizar OCR
        result = ocr_image(temp_file_path)
        if result:
            # 3. Categorizar cada producto individualmente
            if "items" in result:
                for item in result["items"]:
                    if "name" in item:
                        category = categorize_product(item["name"])
                        item["category"] = category
                    else:
                        item["category"] = "Otros"
            else:
                result["items"] = []

            # 4. Enviar a Kafka
            producer = KafkaSender(kafka_broker, kafka_topic)
            print(f"[DEBUG - Streamlit] Ticket procesado: {json.dumps(result, indent=2)}")
            producer.send_message(result)
            st.success(f"Ticket {uploaded_file.name} procesado y enviado a Kafka.")
        else:
            st.error(f"Error al procesar el ticket {uploaded_file.name}")

        os.remove(temp_file_path)

# --- Carga y Visualización de Datos (Parquet) ---
parquet_path = "/app/data/plata/*.parquet"
parquet_files = glob.glob(parquet_path)

if not parquet_files:
    st.write("Aún no hay datos procesados en Parquet.")
else:
    try:
        df_list = [pd.read_parquet(file) for file in parquet_files]
        if df_list:
            df = pd.concat(df_list, ignore_index=True)

            # --- Formateo de la Tabla ---
            def format_items(items_json):
                try:
                    items = json.loads(items_json)
                    return "\n".join([
                        f"- {item['name']} (x{item.get('quantity', 1)}): {item.get('total_price', 'N/A')} - {item.get('category', 'N/A')}"
                        for item in items
                    ])
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"[ERROR - Streamlit] Error al parsear items: {e}, items_json={items_json}")
                    return "Error al parsear"

            def format_taxes(taxes_json):
                try:
                    taxes = json.loads(taxes_json)
                    return "\n".join([f"- {tax['name']}: {tax.get('amount', 'N/A')}" for tax in taxes])
                except (json.JSONDecodeError, TypeError):
                    return "Error al parsear"

            df_display = df.copy()
            if 'items' in df_display.columns:
                df_display['items'] = df_display['items'].apply(format_items)
            if 'taxes' in df_display.columns:
                df_display['taxes'] = df_display['taxes'].apply(format_taxes)

            # --- Gráficos ---
            st.subheader("Análisis de Tickets")

            # Gráfico de Tickets por Mes
            st.write("### Tickets por Mes")
            df['date'] = pd.to_datetime(df['date'], errors='coerce')  # Convertir 'date' a datetime
            df['month'] = df['date'].dt.to_period('M')  # Extraer mes y año

            # Lista de meses únicos
            months = df['month'].dropna().unique().astype(str)
            months.sort()

            # Filtro de meses en Streamlit
            selected_months = st.multiselect(
                "Selecciona los meses para el gráfico de tickets por fecha:",
                months,
                default=months
            )

            # Filtrar el DataFrame por los meses seleccionados
            df_filtered = df[df['month'].astype(str).isin(selected_months)]

            # Contar tickets por mes
            ticket_counts = df_filtered['month'].value_counts().sort_index()

            # Crear gráfico de barras
            fig_tickets = px.bar(
                x=ticket_counts.index.astype(str),
                y=ticket_counts.values,
                labels={'x': 'Mes', 'y': 'Cantidad de Tickets'},
                title='Tickets por Mes'
            )
            st.plotly_chart(fig_tickets)

            # Gráfico de Gasto Total por Supermercado
            st.write("### Gasto Total por Supermercado")
            total_por_supermercado = df.groupby('supermarket')['total'].sum().reset_index()
            fig_total_supermercado = px.bar(
                total_por_supermercado,
                x='supermarket',
                y='total',
                labels={'supermarket': 'Supermercado', 'total': 'Total Gastado (EUR)'},
                title='Gasto Total por Supermercado'
            )
            st.plotly_chart(fig_total_supermercado)

            # Gráfico de Distribución de Categorías
            st.write("### Distribución de Categorías de Productos")
            all_categories = []
            for items_str in df['items']:
                try:
                    items = json.loads(items_str)
                except (json.JSONDecodeError, TypeError):
                    items = []
                for item in items:
                    if isinstance(item, dict) and 'category' in item:
                        all_categories.append(item['category'])

            if all_categories:
                cat_df = pd.DataFrame({'category': all_categories})
                cat_counts = cat_df['category'].value_counts().reset_index()
                cat_counts.columns = ['Categoría', 'Cantidad']
                fig_cat_pie = px.pie(
                    cat_counts,
                    names='Categoría',
                    values='Cantidad',
                    title='Distribución de Categorías de Productos'
                )
                st.plotly_chart(fig_cat_pie)
            else:
                st.write("No hay datos de categorías para graficar.")

            # Mostrar la tabla principal
            st.subheader("Datos procesados")
            df_display = df_display.dropna(axis=1, how='all')
            st.dataframe(df_display)

    except Exception as e:
        st.error(f"Error al leer o procesar los archivos Parquet: {e}")