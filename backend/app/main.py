"""Aplicacao FastAPI do painel de clima."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import dataset
from app.config import cors_origins
from app.routers import health, weather


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carrega o dataset de cidades antes de aceitar requisicoes.

    No startup, e nao sob demanda: sao ~85 ms de parse que, pagos aqui, nao
    aparecem como latencia extra na primeira consulta de vizinhas.
    """
    dataset.carregar_no_startup()
    yield


app = FastAPI(title="Weather Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(weather.router)
