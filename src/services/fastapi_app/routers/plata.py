from fastapi import status, HTTPException, APIRouter
import pandas as pd
import glob
import json

from fastapi_app.models import Ticket, HTTPExceptionModel


router = APIRouter(tags=["Capa Plata"], prefix="/silver")

@router.get("/mytickets",  summary="Devuelve una lista con los tickets introducidos en formato json",
            responses={
                status.HTTP_200_OK: {"description": "OK", "model": list[Ticket]},
                status.HTTP_204_NO_CONTENT: {"descripction": "No content"}
            },)
def get_mytickets():
    parquet_files = glob.glob("/app/data/plata/*.parquet")
    if not parquet_files:
        return HTTPExceptionModel(detail="No hay datos en la capa Plata")
    all_data = []
    try:
        for parquet_file in parquet_files:
            df = pd.read_parquet(parquet_file)
            if df.empty:
                continue
            if 'items' in df.columns:
                df['items'] = df['items'].apply(json.loads)
            if 'taxes' in df.columns:
                df['taxes'] = df['taxes'].apply(json.loads)
            all_data.extend(df.to_dict(orient="records"))
        if len(all_data) < 1:
            return HTTPException(status_code=204, detail="No content")
        else:
            return all_data
    except Exception:
        raise HTTPException(status_code=500, detail="Algo ha ido mal.")