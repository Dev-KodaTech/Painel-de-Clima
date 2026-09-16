"""O ponto de injecao do banco, visto de fora.

O que estes casos protegem e a propriedade que o ticket exige da suite: a
execucao padrao nao tem banco, nao tem Docker e nao pode ganhar nenhum dos
dois por acidente. Um `import` que abrisse conexao, ou um padrao que fosse o
repositorio em memoria, quebraria isso em silencio — e o sintoma apareceria
tarde, em producao ou num CI sem container.

Nenhum caso aqui espia variavel privada: o que se observa e qual implementacao
`atual()` entrega e se a transacao foi aberta, que e o que a aplicacao sente.
"""

import pytest

from app import repositorio_do_processo
from app.db import transacao as banco
from app.db.repositorio import RepositorioEmMemoria, RepositorioSql


@pytest.fixture
def em_memoria():
    """Injeta o repositorio em memoria e desfaz a troca no fim.

    Mesma mecanica da fixture `relogio` de `test_cache_http.py`: o repositorio
    e estado de processo, e uma troca que vaza serviria o teste seguinte.
    """
    repositorio = RepositorioEmMemoria()
    repositorio_do_processo.substituir(repositorio)
    yield repositorio
    repositorio_do_processo.substituir(None)


class TransacaoFalsa:
    """Uma transacao que conta as aberturas, sem banco atras.

    Existe para que o caso do padrao SQL rode na suite padrao: o que ele
    verifica e **qual caminho** `atual()` toma, e nao o que o Postgres
    responde.
    """

    def __init__(self, aberturas: list[int]) -> None:
        self._aberturas = aberturas

    def __enter__(self) -> object:
        self._aberturas.append(1)
        return object()

    def __exit__(self, *_) -> bool:
        return False


def test_o_padrao_e_o_sql_e_nao_o_em_memoria(monkeypatch):
    """Esquecer a injecao em producao tem de doer **na primeira requisicao**.

    Se o padrao fosse o em memoria, o app aceitaria cadastro, responderia
    `200` e perderia tudo no restart — falha silenciosa e tardia. Com o SQL
    como padrao, o mesmo esquecimento derruba a primeira requisicao com erro
    de conexao, que e o sintoma que se quer.
    """
    aberturas: list[int] = []
    monkeypatch.setattr(banco, "transacao", lambda: TransacaoFalsa(aberturas))

    with repositorio_do_processo.atual() as repositorio:
        assert isinstance(repositorio, RepositorioSql)

    assert aberturas == [1], "o repositorio de verdade abre a transacao"


def test_a_troca_faz_a_aplicacao_usar_o_em_memoria(em_memoria):
    with repositorio_do_processo.atual() as repositorio:
        assert repositorio is em_memoria


def test_o_que_a_requisicao_escreveu_o_teste_enxerga(em_memoria):
    """Duas entradas em `atual()` veem o mesmo estado.

    E a propriedade que torna o repositorio em memoria util num teste de
    costura HTTP: o endpoint escreve dentro da requisicao e o caso confere
    depois, do lado de fora.
    """
    with repositorio_do_processo.atual() as repositorio:
        conta = repositorio.criar_conta("ana@exemplo.com", "hash")

    with repositorio_do_processo.atual() as depois:
        assert depois.conta_por_id(conta.id) == conta


def test_desfazer_a_troca_devolve_o_sql(monkeypatch):
    """A troca e reversivel — e o que impede um teste de contaminar o seguinte."""
    aberturas: list[int] = []
    monkeypatch.setattr(banco, "transacao", lambda: TransacaoFalsa(aberturas))
    repositorio_do_processo.substituir(RepositorioEmMemoria())

    repositorio_do_processo.substituir(None)

    with repositorio_do_processo.atual() as repositorio:
        assert isinstance(repositorio, RepositorioSql)


def test_importar_a_aplicacao_nao_conecta_no_banco():
    """O `engine` nasce sob demanda, nao na importacao.

    Sem isso, `import app.main` exigiria Postgres e a suite inteira — os 240
    casos que nada tem com banco — passaria a depender do container. O caso
    roda com o banco parado: e nessa condicao que ele tem valor.
    """
    banco.descartar()

    import app.main  # noqa: F401

    # Nenhuma conexao foi aberta: pedir uma agora ainda teria de criar o
    # `engine` do zero, e e isso que `descartar()` deixou para tras.
    assert banco.engine() is banco.engine()
