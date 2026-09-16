"""Endpoints do painel: candidatas de cidade e o painel de uma cidade."""

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.models import CidadeEscolhida, CidadesResponse, CondicoesResponse, WeatherResponse
from app.services import weather
from app.services.open_meteo import OpenMeteoIndisponivel

router = APIRouter(prefix="/api")

MSG_INDISPONIVEL = (
    "O servico de clima esta indisponivel no momento. Tente novamente em instantes."
)


MSG_MODO_AMBIGUO = (
    "Informe `q` (texto) ou `lat` e `lon` (coordenada), e nao ambos nem nenhum."
)

MSG_TERMO_VAZIO = "Informe um termo de busca em `q`."


@router.get("/cities", response_model=CidadesResponse)
async def cities(
    # **Sem `min_length`**: a validacao do Pydantic roda *antes* do corpo, e
    # `?q=&lat=..&lon=..` sairia como `422` por `q` vazio quando o erro real e
    # ter mandado os dois modos — que a spec define como `400`. Vazio e tratado
    # abaixo, junto da exclusao mutua.
    q: str | None = Query(default=None),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lon: float | None = Query(default=None, ge=-180, le=180),
) -> CidadesResponse:
    """Resolve texto **ou** coordenada em candidatas de cidade.

    Separado de `/weather` porque dispara a cada tecla digitada e nao pode
    arrastar a previsao junto.

    Os dois modos sao a mesma operacao — resolver algo em candidata — sobre
    dados diferentes, e por isso dividem a rota e o formato de resposta: o
    frontend reaproveita o tipo em vez de tratar duas formas de candidata.

    Sao **mutuamente exclusivos**, e ambos ou nenhum e `400`. Escolher um em
    silencio esconderia um bug do chamador: `lat` sem `lon` e tipicamente uma
    coordenada que se perdeu no caminho, e cair na busca por texto devolveria
    a cidade errada sem sinal algum.

    Nada encontrado devolve `200` com lista vazia, nao `404`: "nao encontrada"
    e um resultado normal da busca, e o frontend o exibe como mensagem. A
    armadilha da API externa (a chave `results` some quando nada casa) e
    tratada no cliente.
    """
    coordenada = None if lat is None or lon is None else (lat, lon)
    # `lat` sozinho nao e modo coordenada nem modo texto: cai aqui junto com
    # "nenhum dos dois", que e o que de fato e.
    if (q is None) == (coordenada is None):
        raise HTTPException(status_code=400, detail=MSG_MODO_AMBIGUO)

    if q is not None and not q.strip():
        raise HTTPException(status_code=400, detail=MSG_TERMO_VAZIO)

    if coordenada is not None:
        return CidadesResponse(results=weather.cidade_na_coordenada(*coordenada))

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


@router.get("/condicoes", response_model=CondicoesResponse)
async def condicoes_endpoint(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
) -> CondicoesResponse:
    """A pagina Condicoes: um item por dia que dispara, sem dedup nem teto.

    So a coordenada: a pagina nao exibe nome de cidade, que o cabecalho ja
    mostra do painel — o mesmo motivo de `/api/trends` nao pedi-lo.

    Reaproveita o cache de dez minutos de `buscar_previsao`: quando
    `/api/weather` ja populou a entrada para esta coordenada, abrir a pagina
    Condicoes nao gasta cota da API externa.
    """
    async with httpx.AsyncClient() as client:
        try:
            return await weather.montar_condicoes(client, latitude, longitude)
        except OpenMeteoIndisponivel as erro:
            raise HTTPException(status_code=503, detail=MSG_INDISPONIVEL) from erro
