"""Costura da selecao de vizinhas: funcao pura sobre o dataset real, sem HTTP.

Merece costura propria porque os casos que importam exigem as 34 mil linhas:
so o dataset inteiro mostra que Honolulu nao alcanca a China e que Reykjavik
nao devolve lista vazia. Amarra-los a requisicoes os tornaria lentos e
indiretos.

O dataset e carregado **uma vez** para o modulo inteiro: sao ~85 ms, e paga-los
por teste tornaria a suite lenta sem testar nada a mais.
"""

import pytest

from app.services.geonames import carregar
from app.services.vizinhas import distancia_km, selecionar

BERLIM = (52.52437, 13.41053)
BASILEIA = (47.55839, 7.57327)
HONOLULU = (21.30694, -157.85833)
REYKJAVIK = (64.13548, -21.89541)
PAPEETE = (-17.53333, -149.56667)


@pytest.fixture(scope="module")
def cidades():
    return carregar()


def nomes(selecionadas):
    return [cidade.name for cidade, _ in selecionadas]


def test_dataset_carrega_as_cidades_do_dump(cidades):
    """Regressao do indice de coluna errado, que devolvia zero em silencio.

    `feature_code` e a coluna `[7]`; `[6]` e `feature_class`, que vale `'P'` em
    todas as linhas — filtra-la por `PPL` nao levanta excecao, apenas devolve
    lista vazia e um painel de vizinhas permanentemente em branco.
    """
    assert len(cidades) > 30_000


def test_dataset_traz_os_campos_das_colunas_certas(cidades):
    """Um indice deslocado daria nome no lugar do pais, sem erro algum."""
    berlim = next(
        cidade
        for cidade in cidades
        if cidade.name == "Berlin" and cidade.country_code == "DE"
    )

    assert berlim.latitude == pytest.approx(52.52437)
    assert berlim.longitude == pytest.approx(13.41053)
    assert berlim.population > 3_000_000
    # `id` e `timezone` existem para o modo coordenada de `/api/cities`, que
    # devolve a candidata **do dataset** no mesmo formato do modo texto.
    assert berlim.id == 2950159
    assert berlim.timezone == "Europe/Berlin"


def test_berlim_devolve_vizinhas_reais_e_nao_os_proprios_bairros(cidades):
    """O dataset lista os bairros de Berlim como cidades.

    Kreuzberg (2,8 km) e Prenzlauer Berg (1,9 km) tem populacao de cidade media
    e venceriam qualquer criterio por tamanho. Pontuar por populacao/distancia
    devolvia exatamente isso — suburbios do proprio municipio.
    """
    escolhidas = nomes(selecionar(cidades, *BERLIM))

    assert "Potsdam" in escolhidas
    assert "Oranienburg" in escolhidas
    for bairro in ("Kreuzberg", "Prenzlauer Berg", "Mitte", "Heiligensee", "Teltow"):
        assert bairro not in escolhidas


def test_basileia_mistura_tres_paises_sem_tratamento_especial(cidades):
    """Proximidade importa mais que nacionalidade, e nada no algoritmo olha o
    pais: a mistura sai sozinha da geografia."""
    escolhidas = selecionar(cidades, *BASILEIA)
    paises = {cidade.country_code for cidade, _ in escolhidas}

    assert {"CH", "DE", "FR"} <= paises


def test_honolulu_nao_alcanca_megalopole_distante(cidades):
    """Regressao do criterio de raio fixo.

    "A maior cidade num raio que se expande" mandava Honolulu para megalopoles
    chinesas a 8.000 km: num raio largo o bastante, a maior cidade nao e
    vizinha de ninguem — e so a maior do mundo naquele raio.

    A asercao e sobre a **propriedade**, nao sobre nomes: proibir "Shanghai"
    deixaria passar Los Angeles, que era o que de fato aparecia. Esgotado o
    arquipelago, a lista termina — nao se completa com a maior cidade que
    sobrou no anel largo.
    """
    escolhidas = selecionar(cidades, *HONOLULU)

    assert all(cidade.country_code == "US" for cidade, _ in escolhidas)
    # Todas no Havai: o continente esta a mais de 3.000 km.
    assert all(distancia < 1_000 for _, distancia in escolhidas)
    # A escala de aneis mantem as primeiras no proprio arquipelago.
    assert escolhidas[0][1] < 100


def test_lista_termina_em_vez_de_completar_com_cidade_solta(cidades):
    """Quatro vizinhas honestas valem mais que cinco com uma intrusa.

    Honolulu tem quatro cidades havaianas separadas o bastante; a quinta linha
    so poderia vir do continente. O ticket pede "quatro a cinco", e e aqui que
    o quatro acontece.
    """
    escolhidas = selecionar(cidades, *HONOLULU)

    assert len(escolhidas) == 4
    assert "Los Angeles" not in nomes(escolhidas)


def test_cidade_isolada_de_verdade_mantem_as_cinco(cidades):
    """O corte da cauda nao pode punir isolamento real.

    As vizinhas de Papeete estao entre 4.094 e 4.569 km: distantes, mas um
    conjunto — os saltos entre elas sao de 1,0x. E o salto **brusco** que
    denuncia preenchimento, nao a distancia grande.
    """
    assert len(selecionar(cidades, *PAPEETE)) == 5


@pytest.mark.parametrize(
    ("nome", "coordenada"), [("Reykjavik", REYKJAVIK), ("Papeete", PAPEETE)]
)
def test_cidade_isolada_degrada_para_aneis_largos(cidades, nome, coordenada):
    """Distante e honesto; vazio seria o painel parecendo quebrado."""
    escolhidas = selecionar(cidades, *coordenada)

    assert len(escolhidas) == 5
    # O ultimo anel e meia circunferencia da Terra: sempre ha o que devolver.
    assert all(distancia > 0 for _, distancia in escolhidas)


def test_vizinhas_vem_ordenadas_da_mais_perto_para_a_mais_longe(cidades):
    distancias = [distancia for _, distancia in selecionar(cidades, *BERLIM)]

    assert distancias == sorted(distancias)


def test_nenhuma_vizinha_e_a_propria_cidade(cidades):
    """O dataset contem a propria cidade consultada, a 0 km dela mesma."""
    escolhidas = selecionar(cidades, *BERLIM)

    assert "Berlin" not in nomes(escolhidas)
    assert all(distancia >= 15 for _, distancia in escolhidas)


def test_escolhidas_guardam_separacao_minima_entre_si(cidades):
    """Sem separacao, uma conurbacao ocuparia a tabela com a mesma mancha."""
    escolhidas = selecionar(cidades, *BERLIM)

    for indice, (uma, _) in enumerate(escolhidas):
        for outra, _ in escolhidas[indice + 1 :]:
            distancia = distancia_km(
                uma.latitude, uma.longitude, outra.latitude, outra.longitude
            )
            assert distancia >= 25


def test_distancia_conhecida_confere():
    """Berlim-Paris sao ~878 km em linha reta."""
    paris = (48.85341, 2.3488)

    assert distancia_km(*BERLIM, *paris) == pytest.approx(878, abs=10)
