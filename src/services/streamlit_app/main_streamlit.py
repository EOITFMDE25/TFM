# src/services/streamlit_app/main_streamlit.py
import streamlit as st
import pandas as pd
import glob
import os

st.title("Dashboard de Tickets de Supermercado")

# Ruta donde Spark escribe los archivos Parquet
parquet_path = "/app/data/processed/*.parquet"

# Lee todos los archivos Parquet
parquet_files = glob.glob(parquet_path)
if not parquet_files:
    st.write("Aún no hay datos procesados en Parquet.")
else:
    # Combina todos los archivos Parquet en un solo DataFrame
    df_list = [pd.read_parquet(file) for file in parquet_files]
    if df_list:
        df = pd.concat(df_list, ignore_index=True)
        st.write("Datos procesados:")
        st.dataframe(df)
    else:
        st.write("No se pudieron leer los datos de los archivos Parquet.")