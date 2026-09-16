"""Aplicacao FastAPI do painel de clima."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import dataset
from app.config import cors_origins
from app.routers import conta, health, noticias, trends, weather


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carrega o dataset de cidades antes de aceitar requisicoes.

    No startup, e nao sob demanda: sao ~85 ms de parse que, pagos aqui, nao
    aparecem como latencia extra na primeira consulta de vizinhas.
    """
    dataset.carregar_no_startup()
    yield


app = FastAPI(title="Weather Dashboard API", lifespan=lifespan)

#: A sessao viaja em cookie, e cookie so atravessa origem com
#: `allow_credentials=True` — que por sua vez **proibe** `allow_origins=["*"]`.
#: Nao ha curinga nenhum aqui por isso, e nao por rigor: com o curinga o
#: browser recusa a resposta inteira, e o erro fala de CORS em vez de falar da
#: combinacao que o causou.
#:
#: Os metodos deixam de ser so leitura porque cadastro e entrada sao `POST`, e
#: remover local e `DELETE`. Em desenvolvimento nada disso aparece: o proxy do
#: Vite faz o browser ver uma origem so. Ver ADR 0005.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(conta.router)
app.include_router(weather.router)
app.include_router(trends.router)
app.include_router(noticias.router)
