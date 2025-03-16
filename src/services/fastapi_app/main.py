import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import pandas as pd
import glob



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
    df_plata = pd.read_parquet(parquet_files[0])
    return df_plata.to_dict(orient="records")


@app.get("/", include_in_schema=False)
def redirigir():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)