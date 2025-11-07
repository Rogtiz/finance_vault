from fastapi import FastAPI
from . import models
from .db import engine
from .api import router

# Создаем таблицы в БД при старте
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cards Vault API")

# Подключаем все эндпоинты из api.py
app.include_router(router, tags=["API"])

@app.get("/", tags=["Health"])
def read_root():
    return {"status": "ok"}