"""O cache em memoria: chave por coordenada arredondada, TTL de 10 minutos.

O relogio e **injetado** em todo teste de expiracao. Um `sleep` de dez minutos
nao e teste, e um de dez milissegundos so testaria um TTL que ninguem usa.
"""

import pytest

from app.services.cache import Cache, chave_de_coordenada


def test_segunda_consulta_identica_nao_refaz_o_trabalho():
    """O caso que justifica o modulo: duas consultas, uma chamada externa."""
    cache = Cache(ttl_segundos=600, agora=lambda: 0.0)
    chamadas = []

    def buscar():
        chamadas.append(1)
        return "previsao"

    assert cache.obter("berlim", buscar) == "previsao"
    assert cache.obter("berlim", buscar) == "previsao"
    assert len(chamadas) == 1


def test_apos_o_ttl_a_consulta_e_refeita():
    relogio = _Relogio()
    cache = Cache(ttl_segundos=600, agora=relogio)
    chamadas = []

    def buscar():
        chamadas.append(1)
        return {"previsao": True}

    cache.obter("berlim", buscar)
    relogio.avancar(600.1)
    cache.obter("berlim", buscar)

    assert len(chamadas) == 2


def test_dentro_do_ttl_a_entrada_continua_valida():
    """A fronteira do outro lado: 9m59s ainda serve do cache."""
    relogio = _Relogio()
    cache = Cache(ttl_segundos=600, agora=relogio)
    chamadas = []

    def buscar():
        chamadas.append(1)
        return {"previsao": True}

    cache.obter("berlim", buscar)
    relogio.avancar(599)
    cache.obter("berlim", buscar)

    assert len(chamadas) == 1


def test_chaves_diferentes_nao_se_misturam():
    cache = Cache(ttl_segundos=600, agora=lambda: 0.0)

    assert cache.obter("berlim", lambda: "a") == "a"
    assert cache.obter("paris", lambda: "b") == "b"


def test_a_entrada_expirada_e_substituida_pelo_valor_novo():
    """Expirar nao pode servir o valor velho depois — o dado mudou na fonte."""
    relogio = _Relogio()
    cache = Cache(ttl_segundos=600, agora=relogio)

    cache.obter("berlim", lambda: "antigo")
    relogio.avancar(601)

    assert cache.obter("berlim", lambda: "novo") == "novo"
    assert cache.obter("berlim", lambda: "mais novo") == "novo"


def test_falha_da_busca_nao_fica_cacheada():
    """Um erro guardado por dez minutos prenderia o painel numa falha passageira."""
    cache = Cache(ttl_segundos=600, agora=lambda: 0.0)

    def falhar():
        raise RuntimeError("sem rede")

    with pytest.raises(RuntimeError):
        cache.obter("berlim", falhar)

    assert cache.obter("berlim", lambda: "previsao") == "previsao"


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


class _Relogio:
    """Relogio injetado, avancado a mao. Nenhum teste espera tempo real."""

    def __init__(self) -> None:
        self.instante = 0.0

    def __call__(self) -> float:
        return self.instante

    def avancar(self, segundos: float) -> None:
        self.instante += segundos
