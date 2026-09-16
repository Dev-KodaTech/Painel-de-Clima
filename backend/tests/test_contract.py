"""Teste de contrato: bate na API real e confere apenas que os campos existem.

Excluido da execucao padrao (`-m 'not contract'`). Roda sob demanda:

    uv run pytest -m contract

A Open-Meteo e dependencia externa sem versionamento. Quando o formato mudar,
o erro precisa ser legivel — mas fazer a suite inteira depender da rede a
tornaria lenta e intermitente. Verifica presenca de campo, nunca valor: os
valores mudam a cada hora.

Sao **cinco fornecedores** aqui: a Open-Meteo (clima e geocodificacao), o INMET
(alertas) e os tres feeds de noticias. Os feeds sao os que menos prometem — sao
paginas de WordPress e de um CMS proprietario, sem contrato algum —, e por isso
os unicos cujo teste de contrato verifica tambem que o **agregado** continua
utilizavel, e nao so que os campos existem.
"""

from datetime import datetime, timezone

import httpx
import pytest

from app.services import inmet, noticias, open_meteo


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


@pytest.mark.contract
@pytest.mark.anyio
async def test_arquivo_ainda_traz_os_campos_usados():
    """A reanalise ERA5, o segundo host da Open-Meteo."""
    async with httpx.AsyncClient() as client:
        arquivo = await open_meteo.buscar_arquivo(
            client, 52.52, 13.42, "2026-09-08", "2026-09-14", passado=True
        )

    assert arquivo["daily"]["time"]
    for campo in open_meteo.VARIAVEIS_DO_ARQUIVO:
        assert arquivo["daily"][campo]


@pytest.mark.contract
@pytest.mark.anyio
async def test_o_arquivo_ainda_cobre_o_dia_corrente():
    """Sem lag: e o que dispensa costurar o fim do arquivo com a previsao.

    Se um dia surgir um vao, a janela atual deixa de sair inteira do arquivo e
    a costura passa a ser necessaria — por isso o caso existe aqui.
    """
    hoje = datetime.now(timezone.utc).date().isoformat()

    async with httpx.AsyncClient() as client:
        arquivo = await open_meteo.buscar_arquivo(
            client, 52.52, 13.42, hoje, hoje, passado=False
        )

    assert arquivo["daily"]["time"] == [hoje]
    assert arquivo["daily"]["temperature_2m_max"][0] is not None


@pytest.mark.contract
@pytest.mark.anyio
async def test_o_arquivo_ainda_nao_serve_uv():
    """**A armadilha que vira regra de produto.**

    O arquivo aceita `uv_index_max` e responde `200` com `null` em todos os
    dias. Se um dia a Open-Meteo passar a servir UV historico, queremos saber —
    porque ai o UV *poderia* entrar na comparacao com o ano anterior, e a regra
    que o mantem de fora deixa de ser verdade.
    """
    async with httpx.AsyncClient() as client:
        resposta = await client.get(
            open_meteo.ARCHIVE_URL,
            params={
                "latitude": 52.52,
                "longitude": 13.42,
                "start_date": "2026-09-08",
                "end_date": "2026-09-10",
                "daily": "uv_index_max",
                "timezone": "auto",
            },
        )

    arquivo = resposta.json()
    assert all(valor is None for valor in arquivo["daily"]["uv_index_max"])


@pytest.mark.contract
@pytest.mark.anyio
async def test_a_previsao_ainda_serve_uv():
    """O contraponto: na previsao o mesmo campo devolve valores normais."""
    async with httpx.AsyncClient() as client:
        previsao = await open_meteo.buscar_uv(client, 52.52, 13.42)

    assert any(valor is not None for valor in previsao["hourly"]["uv_index"])
    assert any(valor is not None for valor in previsao["daily"]["uv_index_max"])


@pytest.mark.contract
@pytest.mark.anyio
async def test_inmet_ainda_traz_os_campos_usados():
    """Bate no `/avisos/ativos` real. O formato e proprietario e sem versao —
    se o INMET mudar um nome de campo, e este teste que denuncia, nao
    `test_inmet.py`, que roda contra fixtures fixas.
    """
    avisos = await inmet.buscar_avisos_ativos()

    if not avisos:
        pytest.skip("Nenhum aviso ativo no INMET agora — nada a conferir.")

    campos = (
        "id",
        "id_severidade",
        "severidade",
        "aviso_cor",
        "tipo",
        "data_inicio",
        "data_fim",
        "riscos",
        "instrucoes",
        "poligono",
        "geocodes",
    )
    for campo in campos:
        assert campo in avisos[0]

    # O duplo parse: `poligono` e uma string GeoJSON dentro do JSON.
    anel = inmet.poligono_do_aviso(avisos[0])
    assert len(anel) >= 3
    assert all(len(ponto) == 2 for ponto in anel)


@pytest.mark.contract
@pytest.mark.anyio
@pytest.mark.parametrize("feed", noticias.FEEDS, ids=lambda feed: feed.veiculo)
async def test_feed_de_noticias_ainda_responde_e_traz_os_campos_usados(feed):
    """Um caso por veiculo, e nao um que agrega os tres.

    Parametrizado de proposito: com um caso so, o feed do Observatorio do Clima
    voltando a recusar o cliente ficaria escondido atras dos outros dois — que
    e exatamente o que a agregacao faz em producao, e o contrario do que um
    teste de contrato deve fazer. Aqui cada veiculo falha com o proprio nome.
    """
    async with httpx.AsyncClient(
        timeout=noticias.TIMEOUT,
        headers={"User-Agent": noticias.USER_AGENT},
        follow_redirects=True,
    ) as client:
        response = await client.get(feed.url)

    # O 403 do CloudFront e o que este caso existe para pegar: sem o
    # `User-Agent` proprio, `oc.eco.br` recusa a requisicao.
    assert response.status_code == 200

    itens = noticias._itens_do_xml(response.text, feed.veiculo)

    assert itens, "o feed respondeu, mas nenhum item sobreviveu ao parsing"
    for item in itens:
        assert item.titulo
        assert item.link.startswith("https://")
        assert item.publicada_em.tzinfo is not None


@pytest.mark.contract
@pytest.mark.anyio
async def test_o_agregado_real_mistura_os_tres_veiculos():
    """Ponta a ponta contra a rede: os tres entram e a ordem vale.

    O complemento do caso acima. La se verifica cada feed isolado; aqui, que a
    agregacao de fato produz uma pagina — se um veiculo parar de responder, o
    `status` continua `ok` e e `veiculos_fora_do_ar` que denuncia, que e o
    comportamento que o ADR 0009 exige.
    """
    agregado = await noticias.buscar_noticias()

    assert agregado.status == "ok"
    assert agregado.veiculos_fora_do_ar == []
    assert len({item.veiculo for item in agregado.noticias}) == len(noticias.FEEDS)

    datas = [item.publicada_em for item in agregado.noticias]
    assert datas == sorted(datas, reverse=True)
