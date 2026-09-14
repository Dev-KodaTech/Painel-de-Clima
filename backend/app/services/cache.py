"""Cache em memoria com TTL, para nao repetir consulta a API externa.

A fonte atualiza a cada ~15 minutos: consultar a mesma cidade duas vezes em
dez minutos devolveria o mesmo dado, gastando cota e latencia. Um dicionario
com timestamp basta — **sem Redis**, que acrescentaria um servico para guardar
alguns kilobytes que podem ser perdidos sem consequencia alguma.

O relogio e **injetado**. Nao por gosto de abstracao, mas porque o TTL de dez
minutos so e testavel assim: um teste que espera a expiracao de verdade leva
dez minutos, e um que encurta o TTL testa um valor que a producao nao usa.
"""

import time
from collections.abc import Awaitable, Callable
from typing import Any

#: Dez minutos, alinhado ao ciclo de atualizacao da fonte (~15 min). Um TTL
#: maior serviria dado perceptivelmente velho; um menor gastaria cota para
#: receber os mesmos numeros de volta.
TTL_PADRAO_SEGUNDOS = 600


class Cache:
    """Guarda valores por chave, ate o TTL expirar.

    Nao tem limite de tamanho nem despejo por pressao de memoria: a chave e uma
    coordenada arredondada e cada entrada pesa poucos kilobytes, entao mesmo
    milhares de cidades distintas cabem folgadamente. Entradas expiradas somem
    quando a mesma chave e consultada de novo.

    Nao ha travamento entre requisicoes concorrentes pela mesma chave: duas
    consultas simultaneas a uma cidade fria fazem duas chamadas externas em vez
    de uma. E o que custa menos — um lock assincrono por chave traria
    coordenacao e risco de deadlock para economizar uma requisicao de uma cota
    de 10.000 diarias.
    """

    def __init__(
        self,
        ttl_segundos: float = TTL_PADRAO_SEGUNDOS,
        agora: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_segundos
        self._agora = agora
        #: chave -> (instante em que foi guardado, valor)
        self._entradas: dict[str, tuple[float, Any]] = {}

    async def obter(self, chave: str, buscar: Callable[[], Awaitable[Any]]) -> Any:
        """O valor de `chave`, do cache ou de `buscar()`.

        `buscar` so e chamada quando nao ha entrada valida — e o que torna
        "duas consultas, uma chamada externa" observavel sem espiar o interior
        do cache.

        Assincrona porque o que se cacheia sao chamadas de rede, e nao ha outro
        tipo de chamador. Uma variante sincrona so existiria para os testes
        usarem, e exercitaria um caminho que a producao nunca roda.

        `buscar` e uma **fabrica** de corrotinas, nao uma corrotina: recebe-la
        pronta faria o chamador cria-la mesmo na consulta servida do cache, e
        uma corrotina nunca aguardada e um aviso do runtime.
        """
        guardado = self._guardado(chave)
        if guardado is not None:
            return guardado

        valor = await buscar()
        # Guardado **depois** da chamada: se `buscar` levantar, nada e gravado
        # e a proxima consulta tenta de novo. Cachear uma falha prenderia o
        # painel numa indisponibilidade passageira por dez minutos.
        self._entradas[chave] = (self._agora(), valor)
        return valor

    def limpar(self) -> None:
        """Esvazia o cache. Existe para o teste comecar de um estado conhecido."""
        self._entradas.clear()

    def _guardado(self, chave: str) -> Any | None:
        """O valor valido de `chave`, ou `None` se falta ou expirou.

        `None` nunca e um valor guardado legitimo aqui: o que se cacheia sao
        respostas da API externa, que sao dicionarios ou listas.
        """
        entrada = self._entradas.get(chave)
        if entrada is None:
            return None

        guardado_em, valor = entrada
        if self._agora() - guardado_em >= self._ttl:
            del self._entradas[chave]
            return None

        return valor


#: Casas decimais da coordenada na chave do cache.
#:
#: Duas casas sao ~1,1 km no equador — abaixo da celula de grade que a propria
#: API externa usa, que devolve a coordenada arredondada em vez da pedida. Sem
#: o arredondamento, `52.52437` e `52.5244` (a mesma cidade vinda de duas
#: candidatas com precisao diferente) seriam entradas distintas e o cache
#: erraria justamente no caso que existe para servir.
CASAS_DA_CHAVE = 2


def chave_de_coordenada(prefixo: str, *coordenadas: float) -> str:
    """A chave de cache de uma ou mais coordenadas.

    O `prefixo` separa consultas diferentes sobre a **mesma** coordenada: a
    previsao completa da cidade e o tempo atual das vizinhas partem de lat/lon
    e devolvem coisas distintas. Sem ele, uma sobrescreveria a outra.
    """
    partes = ",".join(f"{valor:.{CASAS_DA_CHAVE}f}" for valor in coordenadas)
    return f"{prefixo}:{partes}"
