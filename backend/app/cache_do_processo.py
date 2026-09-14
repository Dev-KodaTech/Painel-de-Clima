"""O cache das consultas por coordenada, vivo enquanto o processo vive.

Mora fora dos servicos pela mesma razao que `dataset.py`: e **estado do
processo**, nao logica. `services/cache.py` define a mecanica do TTL e continua
uma classe pura, instanciavel quantas vezes um teste quiser; o que mora aqui e
a unica instancia que a aplicacao compartilha.

Separar os dois da ao teste **um** ponto de troca em vez de dois: quem precisa
de relogio sob controle substitui o que esta aqui, e quem so precisa comecar
limpo chama `limpar()`.

Cobre **apenas** as chamadas por coordenada. A busca por texto fica de fora de
proposito: dispara a cada tecla digitada, a chave seria o texto cru — "Ber",
"Berl", "Berli" sao tres entradas para a mesma cidade — e o conjunto de chaves
possiveis nao tem limite. E a chamada barata das duas, que nao arrasta previsao
junto.
"""

from app.services.cache import Cache

_cache = Cache()


def atual() -> Cache:
    """O cache em uso. Funcao, e nao a instancia exportada, para que
    `substituir` valha para quem ja importou o modulo."""
    return _cache


def substituir(cache: Cache) -> None:
    """Troca o cache do processo. Existe para o teste injetar um relogio."""
    global _cache
    _cache = cache


def limpar() -> None:
    """Esvazia o cache, sem troca-lo."""
    _cache.limpar()
