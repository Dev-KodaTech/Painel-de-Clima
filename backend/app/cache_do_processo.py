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

from app.services.cache import TTL_DO_PASSADO_SEGUNDOS, Cache

_cache = Cache()

#: Sao **duas instancias**, e nao uma com TTL por chamada: o `Cache` recebe o
#: TTL no construtor, e duas instancias e a mudanca menor — nao altera a
#: mecanica ja testada.
#:
#: O que separa as duas familias e se o dado ainda muda. O historico do ano
#: anterior nao muda mais; reconsulta-lo a cada dez minutos gasta cota para
#: receber os mesmos numeros de volta.
_cache_do_passado = Cache(ttl_segundos=TTL_DO_PASSADO_SEGUNDOS)


def atual() -> Cache:
    """O cache em uso. Funcao, e nao a instancia exportada, para que
    `substituir` valha para quem ja importou o modulo."""
    return _cache


def do_passado() -> Cache:
    """O cache do dado que nao muda mais: o historico do ano anterior."""
    return _cache_do_passado


def substituir(cache: Cache, passado: Cache | None = None) -> None:
    """Troca o cache do processo. Existe para o teste injetar um relogio.

    `passado` e opcional para que os testes que so olham a previsao nao
    precisem conhecer a segunda familia.
    """
    global _cache, _cache_do_passado
    _cache = cache
    if passado is not None:
        _cache_do_passado = passado


def limpar() -> None:
    """Esvazia os dois caches, sem troca-los."""
    _cache.limpar()
    _cache_do_passado.limpar()
