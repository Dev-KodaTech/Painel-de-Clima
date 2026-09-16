"""Monta o payload do painel a partir das respostas da API externa."""

import httpx

from app import dataset
from app.models import (
    ATRIBUICAO,
    UNIDADES_PADRAO,
    Cidade,
    CidadeEscolhida,
    Current,
    DailyPoint,
    HourlyPoint,
    Location,
    Nearby,
    Sun,
    Units,
    WeatherResponse,
)
from app.services import condicoes, open_meteo, reverso, vizinhas
from app.services.geonames import CidadeLocal
from app.services.wmo import traduzir


def para_cidade(bruto: dict) -> Cidade:
    """Converte uma candidata do geocoding no modelo.

    `admin1` e `population` faltam para lugares pequenos; o modelo os aceita
    como nulos e a interface omite o que nao veio.
    """
    return Cidade(
        id=bruto["id"],
        name=bruto["name"],
        country=bruto.get("country", ""),
        country_code=bruto.get("country_code", ""),
        admin1=bruto.get("admin1"),
        latitude=bruto["latitude"],
        longitude=bruto["longitude"],
        population=bruto.get("population"),
        timezone=bruto.get("timezone", "UTC"),
    )


async def buscar_candidatas(client: httpx.AsyncClient, q: str) -> list[Cidade]:
    brutas = await open_meteo.buscar_cidades(client, q)
    return [para_cidade(bruta) for bruta in brutas]


def cidade_na_coordenada(latitude: float, longitude: float) -> list[Cidade]:
    """A cidade de uma coordenada, como candidata — **no maximo uma**.

    Lista, e nao `Cidade | None`, porque a resposta e a mesma do modo texto: o
    frontend le `results` sem saber qual modo a produziu.

    Vazia quando a coordenada esta a mais de 50 km de qualquer cidade
    cadastrada, que e caminho normal e nao erro.

    `country` vem vazio e `admin1` nulo: o dump traz pais e estado apenas como
    codigos (`DE`, `16`), nao como nomes exibiveis. Nenhum dos dois e novidade
    para quem consome — a API externa ja omite `country` para territorios, e
    `admin1` falta para lugares pequenos. Quem identifica a cidade e
    `country_code`, sempre presente.
    """
    encontrada = reverso.mais_proxima(dataset.cidades(), latitude, longitude)
    if encontrada is None:
        return []

    cidade, _ = encontrada
    return [
        Cidade(
            id=cidade.id,
            name=cidade.name,
            country="",
            country_code=cidade.country_code,
            admin1=None,
            latitude=cidade.latitude,
            longitude=cidade.longitude,
            population=cidade.population,
            timezone=cidade.timezone,
        )
    ]


async def montar_painel(
    client: httpx.AsyncClient, cidade: CidadeEscolhida
) -> WeatherResponse:
    """Busca a previsao e monta o painel para uma cidade ja escolhida.

    A coordenada vem da propria cidade: passa-la em separado abriria a
    possibilidade de buscar o tempo de um lugar e rotula-lo com o nome de
    outro.
    """
    previsao = await open_meteo.buscar_previsao(
        client, cidade.latitude, cidade.longitude
    )

    # **Duas chamadas, nao uma**: as variaveis pedidas valem para todas as
    # coordenadas de uma requisicao, entao pedir o painel inteiro para as seis
    # cidades custaria 32.791 bytes contra os 7.417 destas duas.
    #
    # A selecao e local e roda antes: e ela que diz *quais* coordenadas pedir.
    selecionadas = vizinhas.selecionar(
        dataset.cidades(), cidade.latitude, cidade.longitude
    )
    atuais = await open_meteo.buscar_atual_de_varias(
        client, [(vizinha.latitude, vizinha.longitude) for vizinha, _ in selecionadas]
    )

    return _montar(previsao, cidade, _vizinhas(selecionadas, atuais))


def _horas_do_dia(hourly: dict, dia: str) -> list[HourlyPoint]:
    """As 24 horas de `dia`, recortadas do bloco horario de sete dias.

    Pedir sete dias de previsao traz 168 horas. O recorte e **por data**, nunca
    por posicao ou por "as proximas 24 a partir de agora": o design mostra o dia
    inteiro, de 00:00 a 23:00, com a hora atual marcada na curva. Uma janela
    rolante faria o eixo do grafico mudar a cada hora, e as 02:00 quase tudo
    seria futuro enquanto as 22:00 quase tudo seria passado.
    """
    return [
        HourlyPoint(time=time, temperature=temperatura)
        for time, temperatura in zip(hourly["time"], hourly["temperature_2m"])
        if time.startswith(dia)
    ]


def _dias(daily: dict) -> list[DailyPoint]:
    """Os sete dias da previsao, com o codigo WMO ja traduzido.

    O icone e sempre o diurno: um dia inteiro nao tem variante noturna, e
    herdar o `is_day` da leitura atual poria uma lua no card de amanha as tres
    da manha.
    """
    dias = []
    for indice, data in enumerate(daily["time"]):
        description, icon = traduzir(daily["weather_code"][indice], is_day=True)
        dias.append(
            DailyPoint(
                date=data,
                weather_code=daily["weather_code"][indice],
                description=description,
                icon=icon,
                high=daily["temperature_2m_max"][indice],
                low=daily["temperature_2m_min"][indice],
                precipitation_mm=daily["precipitation_sum"][indice],
            )
        )
    return dias


def _vizinhas(
    selecionadas: list[tuple[CidadeLocal, float]], atuais: list[dict]
) -> list[Nearby]:
    """Casa cada cidade selecionada com a sua leitura atual.

    A correspondencia e **posicional**: a API multi-coordenada devolve um array
    na ordem de entrada e nao repete o nome de nada, entao a i-esima resposta e
    da i-esima coordenada pedida. `zip` para no menor dos dois — uma resposta
    mais curta que o pedido rende menos linhas, nunca um par trocado, que
    exibiria a temperatura de uma cidade sob o nome de outra.
    """
    nearby = []
    for (cidade, distancia), atual in zip(selecionadas, atuais):
        current = atual["current"]
        description, icon = traduzir(current["weather_code"], bool(current["is_day"]))
        nearby.append(
            Nearby(
                name=cidade.name,
                country_code=cidade.country_code,
                # As mesmas que foram pedidas a API externa: no payload, a
                # coordenada passa a testemunhar o casamento posicional.
                latitude=cidade.latitude,
                longitude=cidade.longitude,
                # Arredondada ao km: a tabela exibe inteiros, e a precisao de
                # ponto flutuante nao significa nada numa distancia estimada
                # sobre a esfera.
                distance_km=round(distancia),
                temperature=current["temperature_2m"],
                weather_code=current["weather_code"],
                description=description,
                icon=icon,
            )
        )
    return nearby


def _montar(
    previsao: dict, cidade: CidadeEscolhida, nearby: list[Nearby]
) -> WeatherResponse:
    current = previsao["current"]
    daily = previsao["daily"]

    # `is_day` vem como inteiro (0/1), nao booleano.
    is_day = bool(current["is_day"])
    description, icon = traduzir(current["weather_code"], is_day)

    # O dia corrente e o primeiro do bloco diario, nao a data de `current`:
    # ambos coincidem, mas o bloco diario e quem define a semana exibida.
    hoje = daily["time"][0]

    return WeatherResponse(
        location=Location(
            name=cidade.name,
            country=cidade.country,
            country_code=cidade.country_code,
            admin1=cidade.admin1,
            # A coordenada da resposta, nao a pedida: a API externa arredonda
            # para a celula da grade que de fato usou.
            latitude=previsao["latitude"],
            longitude=previsao["longitude"],
            timezone=previsao["timezone"],
            utc_offset_seconds=previsao["utc_offset_seconds"],
        ),
        current=Current(
            # Viaja exatamente como veio: horario de parede da cidade, sem
            # sufixo de fuso. Reinterpreta-lo como UTC deslocaria tudo.
            observed_at=current["time"],
            temperature=current["temperature_2m"],
            apparent_temperature=current["apparent_temperature"],
            weather_code=current["weather_code"],
            description=description,
            icon=icon,
            is_day=is_day,
            # Do bloco diario: a API nao fornece maxima e minima em `current`.
            high=daily["temperature_2m_max"][0],
            low=daily["temperature_2m_min"][0],
        ),
        hourly=_horas_do_dia(previsao["hourly"], hoje),
        daily=_dias(daily),
        sun=Sun(
            # Do primeiro dia: o painel do sol e de hoje, nao da semana.
            sunrise=daily["sunrise"][0],
            sunset=daily["sunset"][0],
        ),
        # Derivadas da mesma semana que o painel exibe: nao ha fonte oficial de
        # alerta aqui, e a interface diz isso em cada card.
        condicoes=condicoes.derivar(daily),
        nearby=nearby,
        units=Units(**UNIDADES_PADRAO),
        attribution=ATRIBUICAO,
    )
