import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import pandas as pd
import glob
import json


title = "Proyecto: MVP Análisis de Tickets de Supermercado"
app = FastAPI(
    version="1.0.0",
    title=title
    )


@app.get("/tickets")
def get_tickets():
    parquet_files = glob.glob("/app/data/plata/*.parquet")
    if not parquet_files:
        return {"message": "No hay datos en la capa Plata"}
    all_data = []
    for parquet_file in parquet_files:
        df = pd.read_parquet(parquet_file)
        if df.empty:
            continue
        if 'items' in df.columns:
            df['items'] = df['items'].apply(json.loads)
        if 'taxes' in df.columns:
            df['taxes'] = df['taxes'].apply(json.loads)
        all_data.extend(df.to_dict(orient="records"))
    return all_data

@app.get("/supermarket-category")
def get_supermarket_category():
    parquet_files = glob.glob("/app/data/oro/*.parquet")
    if not parquet_files:
        return {"message": "No hay datos en la capa Oro"}
    all_data = []
    for parquet_file in parquet_files:
        df = pd.read_parquet(parquet_file)
        if df.empty:
            continue
        all_data.extend(df.to_dict(orient="records"))
    return all_data

@app.get("/", include_in_schema=False)
def redirigir():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)