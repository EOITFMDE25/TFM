# src/services/streamlit_app/main_streamlit.py
import streamlit as st
import pandas as pd
import glob
import os


def main():
    st.title("Dashboard de Tickets de Supermercado")
    parquet_path = os.getenv("PLATA_PATH", "/app/data/plata")  # Ajusta si usas Oro

    parquet_files = glob.glob(f"{parquet_path}/*.parquet")
    if not parquet_files:
        st.warning("Aún no hay datos procesados en Parquet.")
        return

    # Cargamos la data en un DF
    df = pd.read_parquet(parquet_files[-1])  # Lee el más reciente o concatena todos

    st.subheader("Vista de los últimos registros OCR")
    st.dataframe(df.head(20))

    if "total" in df.columns:
        total_gasto = df["total"].sum()
        st.metric("Gasto total estimado (suma de total)", f"{total_gasto:.2f} EUR")

    # Aquí puedes meter gráficos, groupby por 'supermarket', etc.
    # df.groupby('supermarket').agg(...) => st.bar_chart(...)


if __name__ == "__main__":
    main()
