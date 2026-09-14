"""Teste de contrato: bate na API real e confere apenas que os campos existem.

Excluido da execucao padrao (`-m 'not contract'`). Roda sob demanda:

    uv run pytest -m contract

A Open-Meteo e dependencia externa sem versionamento. Quando o formato mudar,
o erro precisa ser legivel — mas fazer a suite inteira depender da rede a
tornaria lenta e intermitente. Verifica presenca de campo, nunca valor: os
valores mudam a cada hora.
"""

import httpx
import pytest

from app.services import open_meteo


@pytest.mark.contract
@pytest.mark.anyio
async def test_geocoding_ainda_traz_os_campos_usados():
    async with httpx.AsyncClient() as client:
        (candidata, *_) = await open_meteo.buscar_cidades(client, "Berlim")

    for campo in ("id", "name", "latitude", "longitude", "country", "country_code"):
        assert campo in candidata


@pytest.mark.contract
@pytest.mark.anyio
async def test_geocoding_sem_correspondencia_ainda_omite_results():
    """Se um dia vier lista vazia, o cliente continua correto — mas queremos saber."""
    async with httpx.AsyncClient() as client:
        assert await open_meteo.buscar_cidades(client, "zzzqqqxyzwww") == []


@pytest.mark.contract
@pytest.mark.anyio
async def test_forecast_ainda_traz_os_campos_usados():
    async with httpx.AsyncClient() as client:
        previsao = await open_meteo.buscar_previsao(client, 52.52, 13.42)

    for campo in ("timezone", "utc_offset_seconds", "latitude", "longitude"):
        assert campo in previsao
    for campo in ("time", "temperature_2m", "apparent_temperature", "weather_code", "is_day"):
        assert campo in previsao["current"]
    for campo in ("temperature_2m_max", "temperature_2m_min"):
        assert previsao["daily"][campo]

    # As armadilhas de formato, verificadas explicitamente.
    assert isinstance(previsao["current"]["weather_code"], int)
    assert "+" not in previsao["current"]["time"]
    assert "Z" not in previsao["current"]["time"]
