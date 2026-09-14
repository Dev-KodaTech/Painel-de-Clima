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
