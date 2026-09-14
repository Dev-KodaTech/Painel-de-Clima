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
    for campo in open_meteo.VARIAVEIS_DIARIAS:
        assert previsao["daily"][campo]
    assert previsao["hourly"]["temperature_2m"]

    # Sete dias pedidos, sete devolvidos — e as horas acompanham os dias.
    assert len(previsao["daily"]["time"]) == open_meteo.DIAS_DE_PREVISAO
    assert len(previsao["hourly"]["time"]) == open_meteo.DIAS_DE_PREVISAO * 24

    # As armadilhas de formato, verificadas explicitamente.
    assert isinstance(previsao["current"]["weather_code"], int)
    for timestamp in (
        previsao["current"]["time"],
        previsao["hourly"]["time"][0],
        previsao["daily"]["sunrise"][0],
    ):
        assert "+" not in timestamp
        assert "Z" not in timestamp

    # O bloco horario comeca a meia-noite do dia corrente, nunca "agora".
    assert previsao["hourly"]["time"][0].endswith("T00:00")


@pytest.mark.contract
@pytest.mark.anyio
async def test_multi_coordenada_ainda_devolve_array_na_ordem_de_entrada():
    """A chamada das vizinhas: um array, na ordem pedida, com fuso por cidade.

    Duas propriedades sao a base do bloco `nearby` e nenhuma esta documentada
    como garantia: que varias coordenadas devolvem **lista** (uma so devolve
    objeto) e que a ordem da resposta e a da entrada. A correspondencia entre
    cidade e temperatura e posicional — se a ordem deixar de valer, o painel
    passa a exibir a temperatura de uma cidade sob o nome de outra, e nada no
    dado denuncia a troca.
    """
    berlim = (52.52, 13.42)
    honolulu = (21.31, -157.86)

    async with httpx.AsyncClient() as client:
        atuais = await open_meteo.buscar_atual_de_varias(client, [berlim, honolulu])

    assert isinstance(atuais, list)
    assert len(atuais) == 2

    for atual, (latitude, _) in zip(atuais, [berlim, honolulu]):
        # A API arredonda para a celula da grade, mas nao troca hemisferio.
        assert abs(atual["latitude"] - latitude) < 1
        for campo in open_meteo.VARIAVEIS_VIZINHAS:
            assert campo in atual["current"]

    # `timezone=auto` resolve por coordenada, nao uma vez para a requisicao.
    assert atuais[0]["timezone"] != atuais[1]["timezone"]


@pytest.mark.contract
@pytest.mark.anyio
async def test_uma_coordenada_ainda_devolve_objeto_e_o_cliente_normaliza():
    """A assimetria que o cliente esconde: uma coordenada nao vira lista de um."""
    async with httpx.AsyncClient() as client:
        atuais = await open_meteo.buscar_atual_de_varias(client, [(52.52, 13.42)])

    assert isinstance(atuais, list)
    assert len(atuais) == 1
