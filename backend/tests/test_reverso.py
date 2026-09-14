"""Costura do reverse geocoding: coordenada em cidade, sobre o dataset real.

Funcao pura, como a selecao de vizinhas, e testada contra as 34 mil linhas
pelo mesmo motivo: o que importa aqui e o corte entre "esta numa cidade" e
"esta longe de qualquer uma", e ele so aparece no dataset inteiro.
"""

import pytest

from app.services.geonames import carregar
from app.services.reverso import EMPATE_KM, RAIO_MAXIMO_KM, mais_proxima
from app.services.vizinhas import distancia_km

BERLIM = (52.52437, 13.41053)
TOQUIO = (35.6895, 139.69171)
SAO_PAULO = (-23.5505, -46.6333)
LONDRES_SUBURBIO = (51.46875, -0.36167)
AMAZONIA = (-4.5, -65.0)
ATACAMA = (-24.0, -69.0)
INTERIOR_DA_AUSTRALIA = (-26.0, 133.0)
MEIO_DO_PACIFICO = (-10.0, -140.0)


@pytest.fixture(scope="module")
def cidades():
    return carregar()


@pytest.mark.parametrize(
    ("nome", "coordenada"),
    [
        ("Berlim", BERLIM),
        ("Toquio", TOQUIO),
        ("suburbio de Londres", LONDRES_SUBURBIO),
    ],
)
def test_coordenada_urbana_acerta_abaixo_de_cinco_km(cidades, nome, coordenada):
    """Toda area povoada acerta bem abaixo do limiar.

    Medido em 12 coordenadas de densidade oposta: Berlim 0,0 km, Toquio 0,1 km,
    Londres 2,2 km, Fairbanks 4,3 km — e o caso seguinte ja salta para 95 km.
    Nao ha meio-termo entre "esta numa cidade" e "esta longe de todas".
    """
    resultado = mais_proxima(cidades, *coordenada)

    assert resultado is not None
    _, distancia = resultado
    assert distancia < 5


def test_coordenada_urbana_devolve_a_cidade_certa(cidades):
    resultado = mais_proxima(cidades, *TOQUIO)

    assert resultado is not None
    cidade, _ = resultado
    assert cidade.country_code == "JP"


@pytest.mark.parametrize(
    ("nome", "coordenada"),
    [
        ("Amazonia", AMAZONIA),
        ("Atacama", ATACAMA),
        ("interior da Australia", INTERIOR_DA_AUSTRALIA),
        ("meio do Pacifico", MEIO_DO_PACIFICO),
    ],
)
def test_coordenada_remota_nao_sugere_nada(cidades, nome, coordenada):
    """Sugerir Alice Springs a quem esta a 341 km dela e pior que o silencio.

    O corte natural medido: a cidade mais proxima da Amazonia esta a 95 km, do
    Atacama a 149 km, do interior da Australia a 341 km, do Pacifico a 1.043
    km. Qualquer limiar entre 10 e 90 km produz este mesmo resultado.
    """
    assert mais_proxima(cidades, *coordenada) is None


def test_centro_de_metropole_devolve_a_cidade_e_nao_o_distrito(cidades):
    """O dataset lista distritos como cidades, empatados com a propria cidade.

    No centro de Sao Paulo, `Se` (23.832 hab.) e `Sao Paulo` (12,4 milhoes)
    estao **ambos a 0,4 km**: a distancia pura decide o empate por ruido de
    arredondamento, e o cabecalho do painel leria "Se" para quem esta na maior
    cidade do pais. E a mesma armadilha que `vizinhas` documenta para os
    bairros de Berlim.
    """
    resultado = mais_proxima(cidades, *SAO_PAULO)

    assert resultado is not None
    cidade, _ = resultado
    assert cidade.name == "São Paulo"


@pytest.mark.parametrize(
    ("esperada", "coordenada"),
    [("Berlin", BERLIM), ("Tokyo", TOQUIO), ("São Paulo", SAO_PAULO)],
)
def test_desempate_nao_rouba_o_lugar_de_quem_esta_de_fato_mais_perto(
    cidades, esperada, coordenada
):
    """Preferir a maior so vale no empate, e nao a qualquer distancia.

    Sem o limite do empate, "a maior num raio" e o criterio de raio fixo que o
    ticket 08 descartou — o que mandaria qualquer suburbio para a metropole
    vizinha.
    """
    resultado = mais_proxima(cidades, *coordenada)

    assert resultado is not None
    assert resultado[0].name == esperada


def test_suburbio_continua_sendo_o_suburbio_e_nao_a_metropole(cidades):
    """Hounslow esta a 2,2 km de quem esta la, e Londres a 17 km.

    O desempate por populacao nao pode alcanca-la: quem esta em Hounslow esta
    em Hounslow. E o teste que impede o desempate de virar "a maior por perto".
    """
    resultado = mais_proxima(cidades, *LONDRES_SUBURBIO)

    assert resultado is not None
    assert resultado[0].name == "Hounslow"


def test_a_mais_proxima_esta_entre_as_mais_proximas(cidades):
    """Nao basta estar dentro do raio: tem de estar junto da menor distancia.

    Numa metropole ha dezenas de candidatas abaixo de 50 km, e devolver
    qualquer uma delas passaria pelo teste do raio exibindo o bairro errado. A
    folga e a do empate — e so dentro dela que a populacao decide.
    """
    resultado = mais_proxima(cidades, *BERLIM)

    assert resultado is not None
    _, distancia = resultado
    menor = min(
        distancia_km(*BERLIM, cidade.latitude, cidade.longitude) for cidade in cidades
    )
    assert distancia <= menor + EMPATE_KM


def test_o_raio_maximo_e_cinquenta_km():
    """O limiar e decisao da spec, nao detalhe de implementacao."""
    assert RAIO_MAXIMO_KM == 50
