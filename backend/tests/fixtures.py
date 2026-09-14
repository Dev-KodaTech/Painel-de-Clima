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

#: Previsao de Berlim. `utc_offset_seconds` nao-zero, timestamps sem sufixo.
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
    "daily_units": {
        "time": "iso8601",
        "temperature_2m_max": "°C",
        "temperature_2m_min": "°C",
    },
    "daily": {
        "time": ["2026-09-14"],
        "temperature_2m_max": [17.2],
        "temperature_2m_min": [13.7],
    },
}
