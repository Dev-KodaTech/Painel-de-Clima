"""Cliente da API externa Open-Meteo.

Este modulo e o unico lugar que conhece o formato da API externa. Ele trata as
armadilhas de formato e devolve estruturas ja saneadas; o resto do backend nao
precisa saber que `results` pode sumir nem que `is_day` vem como inteiro.
"""

import httpx

from app import cache_do_processo
from app.services.cache import chave_de_coordenada

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

#: Quantas candidatas pedir na desambiguacao. O default da API e 10, e a
#: busca e fuzzy ("Springfield" tambem traz "Palmyra"), entao o frontend exibe
#: estado e pais para que a escolha seja informada.
CANDIDATAS_PADRAO = 10

TIMEOUT = httpx.Timeout(10.0)

class OpenMeteoIndisponivel(Exception):
    """A API externa falhou: rede, timeout ou status de erro.

    Existe para que a camada HTTP traduza a falha numa mensagem compreensivel
    em vez de vazar um erro de httpx ao usuario.
    """


async def buscar_cidades(
    client: httpx.AsyncClient, nome: str, count: int = CANDIDATAS_PADRAO
) -> list[dict]:
    """Resolve um nome em candidatas de cidade.

    **Armadilha da API**: quando nada e encontrado, a chave `results` *some* da
    resposta em vez de vir como lista vazia. Acessa-la direto levantaria
    excecao onde o correto e "cidade nao encontrada"; por isso o `.get`.

    Os nomes vem no idioma default da API (ingles), como no payload de
    referencia: "Berlin", "Germany". So a traducao do codigo WMO e nossa.
    """
    payload = await _get(
        client,
        GEOCODING_URL,
        params={
            "name": nome,
            "count": count,
            "format": "json",
        },
    )
    return payload.get("results", [])


#: Quantos dias de previsao pedir. Sete e o que o painel da semana exibe.
#:
#: O bloco `hourly` acompanha: pedir sete dias traz **168 horas**, das quais o
#: grafico usa so as 24 do dia corrente. Pedir um dia de horas e sete de dias
#: numa mesma chamada nao e possivel — a API aplica `forecast_days` aos dois
#: blocos —, e uma segunda chamada so para as horas custaria mais que os ~18 KB
#: que as 144 horas extras somam.
DIAS_DE_PREVISAO = 7

#: As variaveis diarias. `sunrise`/`sunset` alimentam o painel do sol e
#: `precipitation_sum` o de precipitacao, ambos por dia.
#:
#: `wind_gusts_10m_max` nao alimenta painel algum diretamente: existe so para
#: derivar a condicao severa de vento. E a unica variavel pedida que nao e
#: exibida como tal — a rajada aparece no texto do card, nunca numa coluna.
VARIAVEIS_DIARIAS = (
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "sunrise",
    "sunset",
    "precipitation_sum",
    "wind_gusts_10m_max",
)


async def buscar_previsao(
    client: httpx.AsyncClient, latitude: float, longitude: float
) -> dict:
    """Busca o tempo atual, a tendencia horaria e os sete dias de uma coordenada.

    `timezone=auto` faz a API resolver o fuso pela coordenada e devolver os
    timestamps ja em horario local da cidade.

    **Cacheada por coordenada arredondada**: e a chamada cara — 168 horas e
    sete dias de variaveis —, e a fonte so atualiza a cada ~15 minutos, entao
    repeti-la dentro do TTL devolveria os mesmos numeros gastando cota.
    """
    return await cache_do_processo.atual().obter(
        chave_de_coordenada("previsao", latitude, longitude),
        lambda: _get(
            client,
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,apparent_temperature,weather_code,is_day",
                "hourly": "temperature_2m",
                "daily": ",".join(VARIAVEIS_DIARIAS),
                "timezone": "auto",
                "forecast_days": DIAS_DE_PREVISAO,
            },
        ),
    )


#: As variaveis das vizinhas: **apenas** `current`, e dentro dele so o que a
#: tabela exibe. A API aplica as variaveis pedidas a *todas* as coordenadas da
#: requisicao, entao nao ha como pedir "tudo para a principal, so temperatura
#: para as vizinhas" numa chamada so.
#:
#: Dai serem **duas chamadas**, e nao uma. Medido: uma chamada com seis
#: coordenadas e todas as variaveis pesa 32.791 bytes; a principal completa
#: mais as vizinhas so com `current` pesa 7.417 — **77% menos banda**, ao custo
#: de 2 requisicoes de uma cota diaria de 10.000.
VARIAVEIS_VIZINHAS = ("temperature_2m", "weather_code", "is_day")


async def buscar_atual_de_varias(
    client: httpx.AsyncClient, coordenadas: list[tuple[float, float]]
) -> list[dict]:
    """O tempo agora de varias coordenadas, numa unica requisicao.

    A Open-Meteo aceita **multiplas coordenadas** (`latitude=a,b,c`) e devolve
    um array **na ordem de entrada** — e a ordem que casa cada resposta com a
    sua cidade, porque a resposta nao repete o nome de nada.

    **Armadilha de formato**: com uma unica coordenada a API devolve um objeto,
    nao uma lista de um. Aqui o retorno e sempre lista, para que o chamador nao
    tenha de distinguir os dois casos.

    Lista vazia nao vira requisicao: uma chamada sem coordenada seria `400`.

    **Cacheada pelo conjunto inteiro**, nao por cidade: a requisicao e uma so
    para todas as coordenadas, e a resposta so faz sentido inteira, casada
    posicionalmente com o pedido. Como as vizinhas de uma cidade sao sempre as
    mesmas — a selecao e deterministica sobre um dataset fixo —, a chave do
    conjunto repete tal qual na segunda consulta a mesma cidade.
    """
    if not coordenadas:
        return []

    async def buscar() -> list[dict]:
        payload = await _get(
            client,
            FORECAST_URL,
            params={
                "latitude": ",".join(str(lat) for lat, _ in coordenadas),
                "longitude": ",".join(str(lon) for _, lon in coordenadas),
                "current": ",".join(VARIAVEIS_VIZINHAS),
                "timezone": "auto",
                # Sem previsao: a tabela mostra so a temperatura de agora. O
                # default de sete dias viria como bloco diario que ninguem le.
                "forecast_days": 1,
            },
        )
        return payload if isinstance(payload, list) else [payload]

    chave = chave_de_coordenada(
        "atual", *[valor for par in coordenadas for valor in par]
    )
    return await cache_do_processo.atual().obter(chave, buscar)


async def _get(client: httpx.AsyncClient, url: str, params: dict) -> dict:
    """Faz a requisicao e converte qualquer falha em `OpenMeteoIndisponivel`."""
    try:
        response = await client.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as erro:
        raise OpenMeteoIndisponivel(str(erro)) from erro
