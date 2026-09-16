"""O cliente do INMET: dedup, duplo parse de poligono, ponto-em-poligono.

O que se verifica aqui e a logica do modulo isolada da costura HTTP — as
respostas mockadas nunca tocam rede de verdade, so o formato que o modulo
recebe de `respx`. `test_condicoes_inmet.py` cobre o endpoint por cima disto.
"""

import httpx
import pytest
import respx

from app.services import inmet
from tests.fixtures import (
    AVISO_INMET_GRANDE_PERIGO_SINTETICO,
    AVISO_INMET_PERIGO,
    AVISO_INMET_PERIGO_POTENCIAL,
    CURITIBA,
    SAO_PAULO,
    avisos_inmet,
)

pytestmark = pytest.mark.anyio


@respx.mock
async def test_dedup_de_hoje_e_futuro_por_id():
    """O mesmo aviso em `hoje` e `futuro` conta uma vez so."""
    payload = avisos_inmet(
        AVISO_INMET_PERIGO_POTENCIAL, futuro=(AVISO_INMET_PERIGO_POTENCIAL,)
    )
    respx.get(inmet.ENDPOINT).mock(return_value=httpx.Response(200, json=payload))

    avisos = await inmet.buscar_avisos_ativos()

    assert len(avisos) == 1


@respx.mock
async def test_avisos_distintos_em_hoje_e_futuro_nao_se_fundem():
    payload = avisos_inmet(AVISO_INMET_PERIGO_POTENCIAL, futuro=(AVISO_INMET_PERIGO,))
    respx.get(inmet.ENDPOINT).mock(return_value=httpx.Response(200, json=payload))

    avisos = await inmet.buscar_avisos_ativos()

    assert {aviso["id"] for aviso in avisos} == {
        AVISO_INMET_PERIGO_POTENCIAL["id"],
        AVISO_INMET_PERIGO["id"],
    }


def test_poligono_do_aviso_faz_o_duplo_parse():
    """`poligono` e uma string GeoJSON dentro do JSON — precisa de dois `loads`."""
    anel = inmet.poligono_do_aviso(AVISO_INMET_PERIGO_POTENCIAL)

    assert anel[0] == (-52.5, -26.5)
    # `[lon, lat]`, a ordem do GeoJSON: o primeiro numero e a longitude.
    assert all(lon < 0 and lat < 0 for lon, lat in anel)


def test_ponto_dentro_do_poligono():
    anel = inmet.poligono_do_aviso(AVISO_INMET_PERIGO_POTENCIAL)

    assert inmet.ponto_no_poligono(CURITIBA["latitude"], CURITIBA["longitude"], anel)


def test_ponto_fora_do_poligono():
    """Sao Paulo fica fora do retangulo do fixture, como os `geocodes` do
    mesmo aviso confirmam (4106902 e so Curitiba)."""
    anel = inmet.poligono_do_aviso(AVISO_INMET_PERIGO_POTENCIAL)

    assert not inmet.ponto_no_poligono(
        SAO_PAULO["latitude"], SAO_PAULO["longitude"], anel
    )


@respx.mock
async def test_alertas_da_coordenada_filtra_por_poligono():
    payload = avisos_inmet(AVISO_INMET_PERIGO_POTENCIAL)
    respx.get(inmet.ENDPOINT).mock(return_value=httpx.Response(200, json=payload))

    dentro = await inmet.alertas_da_coordenada(
        CURITIBA["latitude"], CURITIBA["longitude"]
    )
    fora = await inmet.alertas_da_coordenada(
        SAO_PAULO["latitude"], SAO_PAULO["longitude"]
    )

    assert len(dentro) == 1
    assert fora == []


@respx.mock
async def test_falha_da_rede_vira_inmet_indisponivel():
    respx.get(inmet.ENDPOINT).mock(side_effect=httpx.ConnectError("sem rede"))

    with pytest.raises(inmet.InmetIndisponivel):
        await inmet.alertas_da_coordenada(CURITIBA["latitude"], CURITIBA["longitude"])


@respx.mock
async def test_cache_e_de_chave_fixa_nao_por_coordenada():
    """Duas coordenadas diferentes reaproveitam a mesma chamada ao INMET —
    o feed e nacional, e nao ha coordenada na requisicao real."""
    payload = avisos_inmet(AVISO_INMET_PERIGO_POTENCIAL)
    rota = respx.get(inmet.ENDPOINT).mock(return_value=httpx.Response(200, json=payload))

    await inmet.alertas_da_coordenada(CURITIBA["latitude"], CURITIBA["longitude"])
    await inmet.alertas_da_coordenada(SAO_PAULO["latitude"], SAO_PAULO["longitude"])

    assert rota.call_count == 1


def test_para_alerta_traz_severidade_como_texto_alem_da_cor():
    """A severidade nunca e so cor: o modelo carrega o texto oficial junto."""
    alerta = inmet.para_alerta(AVISO_INMET_PERIGO_POTENCIAL)

    assert alerta.severidade == "Perigo Potencial"
    assert alerta.cor == "#FFFE00"
    assert alerta.id_severidade == 6


def test_grande_perigo_usa_a_cor_sintetica_documentada():
    """id_severidade 8 nunca foi observado ao vivo (ADR 0008) — o fixture e
    sintetico, e a cor vem da tabela presumida do modulo, nao do feed."""
    alerta = inmet.para_alerta(AVISO_INMET_GRANDE_PERIGO_SINTETICO)

    assert alerta.id_severidade == 8
    assert alerta.cor == inmet.CORES_POR_SEVERIDADE[8]


def test_severidade_desconhecida_erra_para_o_alarme_e_nao_para_a_calmaria():
    """Uma severidade fora da tabela so pode ser mais grave que a maior que
    conhecemos — a escala do INMET cresce. Pinta-la de amarelo diria "aviso
    fraco" sobre o que pode ser extremo."""
    alerta = inmet.para_alerta(
        {**AVISO_INMET_GRANDE_PERIGO_SINTETICO, "id_severidade": "9"}
    )

    assert alerta.cor == inmet.COR_DE_SEVERIDADE_DESCONHECIDA
    assert alerta.cor != inmet.CORES_POR_SEVERIDADE[6]


async def test_feed_malformado_vira_indisponivel():
    """Campo renomeado ou ausente e falha de fornecedor, nao `500` nosso."""
    payload = avisos_inmet(
        {chave: valor for chave, valor in AVISO_INMET_PERIGO.items() if chave != "tipo"}
    )
    with respx.mock:
        respx.get(inmet.ENDPOINT).mock(return_value=httpx.Response(200, json=payload))

        with pytest.raises(inmet.InmetIndisponivel):
            await inmet.alertas_da_coordenada(
                CURITIBA["latitude"], CURITIBA["longitude"]
            )


async def test_corpo_nao_json_vira_indisponivel():
    """`json.JSONDecodeError` e `ValueError`, nao `httpx.HTTPError` — sem o
    `ValueError` no `except`, um `200` com HTML subia como erro nao tratado."""
    with respx.mock:
        respx.get(inmet.ENDPOINT).mock(
            return_value=httpx.Response(200, text="<html>erro</html>")
        )

        with pytest.raises(inmet.InmetIndisponivel):
            await inmet.buscar_avisos_ativos()
