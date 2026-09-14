"""O cache em memoria: chave por coordenada arredondada, TTL de 10 minutos.

O relogio e **injetado** em todo teste de expiracao. Um `sleep` de dez minutos
nao e teste, e um de dez milissegundos so testaria um TTL que ninguem usa.

Assincronos porque `obter` e assincrona: o que se cacheia sao chamadas de rede,
e nao ha caminho sincrono na producao para testar.
"""

import pytest

from app.services.cache import Cache, chave_de_coordenada
from tests.conftest import Relogio

pytestmark = pytest.mark.anyio


async def test_segunda_consulta_identica_nao_refaz_o_trabalho():
    """O caso que justifica o modulo: duas consultas, uma chamada externa."""
    cache = Cache(ttl_segundos=600, agora=lambda: 0.0)
    chamadas = []

    async def buscar():
        chamadas.append(1)
        return "previsao"

    assert await cache.obter("berlim", buscar) == "previsao"
    assert await cache.obter("berlim", buscar) == "previsao"
    assert len(chamadas) == 1


async def test_apos_o_ttl_a_consulta_e_refeita():
    relogio = Relogio()
    cache = Cache(ttl_segundos=600, agora=relogio)
    chamadas = []

    async def buscar():
        chamadas.append(1)
        return {"previsao": True}

    await cache.obter("berlim", buscar)
    relogio.avancar(600.1)
    await cache.obter("berlim", buscar)

    assert len(chamadas) == 2


async def test_dentro_do_ttl_a_entrada_continua_valida():
    """A fronteira do outro lado: 9m59s ainda serve do cache."""
    relogio = Relogio()
    cache = Cache(ttl_segundos=600, agora=relogio)
    chamadas = []

    async def buscar():
        chamadas.append(1)
        return {"previsao": True}

    await cache.obter("berlim", buscar)
    relogio.avancar(599)
    await cache.obter("berlim", buscar)

    assert len(chamadas) == 1


async def test_chaves_diferentes_nao_se_misturam():
    cache = Cache(ttl_segundos=600, agora=lambda: 0.0)

    async def a():
        return "a"

    async def b():
        return "b"

    assert await cache.obter("berlim", a) == "a"
    assert await cache.obter("paris", b) == "b"


async def test_a_entrada_expirada_e_substituida_pelo_valor_novo():
    """Expirar nao pode servir o valor velho depois — o dado mudou na fonte."""
    relogio = Relogio()
    cache = Cache(ttl_segundos=600, agora=relogio)

    async def antigo():
        return "antigo"

    async def novo():
        return "novo"

    async def mais_novo():
        return "mais novo"

    await cache.obter("berlim", antigo)
    relogio.avancar(601)

    assert await cache.obter("berlim", novo) == "novo"
    assert await cache.obter("berlim", mais_novo) == "novo"


async def test_falha_da_busca_nao_fica_cacheada():
    """Um erro guardado por dez minutos prenderia o painel numa falha passageira."""
    cache = Cache(ttl_segundos=600, agora=lambda: 0.0)

    async def falhar():
        raise RuntimeError("sem rede")

    async def previsao():
        return "previsao"

    with pytest.raises(RuntimeError):
        await cache.obter("berlim", falhar)

    assert await cache.obter("berlim", previsao) == "previsao"


def test_coordenadas_proximas_caem_na_mesma_chave():
    """A mesma cidade vinda de candidatas com precisao diferente: uma entrada.

    `52.52437` e `52.5244` sao Berlim nas duas; sem o arredondamento seriam
    duas entradas, e o cache erraria no caso que existe para servir.
    """
    assert chave_de_coordenada("previsao", 52.52437, 13.41053) == chave_de_coordenada(
        "previsao", 52.5244, 13.4105
    )


def test_coordenadas_de_cidades_distintas_nao_colidem():
    assert chave_de_coordenada("previsao", 52.52, 13.41) != chave_de_coordenada(
        "previsao", 48.85, 2.35
    )


def test_o_prefixo_separa_consultas_diferentes_sobre_a_mesma_coordenada():
    """Previsao e tempo atual partem de lat/lon e devolvem coisas distintas."""
    assert chave_de_coordenada("previsao", 52.52, 13.41) != chave_de_coordenada(
        "atual", 52.52, 13.41
    )


def test_conjuntos_de_vizinhas_diferentes_nao_colidem():
    """A chave das vizinhas cobre o conjunto inteiro, nao a primeira cidade."""
    assert chave_de_coordenada("atual", 52.52, 13.41, 52.40, 13.06) != (
        chave_de_coordenada("atual", 52.52, 13.41, 48.85, 2.35)
    )
