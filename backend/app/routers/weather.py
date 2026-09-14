"""Endpoints do painel: candidatas de cidade e o painel de uma cidade."""

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.models import CidadeEscolhida, CidadesResponse, WeatherResponse
from app.services import weather
from app.services.open_meteo import OpenMeteoIndisponivel

router = APIRouter(prefix="/api")

MSG_INDISPONIVEL = (
    "O servico de clima esta indisponivel no momento. Tente novamente em instantes."
)


@router.get("/cities", response_model=CidadesResponse)
async def cities(q: str = Query(min_length=1)) -> CidadesResponse:
    """Resolve texto em candidatas de cidade, para desambiguacao.

    Separado de `/weather` porque dispara a cada tecla digitada e nao pode
    arrastar a previsao junto.

    Nada encontrado devolve `200` com lista vazia, nao `404`: "nao encontrada"
    e um resultado normal da busca, e o frontend o exibe como mensagem. A
    armadilha da API externa (a chave `results` some quando nada casa) e
    tratada no cliente.
    """
    async with httpx.AsyncClient() as client:
        try:
            candidatas = await weather.buscar_candidatas(client, q)
        except OpenMeteoIndisponivel as erro:
            raise HTTPException(status_code=503, detail=MSG_INDISPONIVEL) from erro

    return CidadesResponse(results=candidatas)


@router.get("/weather", response_model=WeatherResponse)
async def weather_endpoint(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    name: str = Query(min_length=1),
    # **Sem `min_length`**: a chave `country` *some* da resposta do geocoding
    # para territorios e regioes especiais — Papeete (PF), Noumea (NC), Hong
    # Kong (HK), Macau (MO), Saint-Denis (RE) —, exatamente como `results` some
    # quando nada e encontrado. Exigi-la devolvia `422` e deixava essas cidades
    # sem painel algum. Quem confirma a cidade e `country_code`, sempre
    # presente; a interface ja omite o que vier vazio.
    country: str = "",
    country_code: str = Query(min_length=2, max_length=2),
    admin1: str | None = None,
) -> WeatherResponse:
    """Devolve o painel de uma cidade ja escolhida.

    A identidade da cidade (nome, pais, estado) vem de `/api/cities` e viaja
    de volta como parametro: assim o endpoint nao repete a geocodificacao
    apenas para descobrir como a cidade se chama. Nome e sigla do pais sao
    exigidos porque `location` existe para o usuario confirmar que e a cidade
    que pediu — em branco, ela nao confirmaria nada. O *nome* do pais nao,
    porque a API externa o omite para territorios.
    """
    cidade = CidadeEscolhida(
        name=name,
        country=country,
        country_code=country_code,
        admin1=admin1,
        latitude=latitude,
        longitude=longitude,
    )

    async with httpx.AsyncClient() as client:
        try:
            return await weather.montar_painel(client, cidade)
        except OpenMeteoIndisponivel as erro:
            raise HTTPException(status_code=503, detail=MSG_INDISPONIVEL) from erro
