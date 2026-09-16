import httpx
import pytest
import respx

from app import cache_do_processo
from app.services import noticias
from tests.fixtures_rss import FEED_AGENCIA_BRASIL, FEED_FAPESP, FEED_OBSERVATORIO


def resposta_de_feed(corpo: str) -> httpx.Response:
    """Uma resposta de RSS, com o `content-type` que os tres veiculos servem.

    Mora aqui porque os dois arquivos de teste das noticias precisam dela — o
    do agregador e o do endpoint —, e uma copia em cada divergiria no dia em
    que o `content-type` importasse.
    """
    return httpx.Response(
        200, text=corpo, headers={"content-type": "application/rss+xml; charset=utf-8"}
    )


def mockar_todos_os_feeds() -> None:
    """Mocka os tres feeds com as fixtures golden. Pede `@respx.mock` no teste."""
    respx.get(noticias.AGENCIA_BRASIL.url).mock(
        return_value=resposta_de_feed(FEED_AGENCIA_BRASIL)
    )
    respx.get(noticias.OBSERVATORIO_DO_CLIMA.url).mock(
        return_value=resposta_de_feed(FEED_OBSERVATORIO)
    )
    respx.get(noticias.PESQUISA_FAPESP.url).mock(
        return_value=resposta_de_feed(FEED_FAPESP)
    )


class Relogio:
    """Relogio injetado, avancado a mao.

    Todo teste de expiracao usa este: um que espera o TTL de verdade leva dez
    minutos, e um que encurta o TTL testa um valor que a producao nao usa.
    """

    def __init__(self) -> None:
        self.instante = 0.0

    def __call__(self) -> float:
        return self.instante

    def avancar(self, segundos: float) -> None:
        self.instante += segundos


@pytest.fixture
def anyio_backend():
    """Roda os testes assincronos so no asyncio, sem exigir trio instalado."""
    return "asyncio"


@pytest.fixture(autouse=True)
def cache_limpo():
    """Esvazia o cache do processo antes de cada teste.

    O cache e **estado de processo**: sem isto, a previsao que um teste deixa
    guardada e servida ao seguinte, que mockou outra resposta para a mesma
    coordenada. O sintoma seria uma falha que depende da ordem de execucao e
    some quando o teste roda sozinho.

    Autouse porque a armadilha atinge todo teste que bate em `/api/weather`,
    inclusive os que ainda nao existem — deixar a limpeza a cargo de quem
    escreve o teste seria confiar em que ninguem esquecera.
    """
    cache_do_processo.limpar()
