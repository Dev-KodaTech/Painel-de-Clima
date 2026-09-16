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

#: O **segundo host** da Open-Meteo: a reanalise ERA5, de onde vem o historico
#: climatologico. Mesmo fornecedor e mesma licenca CC-BY 4.0 que a previsao,
#: entao a atribuicao ja existente continua valendo sem mudanca.
#:
#: Medido: o arquivo cobre ate o dia corrente, sem o lag de ~5 dias que se
#: esperaria de uma reanalise. Isso dispensa costurar o fim do arquivo com o
#: inicio da previsao — a janela atual sai dele inteira.
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

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


#: Quantos dias a pagina Calendario pede. **Dezesseis e o teto da API**: acima
#: disso ela recusa com `"Forecast days is invalid. Allowed range 0 to 16."`.
#:
#: Trinta dias nao foram recusados por limite tecnico — o ensemble de 35 dias
#: existe e e gratuito —, e sim porque nao tem `weather_code` e cai para ~50 km
#: de resolucao. Ver ADR 0010.
DIAS_DO_HORIZONTE = 16

#: **O primeiro dia do horizonte longo.** Indice no bloco diario, contado de
#: zero: o dia 8 da grade.
#:
#: Nao e preferencia de layout. E onde a Open-Meteo troca de modelo no
#: `best_match` — ICON (2-11 km) ate o dia 7, ECMWF IFS 0,25° (~25 km) do 8 em
#: diante —, e a emenda **aparece no dado**: para o mesmo dia, ICON dizia
#: 27,4 °C e ECMWF dizia 22,7 °C, 4,7 °C de desacordo medido na costura.
#: Desenhar os dezesseis como uma curva so exibiria esse degrau como mudanca de
#: tempo, que ele nao e.
#:
#: **O encadeamento nao e documentado pela Open-Meteo** — foi descoberto
#: comparando `best_match` com cada modelo, em setembro de 2026 (ADR 0010). Se
#: ela mudar a emenda, esta constante deixa de casar com a troca real e o app
#: desenha a fronteira no lugar errado **sem erro nenhum**, que e pior do que
#: falhar. Quem avisa e o teste de contrato marcado em `test_contract.py`.
PRIMEIRO_DIA_DO_HORIZONTE_LONGO = 7

#: As variaveis diarias do horizonte: as sete do painel mais a probabilidade de
#: precipitacao.
#:
#: `precipitation_probability_max` e o **unico canal de incerteza gratuito** do
#: endpoint padrao — nao existe `temperature_2m_max_spread` aqui, e obte-lo
#: exigiria o ensemble e o calculo sobre `_member01..31` a mao. E por isso que o
#: horizonte longo exibe a probabilidade no lugar do numero seco: e a unica
#: incerteza honesta disponivel sem trocar de API (ADR 0010).
VARIAVEIS_DO_HORIZONTE = (*VARIAVEIS_DIARIAS, "precipitation_probability_max")


async def buscar_horizonte(
    client: httpx.AsyncClient, latitude: float, longitude: float
) -> dict:
    """Os dezesseis dias de uma coordenada, para a pagina Calendario.

    Chamada **nova**, e nao `forecast_days=16` em `buscar_previsao`: aquela
    serve cinco paginas que nao leem o dia 12, e engorda-la faria todas pagarem
    pelos nove dias extras. Mesmo raciocinio do ADR 0003 e da separacao de
    `buscar_uv`.

    **Sem bloco `hourly`**: a pagina e diaria, e dezesseis dias de horas seriam
    384 pontos que ninguem le.

    Cacheada na familia de dez minutos com **prefixo proprio**: a chave nao pode
    colidir com `previsao:`, que guarda sete dias com outro conjunto de
    variaveis. Colidindo, a grade receberia sete dias em vez de dezesseis sem
    erro algum.
    """
    async def buscar() -> dict:
        payload = await _get(
            client,
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": ",".join(VARIAVEIS_DO_HORIZONTE),
                "timezone": "auto",
                "forecast_days": DIAS_DO_HORIZONTE,
            },
        )

        # **A janela curta e indisponibilidade, nao meia pagina.** Os valores da
        # borda podem faltar — e esperado, e o payload os carrega como nulos —,
        # mas as dezesseis *datas* nao: a grade e a fronteira do dia 8 contam
        # com elas. Sem esta guarda, uma resposta truncada viraria uma grade
        # menor, com a fronteira ainda no lugar certo e dias faltando sem
        # explicacao — o mesmo modo de falhar em silencio que a chave de cache
        # com prefixo proprio existe para impedir.
        if len(payload["daily"]["time"]) != DIAS_DO_HORIZONTE:
            raise OpenMeteoIndisponivel(
                f"a previsao devolveu {len(payload['daily']['time'])} dias, "
                f"e a grade precisa de {DIAS_DO_HORIZONTE}"
            )

        return payload

    return await cache_do_processo.atual().obter(
        chave_de_coordenada("horizonte", latitude, longitude), buscar
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


#: As variaveis diarias do arquivo, uma por serie ou metrica da pagina
#: Tendencia.
#:
#: **`uv_index_max` nao esta aqui, e a ausencia e deliberada.** A API a aceita e
#: responde `200`, mas devolve `null` para todos os dias, com `daily_units`
#: igual a `"undefined"` — a reanalise ERA5 nao tem UV. Pedi-la traria uma
#: coluna de nulos que um consumidor desatento plota como linha reta no zero. O
#: UV da pagina vem da previsao, num bloco proprio.
VARIAVEIS_DO_ARQUIVO = (
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "relative_humidity_2m_mean",
    "wind_speed_10m_max",
    "wind_direction_10m_dominant",
)


async def buscar_arquivo(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    inicio: str,
    fim: str,
    *,
    passado: bool,
) -> dict:
    """O historico climatologico de um intervalo de datas.

    **Um intervalo por chamada**: a API nao aceita dois, e pedir do ano passado
    ate hoje traria 365 dias para usar 60. A pagina faz duas chamadas — a janela
    atual e a mesma janela do ano anterior — e casa as duas series depois.

    `passado` escolhe a familia de cache, nao o que se pede: o dado do ano
    anterior nao muda mais, entao reconsulta-lo a cada dez minutos gasta cota
    para receber os mesmos numeros. O da janela atual termina no dia corrente,
    que ainda muda.
    """
    cache = (
        cache_do_processo.do_passado() if passado else cache_do_processo.atual()
    )
    # O intervalo entra na chave junto da coordenada, pelo mesmo motivo que a
    # coordenada entra: duas janelas da mesma cidade sao consultas diferentes.
    chave = f"{chave_de_coordenada('arquivo', latitude, longitude)}:{inicio}:{fim}"

    return await cache.obter(
        chave,
        lambda: _get(
            client,
            ARCHIVE_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "start_date": inicio,
                "end_date": fim,
                "daily": ",".join(VARIAVEIS_DO_ARQUIVO),
                "timezone": "auto",
            },
        ),
    )


#: As variaveis de UV pedidas a previsao: o dia corrente hora a hora para o
#: grafico, e a maxima dos sete dias para o numero de resumo.
VARIAVEIS_DE_UV_HORARIAS = ("uv_index",)
VARIAVEIS_DE_UV_DIARIAS = ("uv_index_max",)


async def buscar_uv(
    client: httpx.AsyncClient, latitude: float, longitude: float
) -> dict:
    """O indice UV previsto de uma coordenada.

    Chamada a parte da previsao do painel, e nao uma variavel a mais nela: o
    painel e lido pelas seis paginas e so a Tendencia exibe UV. Engordar a
    chamada compartilhada faria as outras cinco pagarem pelo bloco.

    Cacheada com o TTL curto: e previsao, e ela muda.
    """
    return await cache_do_processo.atual().obter(
        chave_de_coordenada("uv", latitude, longitude),
        lambda: _get(
            client,
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "hourly": ",".join(VARIAVEIS_DE_UV_HORARIAS),
                "daily": ",".join(VARIAVEIS_DE_UV_DIARIAS),
                "timezone": "auto",
                "forecast_days": DIAS_DE_PREVISAO,
            },
        ),
    )


async def _get(client: httpx.AsyncClient, url: str, params: dict) -> dict:
    """Faz a requisicao e converte qualquer falha em `OpenMeteoIndisponivel`."""
    try:
        response = await client.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as erro:
        raise OpenMeteoIndisponivel(str(erro)) from erro
