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

from app.services.cache import (
    TTL_DAS_NOTICIAS_SEGUNDOS,
    TTL_DO_PASSADO_SEGUNDOS,
    Cache,
)

_cache = Cache()

#: Sao **duas instancias**, e nao uma com TTL por chamada: o `Cache` recebe o
#: TTL no construtor, e duas instancias e a mudanca menor — nao altera a
#: mecanica ja testada.
#:
#: O que separa as duas familias e se o dado ainda muda. O historico do ano
#: anterior nao muda mais; reconsulta-lo a cada dez minutos gasta cota para
#: receber os mesmos numeros de volta.
_cache_do_passado = Cache(ttl_segundos=TTL_DO_PASSADO_SEGUNDOS)

#: A terceira familia: as noticias. Entrou pelo mesmo criterio que separou as
#: duas primeiras — **a escala em que o dado muda** —, e nao por ser mais um
#: fornecedor. A previsao muda a cada quinze minutos, o passado nao muda mais, e
#: uma materia publicada e um evento que nao se repete.
#:
#: Se uma quarta aparecer, o criterio continua sendo este. O que nao deve
#: acontecer e uma instancia por endpoint: duas chamadas com a mesma escala
#: compartilham a mesma familia, como a previsao e as vizinhas ja fazem.
_cache_das_noticias = Cache(ttl_segundos=TTL_DAS_NOTICIAS_SEGUNDOS)


def atual() -> Cache:
    """O cache em uso. Funcao, e nao a instancia exportada, para que
    `substituir` valha para quem ja importou o modulo."""
    return _cache


def do_passado() -> Cache:
    """O cache do dado que nao muda mais: o historico do ano anterior."""
    return _cache_do_passado


def das_noticias() -> Cache:
    """O cache das noticias, com TTL de meia hora."""
    return _cache_das_noticias


def substituir(cache: Cache, passado: Cache | None = None) -> None:
    """Troca o cache do processo. Existe para o teste injetar um relogio.

    `passado` e opcional para que os testes que so olham a previsao nao
    precisem conhecer a segunda familia.
    """
    global _cache, _cache_do_passado
    _cache = cache
    if passado is not None:
        _cache_do_passado = passado


def substituir_noticias(cache: Cache) -> None:
    """Troca o cache das noticias. Existe para o teste injetar um relogio.

    Funcao propria, e nao um terceiro parametro de `substituir`: quem testa a
    expiracao das noticias nao tem previsao nenhuma a trocar junto, e a
    assinatura com tres opcionais deixaria de dizer qual delas se esta
    exercitando.
    """
    global _cache_das_noticias
    _cache_das_noticias = cache


def limpar() -> None:
    """Esvazia os tres caches, sem troca-los.

    **Toda familia nova entra aqui.** Esquecer uma faz a entrada guardada por
    um teste ser servida ao seguinte, e o sintoma e uma falha que depende da
    ordem de execucao e some quando o teste roda sozinho — exatamente o que a
    fixture `cache_limpo` existe para impedir.
    """
    _cache.limpar()
    _cache_do_passado.limpar()
    _cache_das_noticias.limpar()
