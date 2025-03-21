import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.services.fastapi_app.routers import plata, oro



title = "Proyecto: MVP Análisis de Tickets de Supermercado"
app = FastAPI(
    version="1.0.0",
    title=title, 
    description="""API para consultar los datos procesados en el proyecto MVP Análisis de Tickets de Supermercado. 
    \n\n En este API se consumen datos tanto de la capa plata como 
    de la capa oro. En la capa plata tenemos los tickets procesados ya con un esquema apropiado
    mientras que en la capa oro se alamcenan los datos resultado de ciertas agregaciones con el fin de proporcionar
    información útil al negocio."""
    )

app.include_router(plata.router)
app.include_router(oro.router)



@app.get("/", include_in_schema=False)
def redirigir():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)