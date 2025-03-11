import streamlit as st
import pandas as pd
import glob
import json

st.title("Dashboard de Tickets de Supermercado")

# Ruta donde están los archivos Parquet procesados
parquet_path = "/app/data/processed/*.parquet"

# Leer los archivos Parquet
parquet_files = glob.glob(parquet_path)
if not parquet_files:
    st.write("Aún no hay datos procesados en Parquet.")
else:
    try:
        # Combinar todos los archivos Parquet en un DataFrame
        df_list = [pd.read_parquet(file) for file in parquet_files]
        if df_list:
            df = pd.concat(df_list, ignore_index=True)

            # Función para formatear JSON o mostrar mensaje de error
            def format_json(data):
                try:
                    if isinstance(data, str):
                        return json.dumps(json.loads(data), indent=2, ensure_ascii=False)
                    elif isinstance(data, list) or isinstance(data, dict):
                        return json.dumps(data, indent=2, ensure_ascii=False)
                    else:
                         return "Dato no parseable"
                except (json.JSONDecodeError, TypeError):
                    return "Error al parsear"

            # Aplicar la función a las columnas 'items' y 'taxes'
            df['items'] = df['items'].apply(format_json)
            df['taxes'] = df['taxes'].apply(format_json)
            
            #elimina columnas con todo "error al parsear" o "Dato no parseable"
            for col in ['items', 'taxes']:
                if all(df[col].isin(["Error al parsear", "Dato no parseable"])):
                    df.drop(columns=[col], inplace=True)

            # Mostrar la tabla principal
            st.write("Datos procesados:")
            st.dataframe(df)

        else:
            st.error("No se encontraron datos en los archivos Parquet.")
    except Exception as e:
        st.error(f"Error al leer los archivos Parquet: {e}")