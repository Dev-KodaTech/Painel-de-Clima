"""O dataset de cidades carregado uma vez, no startup.

Mora fora dos servicos porque e **estado do processo**, nao logica: quem
seleciona vizinhas recebe a lista como argumento e permanece uma funcao pura,
testavel sem subir aplicacao.

A carga acontece no `lifespan` e nao na primeira requisicao: sao ~85 ms, e
paga-los no startup faz a primeira consulta custar o mesmo que as demais.
"""

from app.services.geonames import CidadeLocal, carregar

_cidades: list[CidadeLocal] = []


def carregar_no_startup() -> None:
    """Le o dump para a memoria. Chamado uma vez, pelo `lifespan`."""
    global _cidades
    _cidades = carregar()


def cidades() -> list[CidadeLocal]:
    """As cidades carregadas.

    Lista vazia se o startup nao rodou — o que acontece em teste que monta o
    app sem `lifespan`. Quem depende dela degrada para "sem vizinhas" em vez de
    quebrar: o painel inteiro nao pode cair porque uma tabela ficou sem dados.
    """
    return _cidades
