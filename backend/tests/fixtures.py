"""Respostas da API externa gravadas do servico real.

Reproduzem o formato exato da Open-Meteo, incluindo as armadilhas: timestamps
sem sufixo de fuso, `is_day` como inteiro, `weather_code` como inteiro nu, e a
chave `results` ausente quando o geocoding nao acha nada.
"""

#: Busca que casa uma unica cidade.
GEOCODING_BERLIM = {
    "results": [
        {
            "id": 2950159,
            "name": "Berlin",
            "latitude": 52.52437,
            "longitude": 13.41053,
            "elevation": 74.0,
            "feature_code": "PPLC",
            "country_code": "DE",
            "timezone": "Europe/Berlin",
            "population": 3426354,
            "country": "Germany",
            "admin1": "Land Berlin",
        }
    ],
    "generationtime_ms": 0.6,
}

#: Nome ambiguo: varias candidatas, distinguiveis por estado e populacao. A
#: terceira e um resultado fuzzy — a busca por "Springfield" tambem traz
#: "Palmyra" —, o que torna estado e pais obrigatorios na interface.
GEOCODING_SPRINGFIELD = {
    "results": [
        {
            "id": 4409896,
            "name": "Springfield",
            "latitude": 37.21533,
            "longitude": -93.29824,
            "feature_code": "PPLA2",
            "country_code": "US",
            "timezone": "America/Chicago",
            "population": 170188,
            "country": "United States",
            "admin1": "Missouri",
        },
        {
            "id": 4250542,
            "name": "Springfield",
            "latitude": 39.80172,
            "longitude": -89.64371,
            "feature_code": "PPLA",
            "country_code": "US",
            "timezone": "America/Chicago",
            "population": 114394,
            "country": "United States",
            "admin1": "Illinois",
        },
        {
            "id": 4951788,
            "name": "Palmyra",
            "latitude": 42.10176,
            "longitude": -72.58981,
            "feature_code": "PPL",
            "country_code": "US",
            "timezone": "America/New_York",
            "country": "United States",
            "admin1": "Massachusetts",
        },
    ],
    "generationtime_ms": 0.7,
}

#: **A armadilha**: sem correspondencia, a chave `results` nao vem vazia — ela
#: simplesmente nao existe na resposta.
GEOCODING_VAZIO = {"generationtime_ms": 0.45}

#: **A mesma armadilha, noutro campo**: para territorios e regioes especiais, a
#: chave `country` some da candidata. Gravado do servico real; Noumea (NC),
#: Hong Kong (HK), Macau (MO) e Saint-Denis (RE) respondem igual.
#:
#: Papeete e tambem a cidade isolada da spec, entao e por esta resposta que
#: passa o caso que o painel de vizinhas existe para servir.
GEOCODING_PAPEETE = {
    "results": [
        {
            "id": 4033936,
            "name": "Papeete",
            "latitude": -17.5347,
            "longitude": -149.56844,
            "elevation": 11.0,
            "feature_code": "PPLC",
            "country_code": "PF",
            "timezone": "Pacific/Tahiti",
            "population": 26357,
            "admin1": "Iles du Vent",
        }
    ],
    "generationtime_ms": 0.6,
}

#: As 24 temperaturas do dia corrente, na resolucao real (uma por hora). O
#: grafico do painel exibe exatamente estas.
TEMPERATURAS_DIA_CORRENTE = [
    16.9, 16.7, 16.7, 16.5, 16.3, 15.8, 15.1, 14.3,
    13.7, 13.7, 14.0, 14.9, 15.6, 15.9, 16.5, 16.9,
    17.0, 17.2, 17.1, 16.8, 16.3, 15.7, 15.1, 14.5,
]

DIAS_DA_PREVISAO = [
    "2026-09-14",
    "2026-09-15",
    "2026-09-16",
    "2026-09-17",
    "2026-09-18",
    "2026-09-19",
    "2026-09-20",
]


def _horas_de_sete_dias() -> dict:
    """O bloco `hourly` como a API o devolve: 168 pontos, nao 24.

    Pedir sete dias de previsao traz sete dias de horas. So o primeiro dia
    interessa ao grafico, e as temperaturas dele sao as reais; os demais dias
    recebem valores deslocados apenas para que o recorte errado se revele —
    um recorte que pegasse 24 pontos da posicao errada mostraria outro dia.
    """
    horas = []
    temperaturas = []
    for indice, dia in enumerate(DIAS_DA_PREVISAO):
        for hora, temperatura in enumerate(TEMPERATURAS_DIA_CORRENTE):
            horas.append(f"{dia}T{hora:02d}:00")
            temperaturas.append(round(temperatura + indice, 1))
    return {"time": horas, "temperature_2m": temperaturas}


#: Previsao de Berlim. `utc_offset_seconds` nao-zero, timestamps sem sufixo.
#:
#: Reproduz a resposta real de sete dias: `hourly` traz **168 pontos** (7 x 24),
#: nao 24 — quem quiser o dia corrente precisa recorta-lo. O bloco comeca a
#: meia-noite do dia corrente, nunca "agora".
FORECAST_BERLIM = {
    "latitude": 52.52,
    "longitude": 13.419998,
    "generationtime_ms": 0.24,
    "utc_offset_seconds": 7200,
    "timezone": "Europe/Berlin",
    "timezone_abbreviation": "GMT+2",
    "elevation": 40.0,
    "current_units": {
        "time": "iso8601",
        "interval": "seconds",
        "temperature_2m": "°C",
        "apparent_temperature": "°C",
        "weather_code": "wmo code",
        "is_day": "",
    },
    "current": {
        "time": "2026-09-14T03:00",
        "interval": 900,
        "temperature_2m": 16.5,
        "apparent_temperature": 16.9,
        "weather_code": 3,
        "is_day": 0,
    },
    "hourly_units": {"time": "iso8601", "temperature_2m": "°C"},
    "hourly": _horas_de_sete_dias(),
    "daily_units": {
        "time": "iso8601",
        "weather_code": "wmo code",
        "temperature_2m_max": "°C",
        "temperature_2m_min": "°C",
        "sunrise": "iso8601",
        "sunset": "iso8601",
        "precipitation_sum": "mm",
    },
    "daily": {
        "time": [
            "2026-09-14",
            "2026-09-15",
            "2026-09-16",
            "2026-09-17",
            "2026-09-18",
            "2026-09-19",
            "2026-09-20",
        ],
        "weather_code": [3, 3, 95, 3, 3, 61, 3],
        "temperature_2m_max": [17.2, 24.7, 20.4, 19.2, 19.8, 16.8, 17.8],
        "temperature_2m_min": [13.7, 11.8, 15.0, 12.7, 13.6, 10.9, 13.3],
        "sunrise": [
            "2026-09-14T06:38",
            "2026-09-15T06:40",
            "2026-09-16T06:42",
            "2026-09-17T06:43",
            "2026-09-18T06:45",
            "2026-09-19T06:47",
            "2026-09-20T06:48",
        ],
        "sunset": [
            "2026-09-14T19:23",
            "2026-09-15T19:21",
            "2026-09-16T19:19",
            "2026-09-17T19:16",
            "2026-09-18T19:14",
            "2026-09-19T19:12",
            "2026-09-20T19:09",
        ],
        "precipitation_sum": [0.0, 0.0, 6.0, 0.0, 0.0, 2.4, 0.0],
    },
}


# ---------------------------------------------------------------------------
# Condicoes severas: seis cidades de perfis climaticos opostos.
#
# Blocos `daily` gravados do servico real numa unica chamada multi-coordenada
# (`../.scratch/weather-dashboard/probe-alertas.json`). Sao a amostra sobre a
# qual os limiares foram calibrados, e existem aqui para que a regra nao possa
# mudar em silencio: cada cidade cobre um caso que a regra tem de acertar.
#
# As datas de Miami foram deslocadas para a mesma semana das demais; so a
# posicao relativa dos dias importa, e uma semana comum torna os testes
# comparaveis.

#: Litoranea: vento >= 60 km/h em **cinco** dos sete dias. O caso que derrubou
#: a regra sem dedup — cinco cards identicos de vento.
DAILY_WELLINGTON = {
    "time": DIAS_DA_PREVISAO,
    "weather_code": [3, 3, 51, 81, 51, 51, 51],
    "wind_gusts_10m_max": [37.1, 69.5, 86.4, 76.3, 59.0, 79.6, 80.6],
    "precipitation_sum": [0.0, 0.0, 0.4, 14.5, 0.3, 0.4, 0.2],
    "temperature_2m_max": [14.2, 14.4, 14.1, 14.2, 12.2, 15.4, 13.7],
    "temperature_2m_min": [9.6, 10.5, 11.9, 9.6, 9.7, 7.5, 12.6],
}

#: Duas categorias no mesmo dia: vento de 86 km/h e chuva de 27,9 mm.
DAILY_REYKJAVIK = {
    "time": DIAS_DA_PREVISAO,
    "weather_code": [51, 3, 81, 53, 81, 55, 51],
    "wind_gusts_10m_max": [56.2, 44.3, 86.0, 29.5, 51.5, 46.8, 36.4],
    "precipitation_sum": [0.5, 0.0, 27.9, 2.9, 14.8, 10.4, 1.1],
    "temperature_2m_max": [11.5, 9.4, 11.6, 10.7, 9.8, 10.4, 9.8],
    "temperature_2m_min": [8.2, 6.7, 8.0, 8.6, 8.3, 7.5, 6.8],
}

#: Tempestade (95) sem vento nem chuva acima do limiar: a categoria sozinha.
DAILY_INNSBRUCK = {
    "time": DIAS_DA_PREVISAO,
    "weather_code": [81, 45, 95, 61, 3, 3, 3],
    "wind_gusts_10m_max": [16.9, 10.1, 19.1, 13.3, 10.8, 9.4, 12.6],
    "precipitation_sum": [13.6, 0.0, 9.8, 2.6, 0.0, 0.0, 0.0],
    "temperature_2m_max": [21.5, 25.2, 23.3, 16.6, 17.7, 22.3, 24.3],
    "temperature_2m_min": [13.7, 11.4, 14.7, 11.4, 11.7, 9.4, 11.7],
}

#: Chove quase todo dia, nunca muito: o estado vazio como caminho normal.
DAILY_SINGAPURA = {
    "time": DIAS_DA_PREVISAO,
    "weather_code": [80, 51, 3, 80, 51, 53, 55],
    "wind_gusts_10m_max": [37.4, 30.2, 29.5, 28.1, 26.6, 29.5, 37.1],
    "precipitation_sum": [5.8, 0.8, 0.0, 5.7, 1.5, 3.6, 7.8],
    "temperature_2m_max": [30.9, 32.1, 32.6, 32.2, 33.1, 30.0, 31.7],
    "temperature_2m_min": [25.4, 25.2, 23.7, 24.9, 24.4, 23.4, 24.2],
}

#: Seco e quente: nenhuma precipitacao na semana inteira. Vazio tambem.
DAILY_CAIRO = {
    "time": DIAS_DA_PREVISAO,
    "weather_code": [45, 2, 45, 2, 2, 3, 3],
    "wind_gusts_10m_max": [32.0, 34.9, 23.8, 36.4, 30.2, 32.4, 32.4],
    "precipitation_sum": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "temperature_2m_max": [37.3, 36.7, 37.1, 38.2, 32.2, 32.5, 33.9],
    "temperature_2m_min": [22.1, 23.1, 21.9, 25.1, 22.6, 22.4, 21.5],
}

#: Duas categorias em dias distintos: chuva de 104,4 mm no primeiro dia e
#: tempestade (96) no sexto. O caso de dois cards com datas diferentes.
DAILY_MIAMI = {
    "time": DIAS_DA_PREVISAO,
    "weather_code": [82, 3, 3, 55, 80, 96, 51],
    "wind_gusts_10m_max": [20.2, 22.0, 25.2, 26.3, 23.8, 22.7, 24.1],
    "precipitation_sum": [104.4, 0.0, 0.0, 7.2, 8.3, 3.6, 0.9],
    "temperature_2m_max": [32.4, 30.6, 31.0, 29.7, 30.1, 29.0, 30.8],
    "temperature_2m_min": [24.9, 24.2, 24.2, 27.4, 27.2, 28.2, 28.0],
}


def forecast_com_daily(daily: dict) -> dict:
    """A previsao de Berlim com outro bloco diario.

    As condicoes severas dependem so do bloco `daily`; o resto do payload e o
    mesmo em qualquer cidade. Trocar apenas o bloco mantem cada fixture legivel
    como o que ela e — uma semana de clima — em vez de repetir a resposta
    inteira seis vezes.

    Os campos que Berlim ja trazia (`sunrise`, `sunset`) sao preservados: o
    painel do sol continua montando mesmo na semana de Wellington.
    """
    return {
        **FORECAST_BERLIM,
        "daily": {
            **FORECAST_BERLIM["daily"],
            **daily,
        },
    }


# ---------------------------------------------------------------------------
# Cidades vizinhas: a resposta multi-coordenada.


def atual_de_varias(temperaturas: list[float]) -> list[dict]:
    """A resposta da chamada multi-coordenada, uma entrada por vizinha.

    A API devolve um **array na ordem de entrada** e nao repete o nome de
    nada: e a posicao que casa cada leitura com a sua cidade. As temperaturas
    sao distintas de proposito, para que uma correspondencia trocada apareca
    como valor errado na linha errada.

    Traz so `current`, que e o que a segunda chamada pede — nenhum bloco
    diario ou horario, que custariam banda sem alimentar a tabela.
    """
    return [
        {
            "latitude": 52.4,
            "longitude": 13.0,
            "timezone": "Europe/Berlin",
            "utc_offset_seconds": 7200,
            "current": {
                "time": "2026-09-14T03:00",
                "interval": 900,
                "temperature_2m": temperatura,
                "weather_code": 3,
                "is_day": 0,
            },
        }
        for temperatura in temperaturas
    ]


#: Sete dias do arquivo de Berlim, gravados do servico real em 2026-09-15.
#:
#: Os valores sao os medidos: a chuva concentrada num dia (2,1 mm em 13/09
#: contra 0,0 em dois outros) e as direcoes espalhadas entre 165° e 295° sao o
#: que o dado de verdade parece.
ARQUIVO_BERLIM = {
    "latitude": 52.54833,
    "longitude": 13.407822,
    "utc_offset_seconds": 7200,
    "timezone": "Europe/Berlin",
    "daily_units": {
        "time": "iso8601",
        "temperature_2m_max": "°C",
        "temperature_2m_min": "°C",
        "precipitation_sum": "mm",
        "relative_humidity_2m_mean": "%",
        "wind_speed_10m_max": "km/h",
        "wind_direction_10m_dominant": "°",
    },
    "daily": {
        "time": [
            "2026-09-09", "2026-09-10", "2026-09-11",
            "2026-09-12", "2026-09-13", "2026-09-14", "2026-09-15",
        ],
        "temperature_2m_max": [21.2, 18.1, 20.1, 21.7, 21.3, 18.8, 19.4],
        "temperature_2m_min": [16.0, 12.1, 10.9, 12.1, 15.0, 14.2, 13.1],
        "precipitation_sum": [0.0, 0.1, 0.0, 0.7, 2.1, 0.2, 0.0],
        "relative_humidity_2m_mean": [62, 64, 63, 68, 80, 73, 70],
        "wind_speed_10m_max": [20.1, 17.5, 8.5, 12.1, 13.7, 13.5, 11.0],
        "wind_direction_10m_dominant": [250, 275, 165, 268, 239, 295, 260],
    },
}

#: O mesmo periodo do ano anterior. Mais frio e mais chuvoso, para que a
#: diferenca media e o acumulado comparado sejam visiveis no teste.
ARQUIVO_BERLIM_ANTERIOR = {
    **ARQUIVO_BERLIM,
    "daily": {
        **ARQUIVO_BERLIM["daily"],
        "time": [
            "2025-09-09", "2025-09-10", "2025-09-11",
            "2025-09-12", "2025-09-13", "2025-09-14", "2025-09-15",
        ],
        "temperature_2m_max": [17.2, 15.1, 16.1, 17.7, 16.3, 14.8, 15.4],
        "temperature_2m_min": [12.0, 8.1, 6.9, 8.1, 11.0, 10.2, 9.1],
        "precipitation_sum": [4.0, 6.1, 0.0, 3.7, 8.1, 1.2, 0.0],
    },
}

#: **A armadilha do UV**, gravada do servico real: o arquivo aceita
#: `uv_index_max`, responde `200` e devolve `null` para **todos** os dias, com
#: `daily_units` igual a `"undefined"`. A reanalise ERA5 nao tem UV.
#:
#: Existe como fixture para que o teste prove que o payload nao carrega essa
#: coluna de nulos — um consumidor desatento a plota como linha reta no zero.
ARQUIVO_COM_UV_NULO = {
    **ARQUIVO_BERLIM,
    "daily_units": {**ARQUIVO_BERLIM["daily_units"], "uv_index_max": "undefined"},
    "daily": {**ARQUIVO_BERLIM["daily"], "uv_index_max": [None] * 7},
}

#: Um arquivo que **nao cobre** o periodo pedido: `time` vazio e todas as
#: colunas vazias, que e como a API responde um intervalo sem dado. Status
#: `200`, nao erro.
ARQUIVO_VAZIO = {
    **ARQUIVO_BERLIM,
    "daily": {chave: [] for chave in ARQUIVO_BERLIM["daily"]},
}

#: Um arquivo **incompleto**: tres dias em vez de sete, e um deles sem umidade
#: nem vento. E o que as bordas da reanalise parecem, e a pagina deve mostrar
#: os dias que existem.
ARQUIVO_INCOMPLETO = {
    **ARQUIVO_BERLIM,
    "daily": {
        "time": ["2026-09-13", "2026-09-14", "2026-09-15"],
        "temperature_2m_max": [21.3, 18.8, 19.4],
        "temperature_2m_min": [15.0, 14.2, 13.1],
        "precipitation_sum": [2.1, 0.2, None],
        "relative_humidity_2m_mean": [80, None, 70],
        "wind_speed_10m_max": [13.7, None, 11.0],
        "wind_direction_10m_dominant": [239, None, 260],
    },
}


def _uv_de_sete_dias() -> dict:
    """168 horas de UV, como a previsao as devolve.

    O perfil e o de um dia real: zero de madrugada, pico ao meio-dia. O grafico
    da pagina usa so as 24 do dia corrente, como o da tendencia do painel.
    """
    horas = []
    valores = []
    for dia in range(7):
        data = f"2026-09-{15 + dia:02d}"
        for hora in range(24):
            horas.append(f"{data}T{hora:02d}:00")
            # Uma parabola grosseira em torno das 13h, zerada a noite.
            valores.append(round(max(0.0, 3.6 - 0.09 * (hora - 13) ** 2), 2))
    return {"time": horas, "uv_index": valores}


#: O UV previsto de Berlim: horas do bloco `hourly` e a maxima de cada dia.
#:
#: E o contraponto medido da armadilha acima — na **previsao** o mesmo campo
#: devolve valores normais.
UV_BERLIM = {
    "latitude": 52.52,
    "longitude": 13.419998,
    "utc_offset_seconds": 7200,
    "timezone": "Europe/Berlin",
    "hourly_units": {"time": "iso8601", "uv_index": ""},
    "hourly": _uv_de_sete_dias(),
    "daily_units": {"time": "iso8601", "uv_index_max": ""},
    "daily": {
        "time": [f"2026-09-{15 + dia:02d}" for dia in range(7)],
        "uv_index_max": [3.55, 2.05, 3.40, 3.25, 2.80, 3.10, 2.95],
    },
}
