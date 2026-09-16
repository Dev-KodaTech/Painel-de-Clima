"""Monta o payload do painel a partir das respostas da API externa."""

import asyncio

import httpx

from app import dataset
from app.models import (
    UNIDADES_PADRAO,
    AlertaOficial,
    Cidade,
    CidadeEscolhida,
    CondicaoPrevista,
    CondicoesResponse,
    Current,
    DailyPoint,
    DiaDoHorizonte,
    HorizonteResponse,
    HourlyPoint,
    Location,
    Nearby,
    PainelSlot,
    StatusDosAlertas,
    Sun,
    Units,
    WeatherResponse,
    atribuicao,
)
from app.services import condicoes, inmet, open_meteo, reverso, vizinhas
from app.services.geonames import CidadeLocal
from app.services.wmo import traduzir

#: O unico pais com cobertura de alerta oficial no app. Constante, e nao o
#: literal solto na comparacao, porque o dia em que houver um segundo
#: fornecedor a regra deixa de ser "e o Brasil?" e vira "quem cobre aqui?" —
#: e ha de haver um lugar so para mudar.
_CODIGO_DO_BRASIL = "BR"


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
    # As duas em paralelo: sao fornecedores diferentes e nenhuma depende da
    # outra, entao esperar uma para so entao pedir a outra somaria as
    # latencias — e a do INMET tem timeout de dez segundos.
    #
    # Falha do INMET nao pode derrubar o painel inteiro — so a condicao
    # prevista perde a chance de ser precedida por um alerta oficial. O painel
    # nao carrega o status: ele nao tem onde dizer "nao foi possivel
    # consultar" (sao dois cards de altura fixa, sem espaco para um terceiro
    # estado), e e a pagina Condicoes que declara os tres. Ver ADR 0008.
    atuais, (alertas, _) = await asyncio.gather(
        open_meteo.buscar_atual_de_varias(
            client,
            [(vizinha.latitude, vizinha.longitude) for vizinha, _ in selecionadas],
        ),
        _alertas_oficiais(cidade.latitude, cidade.longitude, cidade.country_code),
    )

    return _montar(previsao, cidade, _vizinhas(selecionadas, atuais), alertas)


async def montar_condicoes(
    client: httpx.AsyncClient, latitude: float, longitude: float, country_code: str
) -> CondicoesResponse:
    """A pagina Condicoes: alertas do INMET e um item por dia que dispara.

    `buscar_previsao` e cacheado por coordenada arredondada — a mesma chave
    que `/api/weather` populou. Uma cidade cujo painel ja abriu nao gera
    segunda chamada a API externa ao abrir esta pagina dentro do TTL.

    O INMET so e consultado quando `country_code` e `BR` — fora disso a
    secao de alertas declara "fora de cobertura", nunca "sem alertas" (ADR
    0008). Uma falha na consulta ao INMET nao derruba a resposta: as
    condicoes previstas continuam vindo, e o status avisa que a consulta
    falhou em vez de sugerir uma lista vazia de avisos.
    """
    # Em paralelo pela mesma razao do painel: dois fornecedores independentes,
    # e a soma das latencias seria gratuita.
    previsao, (alertas, status) = await asyncio.gather(
        open_meteo.buscar_previsao(client, latitude, longitude),
        _alertas_oficiais(latitude, longitude, country_code),
    )

    return CondicoesResponse(
        alertas=alertas,
        status_dos_alertas=status,
        condicoes=condicoes.derivar_por_dia(previsao["daily"]),
        attribution=atribuicao(com_inmet=bool(alertas)),
    )


async def montar_horizonte(
    client: httpx.AsyncClient, latitude: float, longitude: float
) -> HorizonteResponse:
    """Os dezesseis dias da pagina Calendario, com a fronteira ja declarada.

    Chamada propria e cache proprio: `buscar_horizonte` nao reaproveita a
    entrada de sete dias de `buscar_previsao`, porque pede outro conjunto de
    variaveis. Abrir o painel e depois esta pagina custa duas chamadas externas,
    e e o correto — a alternativa seria a grade receber sete dias.
    """
    horizonte = await open_meteo.buscar_horizonte(client, latitude, longitude)

    return HorizonteResponse(
        dias=_dias_do_horizonte(horizonte["daily"]),
        # Pela funcao, e nao pela constante: o padrao que a pagina Noticias
        # estabeleceu. Sem INMET — esta pagina nao consulta alertas, e nomea-lo
        # creditaria fornecedor que nao forneceu nada.
        attribution=atribuicao(),
    )


def _dias_do_horizonte(daily: dict) -> list[DiaDoHorizonte]:
    """Os dezesseis dias, cada um declarando a que horizonte pertence.

    **O corte e feito aqui, e o payload carrega o resultado.** Do oitavo dia em
    diante o icone e a descricao nao sao montados: a fonte ja e outro modelo
    (ECMWF no lugar do ICON), e um ceu desenhado com a confianca do dia 2 sobre
    o dado do dia 14 e a afirmacao que o ADR 0010 existe para nao fazer.

    A probabilidade de precipitacao vai nos dezesseis: e o unico canal de
    incerteza gratuito, e quem decide onde exibi-la e a interface.
    """
    dias = []
    for indice, data in enumerate(daily["time"]):
        longo = indice >= open_meteo.PRIMEIRO_DIA_DO_HORIZONTE_LONGO
        codigo = daily["weather_code"][indice]
        # No horizonte longo os tres ficam `None` juntos: o codigo WMO e o que
        # produz icone e descricao, e envia-lo sozinho seria mandar a materia
        # prima do que se acabou de decidir nao exibir.
        description, icon = (None, None) if longo else traduzir(codigo, is_day=True)

        dias.append(
            DiaDoHorizonte(
                date=data,
                horizonte="longo" if longo else "curto",
                high=daily["temperature_2m_max"][indice],
                low=daily["temperature_2m_min"][indice],
                precipitation_mm=daily["precipitation_sum"][indice],
                precipitation_probability_max=daily["precipitation_probability_max"][
                    indice
                ],
                weather_code=None if longo else codigo,
                description=description,
                icon=icon,
            )
        )
    return dias


async def _alertas_oficiais(
    latitude: float, longitude: float, country_code: str
) -> tuple[list[AlertaOficial], StatusDosAlertas]:
    """Os alertas do INMET e o estado da consulta, para uma coordenada.

    Os dois juntos porque so fazem sentido juntos: lista vazia nao diz nada
    sem o status que explica *por que* esta vazia (ADR 0008).

    `.upper()` no codigo do pais pela mesma razao que o `repositorio.py` o
    aplica: o parametro chega de uma URL, e `br` minusculo cairia em "fora de
    cobertura" para uma coordenada brasileira — a falsa afirmacao de
    seguranca que o ADR existe para impedir, so que disparada pela caixa em
    vez da geografia.
    """
    if country_code.upper() != _CODIGO_DO_BRASIL:
        return [], "fora_de_cobertura"

    try:
        return await inmet.alertas_da_coordenada(latitude, longitude), "ok"
    except inmet.InmetIndisponivel:
        return [], "indisponivel"


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
    previsao: dict,
    cidade: CidadeEscolhida,
    nearby: list[Nearby],
    alertas: list[AlertaOficial],
) -> WeatherResponse:
    current = previsao["current"]
    daily = previsao["daily"]

    # `is_day` vem como inteiro (0/1), nao booleano.
    is_day = bool(current["is_day"])
    description, icon = traduzir(current["weather_code"], is_day)

    # O dia corrente e o primeiro do bloco diario, nao a data de `current`:
    # ambos coincidem, mas o bloco diario e quem define a semana exibida.
    hoje = daily["time"][0]

    # Alerta oficial tem precedencia sobre condicao prevista nos dois slots
    # (ADR 0007): entra primeiro, e so o espaco que sobra vai para o dedup por
    # categoria de `derivar()`. O painel continua com dois cards no total — o
    # teto e do layout, nao mudou.
    slots = _slots_do_painel(alertas, condicoes.derivar(daily))

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
        condicoes=slots,
        nearby=nearby,
        units=Units(**UNIDADES_PADRAO),
        # Credita o INMET pelo que o painel de fato **exibe**, nao pelo que a
        # consulta devolveu: com dois alertas ativos o segundo nao cabe nos
        # slots, e um alerta que ficou de fora nao e fonte de nada aqui.
        attribution=atribuicao(
            com_inmet=any(isinstance(slot, AlertaOficial) for slot in slots)
        ),
    )


def _slots_do_painel(
    alertas: list[AlertaOficial], previstas: list[CondicaoPrevista]
) -> list[PainelSlot]:
    """Os dois slots do card de condicoes, com alerta oficial na frente.

    O painel nao mostra alerta e condicao prevista do mesmo total livremente
    somados — o teto de dois cards e do layout (`condicoes.MAXIMO_DE_CARDS`),
    e alerta entra primeiro nos slots que existem. Com dois alertas ativos, as
    condicoes previstas nao aparecem no painel; a pagina Condicoes continua
    mostrando as duas listas completas e separadas.
    """
    slots: list[PainelSlot] = [*alertas, *previstas]
    return slots[: condicoes.MAXIMO_DE_CARDS]
