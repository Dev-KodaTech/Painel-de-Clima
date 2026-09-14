"""Cliente da API externa Open-Meteo.

Este modulo e o unico lugar que conhece o formato da API externa. Ele trata as
armadilhas de formato e devolve estruturas ja saneadas; o resto do backend nao
precisa saber que `results` pode sumir nem que `is_day` vem como inteiro.
"""

import httpx

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
VARIAVEIS_DIARIAS = (
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "sunrise",
    "sunset",
    "precipitation_sum",
)


async def buscar_previsao(
    client: httpx.AsyncClient, latitude: float, longitude: float
) -> dict:
    """Busca o tempo atual, a tendencia horaria e os sete dias de uma coordenada.

    `timezone=auto` faz a API resolver o fuso pela coordenada e devolver os
    timestamps ja em horario local da cidade.
    """
    return await _get(
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
    )


async def _get(client: httpx.AsyncClient, url: str, params: dict) -> dict:
    """Faz a requisicao e converte qualquer falha em `OpenMeteoIndisponivel`."""
    try:
        response = await client.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as erro:
        raise OpenMeteoIndisponivel(str(erro)) from erro
