"""O repositorio em uso, trocavel — o ponto de injecao do banco.

Mesma mecanica de `cache_do_processo.py`, e de proposito: quem le aquele
arquivo ja sabe ler este. A aplicacao pede `atual()`, o teste chama
`substituir()`, e nenhum endpoint sabe qual das duas implementacoes esta
respondendo.

**O padrao e o SQL.** Fosse o em memoria, esquecer a troca em producao daria um
app que aceita cadastro, responde `200` e perde tudo no restart — uma falha
silenciosa e tardia. Com o SQL como padrao, o mesmo esquecimento derruba a
primeira requisicao com erro de conexao, que e o sintoma que se quer.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from app.db import transacao as banco
from app.db.repositorio import Repositorio, RepositorioSql

_substituto: Repositorio | None = None


@contextmanager
def atual() -> Iterator[Repositorio]:
    """O repositorio desta requisicao.

    Gerenciador de contexto, e nao valor direto como em `cache_do_processo`,
    porque o repositorio de verdade tem transacao: ela abre aqui e fecha na
    saida. Com o substituto nao ha o que abrir, e o `yield` entrega a mesma
    instancia — e o que faz o teste enxergar o que a requisicao escreveu.
    """
    if _substituto is not None:
        yield _substituto
        return

    with banco.transacao() as aberta:
        yield RepositorioSql(aberta)


def substituir(repositorio: Repositorio | None) -> None:
    """Troca o repositorio do processo. `None` devolve o SQL.

    Existe para o teste injetar o em memoria — e para o teste marcado tira-lo
    do caminho e falar com o Postgres de verdade.
    """
    global _substituto
    _substituto = repositorio
