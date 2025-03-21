from fastapi import status, HTTPException, APIRouter
import pandas as pd
import glob


from fastapi_app.models import SupermarketCategoryResult, HTTPExceptionModel


router = APIRouter(tags=["Capa Oro"], prefix="/gold")


@router.get("/supermarket-category", summary="Devuelve un resumen de gasto por supermercado y categoría",
         responses={
                status.HTTP_200_OK: {"description": "OK", "model": list[SupermarketCategoryResult]},
                status.HTTP_204_NO_CONTENT: {"descripction": "No content"}
            })
def get_supermarket_category():
    parquet_files = glob.glob("/app/data/oro/*.parquet")
    if not parquet_files:
        return HTTPExceptionModel(detail="No hay datos en la capa Oro")
    all_data = []
    try:
        for parquet_file in parquet_files:
            df = pd.read_parquet(parquet_file)
            if df.empty:
                continue
            all_data.extend(df.to_dict(orient="records"))
        if len(all_data) < 1:
            return HTTPException(status_code=204, detail="No content")
        else:
            return all_data
    except Exception:
        raise HTTPException(status_code=500, detail="Algo ha ido mal.")