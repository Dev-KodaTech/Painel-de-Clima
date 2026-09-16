"""A sessao: o identificador que viaja no cookie, e a politica do cookie.

O que mora aqui e a regra; quem guarda a linha e o repositorio, e quem fala
HTTP e o router. Ver ADR 0005 para por que a sessao e um cookie com linha no
banco e nao um JWT.

O **relogio entra por parametro**, como ja entra no cache: um teste de
expiracao que esperasse a duracao de verdade levaria sete dias, e um que
encurtasse a duracao testaria um valor que a producao nao usa.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from app.config import em_desenvolvimento

#: O nome do cookie. Uma constante porque tres lugares o escrevem — a resposta
#: do cadastro, a leitura de "quem sou" e, no ticket seguinte, a saida — e tres
#: literais divergiriam no dia em que um fosse renomeado.
NOME_DO_COOKIE = "sessao"

#: Quanto uma sessao dura. Sete dias atende "continuar entrada ao voltar
#: depois" sem que uma sessao esquecida num computador emprestado valha para
#: sempre.
DURACAO = timedelta(days=7)

#: Bytes de entropia do identificador. 32 bytes e o que `secrets` recomenda
#: para um token que vale como credencial; em base64 cabem nos 64 caracteres da
#: coluna.
BYTES_DO_IDENTIFICADOR = 32


def novo_identificador() -> str:
    """Um identificador de sessao imprevisivel.

    `secrets`, e nao `random`: o `random` e um Mersenne Twister semeado de
    forma previsivel, e quem observasse alguns identificadores poderia prever
    os seguintes — que aqui significa entrar na conta de outra pessoa.
    """
    return token_urlsafe(BYTES_DO_IDENTIFICADOR)


def _relogio_do_sistema() -> datetime:
    """O instante atual, **com fuso**.

    Ingenuo levantaria na comparacao com `expira_em`, que vem do banco com
    fuso — e, pior, compararia errado no SQL de quem roda em outro fuso.
    """
    return datetime.now(timezone.utc)


#: O relogio em uso. Trocavel pelo teste, como o do cache: verificar expiracao
#: com o relogio de verdade custaria sete dias de espera, e encurtar a duracao
#: para o teste provaria que um valor que a producao nao usa funciona.
_relogio: Callable[[], datetime] = _relogio_do_sistema


def agora() -> datetime:
    """O instante atual, segundo o relogio em uso."""
    return _relogio()


def substituir_relogio(relogio: Callable[[], datetime] | None) -> None:
    """Troca o relogio do processo. `None` devolve o do sistema."""
    global _relogio
    _relogio = _relogio_do_sistema if relogio is None else relogio


def expira_em(instante: datetime) -> datetime:
    """Quando expira uma sessao aberta neste instante."""
    return instante + DURACAO


def esta_valida(expira_em: datetime, instante: datetime) -> bool:
    """Se uma sessao que expira nesse momento ainda vale agora."""
    return expira_em > instante


def cookie_seguro() -> bool:
    """Se o cookie leva a flag `Secure`.

    Ligado em toda parte menos em desenvolvimento, onde o `http://localhost`
    nao devolveria um cookie `Secure` e ninguem conseguiria entrar. Quem le a
    variavel e `config.py`, como nas outras duas configuracoes do projeto.
    """
    return not em_desenvolvimento()
