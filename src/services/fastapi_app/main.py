from fastapi import FastAPI
import pandas as pd
import glob

app = FastAPI()

@app.get("/tickets")
def get_tickets():
    parquet_files = glob.glob("/app/data/oro/*.parquet")
    if not parquet_files:
        return {"message": "No hay datos en la capa Oro"}
    df_oro = pd.read_parquet(parquet_files[0])
    return df_oro.to_dict(orient="records")
