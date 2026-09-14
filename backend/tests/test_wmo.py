"""Tabela WMO: cobertura dos codigos emitidos e degradacao do desconhecido."""

import pathlib

import pytest

from app.services.wmo import (
    DESCRICAO_DESCONHECIDA,
    ICONE_DESCONHECIDO,
    TABELA_WMO,
    traduzir,
)

#: Os codigos que a Open-Meteo de fato emite, conforme verificado contra
#: respostas ao vivo. Listados aqui para que a tabela nao possa perder um
#: deles em silencio.
CODIGOS_EMITIDOS = [
    0, 1, 2, 3,
    45, 48,
    51, 53, 55, 56, 57,
    61, 63, 65, 66, 67,
    71, 73, 75, 77,
    80, 81, 82, 85, 86,
    95, 96, 99,
]


@pytest.mark.parametrize("codigo", CODIGOS_EMITIDOS)
def test_todo_codigo_emitido_tem_texto_e_icone(codigo):
    description, icon = traduzir(codigo, is_day=True)

    assert description and description != DESCRICAO_DESCONHECIDA
    assert icon and icon != ICONE_DESCONHECIDO


@pytest.mark.parametrize("codigo", CODIGOS_EMITIDOS)
def test_todo_codigo_emitido_tem_icone_tambem_a_noite(codigo):
    _, icon = traduzir(codigo, is_day=False)

    assert icon and icon != ICONE_DESCONHECIDO


def test_a_tabela_nao_tem_codigo_fora_do_conjunto_emitido():
    assert sorted(TABELA_WMO) == CODIGOS_EMITIDOS


def test_ceu_limpo_troca_de_icone_entre_dia_e_noite():
    assert traduzir(0, is_day=True) == ("Ceu limpo", "clear-day")
    assert traduzir(0, is_day=False) == ("Ceu limpo", "clear-night")


def test_nublado_usa_o_mesmo_icone_de_dia_e_de_noite():
    assert traduzir(3, is_day=True)[1] == traduzir(3, is_day=False)[1]


def test_codigo_desconhecido_devolve_o_par_de_fallback():
    """A Open-Meteo nao versiona o vocabulario: um codigo novo nao derruba."""
    assert traduzir(42) == (DESCRICAO_DESCONHECIDA, ICONE_DESCONHECIDO)


def test_todo_icone_da_tabela_existe_no_pacote_meteocons():
    """Os nomes da tabela sao caminhos de arquivo no `@bybas/weather-icons`.

    Um nome inventado renderizaria um espaco vazio sem erro nenhum, entao a
    correspondencia entre a tabela do backend e os arquivos do pacote fica
    presa aqui. O teste se desativa sozinho se o frontend nao estiver
    instalado, para nao exigir `npm install` na suite do backend.
    """
    icones = (
        pathlib.Path(__file__).parents[2]
        / "frontend/node_modules/@bybas/weather-icons/production/fill/all"
    )
    if not icones.is_dir():
        pytest.skip("pacote de icones nao instalado")

    nomes = {ICONE_DESCONHECIDO}
    for condicao in TABELA_WMO.values():
        nomes.update({condicao.icon_dia, condicao.icon_noite})

    ausentes = sorted(nome for nome in nomes if not (icones / f"{nome}.svg").is_file())
    assert ausentes == []
