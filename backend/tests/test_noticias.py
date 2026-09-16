"""O agregador de RSS: parsing dos tres feeds, ordem e degradacao parcial.

O que se verifica aqui e a logica do modulo isolada da costura HTTP, como em
`test_inmet.py` — `respx` devolve as fixtures golden de `fixtures_rss.py` e
nada toca rede de verdade. `test_noticias_http.py` cobre o endpoint por cima
disto.

O caso que da nome ao modulo e o de **um feed fora do ar**: o ADR 0009 exige
que a agregacao ignore o que falhou e devolva o resto, e que "todos fora do ar"
seja distinguivel de "nenhuma noticia".
"""

import httpx
import pytest
import respx

from app import cache_do_processo
from app.services import noticias
from app.services.cache import TTL_DAS_NOTICIAS_SEGUNDOS, Cache
from tests.conftest import Relogio, mockar_todos_os_feeds, resposta_de_feed
from tests.fixtures_rss import (
    FEED_FAPESP,
    FEED_MALFORMADO,
    FEED_OBSERVATORIO,
    FEED_SEM_ITENS,
)

pytestmark = pytest.mark.anyio


@respx.mock
async def test_agrega_os_tres_feeds():
    mockar_todos_os_feeds()

    resultado = await noticias.buscar_noticias()

    assert resultado.status == "ok"
    # Dois itens por fixture, tres fixtures.
    assert len(resultado.noticias) == 6
    assert {item.veiculo for item in resultado.noticias} == {
        noticias.AGENCIA_BRASIL.veiculo,
        noticias.OBSERVATORIO_DO_CLIMA.veiculo,
        noticias.PESQUISA_FAPESP.veiculo,
    }


@respx.mock
async def test_ordem_cronologica_decrescente_atravessa_os_veiculos():
    """A mais recente primeiro, **misturando** os feeds.

    O item mais novo e do Observatorio (16 set) e o mais velho e da FAPESP
    (9 set): uma ordenacao que respeitasse a origem — os dois da Agencia
    Brasil, depois os dois do Observatorio — passaria por qualquer teste que
    so olhasse um feed. Por isso a asercao e sobre a lista inteira.
    """
    mockar_todos_os_feeds()

    resultado = await noticias.buscar_noticias()

    datas = [item.publicada_em for item in resultado.noticias]
    assert datas == sorted(datas, reverse=True)
    assert resultado.noticias[0].veiculo == noticias.OBSERVATORIO_DO_CLIMA.veiculo
    assert resultado.noticias[-1].veiculo == noticias.PESQUISA_FAPESP.veiculo


@respx.mock
async def test_offsets_diferentes_sao_comparados_como_instante():
    """`-0300` e `+0000` no mesmo feed agregado.

    Ordenar por texto poria "Mon, 14 Sep … -0300" antes de "Wed, 16 Sep …
    +0000" pela letra do dia da semana. As datas viram `datetime` com fuso, e
    a comparacao e de instante.
    """
    mockar_todos_os_feeds()

    resultado = await noticias.buscar_noticias()

    assert all(item.publicada_em.tzinfo is not None for item in resultado.noticias)


@respx.mock
async def test_um_feed_fora_do_ar_nao_derruba_a_resposta():
    """O caso central do ADR 0009: ignora o que falhou, devolve o resto."""
    respx.get(noticias.AGENCIA_BRASIL.url).mock(
        side_effect=httpx.ConnectError("sem rede")
    )
    respx.get(noticias.OBSERVATORIO_DO_CLIMA.url).mock(
        return_value=resposta_de_feed(FEED_OBSERVATORIO)
    )
    respx.get(noticias.PESQUISA_FAPESP.url).mock(
        return_value=resposta_de_feed(FEED_FAPESP)
    )

    resultado = await noticias.buscar_noticias()

    assert resultado.status == "ok"
    assert len(resultado.noticias) == 4
    assert noticias.AGENCIA_BRASIL.veiculo not in {
        item.veiculo for item in resultado.noticias
    }
    # O que caiu e nomeado: a pagina diz quais veiculos nao responderam em vez
    # de apresentar uma lista curta como se fosse a lista inteira.
    assert resultado.veiculos_fora_do_ar == [noticias.AGENCIA_BRASIL.veiculo]


@respx.mock
async def test_status_de_erro_conta_como_feed_fora_do_ar():
    """O 403 do CloudFront e o 500 do veiculo sao o mesmo caso que o timeout."""
    respx.get(noticias.AGENCIA_BRASIL.url).mock(return_value=httpx.Response(403))
    respx.get(noticias.OBSERVATORIO_DO_CLIMA.url).mock(
        return_value=resposta_de_feed(FEED_OBSERVATORIO)
    )
    respx.get(noticias.PESQUISA_FAPESP.url).mock(
        return_value=resposta_de_feed(FEED_FAPESP)
    )

    resultado = await noticias.buscar_noticias()

    assert resultado.status == "ok"
    assert resultado.veiculos_fora_do_ar == [noticias.AGENCIA_BRASIL.veiculo]


@respx.mock
async def test_todos_os_feeds_fora_do_ar_e_estado_distinto():
    """**Nao** e "nenhuma noticia": a interface precisa dizer coisas diferentes."""
    for feed in noticias.FEEDS:
        respx.get(feed.url).mock(side_effect=httpx.ConnectError("sem rede"))

    resultado = await noticias.buscar_noticias()

    assert resultado.status == "indisponivel"
    assert resultado.noticias == []
    assert resultado.veiculos_fora_do_ar == [feed.veiculo for feed in noticias.FEEDS]


@respx.mock
async def test_feeds_vazios_nao_sao_indisponibilidade():
    """O contraste do teste acima: responderam, e nao ha materia.

    Sem esta distincao, um dia calmo nos tres veiculos seria anunciado como
    falha — e o inverso, tres feeds fora do ar, como "sem noticias".
    """
    for feed in noticias.FEEDS:
        respx.get(feed.url).mock(return_value=resposta_de_feed(FEED_SEM_ITENS))

    resultado = await noticias.buscar_noticias()

    assert resultado.status == "ok"
    assert resultado.noticias == []
    assert resultado.veiculos_fora_do_ar == []


@respx.mock
async def test_xml_malformado_nao_derruba_o_agregador():
    """Um feed truncado cai como feed fora do ar, nao como `500`."""
    respx.get(noticias.AGENCIA_BRASIL.url).mock(
        return_value=resposta_de_feed(FEED_MALFORMADO)
    )
    respx.get(noticias.OBSERVATORIO_DO_CLIMA.url).mock(
        return_value=resposta_de_feed(FEED_OBSERVATORIO)
    )
    respx.get(noticias.PESQUISA_FAPESP.url).mock(
        return_value=resposta_de_feed(FEED_FAPESP)
    )

    resultado = await noticias.buscar_noticias()

    assert resultado.status == "ok"
    assert len(resultado.noticias) == 4
    assert resultado.veiculos_fora_do_ar == [noticias.AGENCIA_BRASIL.veiculo]


@respx.mock
async def test_resumo_da_agencia_brasil_perde_o_html_duplamente_escapado():
    """O `description` com `&lt;p&gt;` vira texto legivel, sem marcacao.

    E o pior dos tres formatos: HTML escapado duas vezes, com um logotipo e um
    `<p>` de centralizacao antes do texto. Sem a limpeza, o resumo comecaria
    com "<p><p style="text-align:center;">".
    """
    mockar_todos_os_feeds()

    resultado = await noticias.buscar_noticias()

    item = next(
        n for n in resultado.noticias if n.veiculo == noticias.AGENCIA_BRASIL.veiculo
    )

    assert item.resumo.startswith("Ao menos 152 famílias seguem em abrigos")
    for ruido in ("<", ">", "&lt;", "&quot;", "Logo Agência Brasil"):
        assert ruido not in item.resumo


@respx.mock
async def test_resumo_do_observatorio_perde_o_rodape_do_wordpress():
    """"O post … apareceu primeiro em …" nao e resumo da materia.

    Sem o corte, essa frase fecharia o resumo de **todos** os itens do
    Observatorio e da FAPESP, repetindo o nome do veiculo que a linha ao lado
    ja mostra.
    """
    mockar_todos_os_feeds()

    resultado = await noticias.buscar_noticias()

    item = next(
        n
        for n in resultado.noticias
        if n.veiculo == noticias.OBSERVATORIO_DO_CLIMA.veiculo
        and n.titulo.startswith("Entre enchentes")
    )

    assert item.resumo.startswith("Caderno eleitoral do OC pede maior proteção")
    assert "apareceu primeiro em" not in item.resumo


@respx.mock
async def test_resumo_limpo_da_fapesp_atravessa_intacto():
    """O controle: a limpeza nao pode estragar o que ja estava bom."""
    mockar_todos_os_feeds()

    resultado = await noticias.buscar_noticias()

    item = next(
        n for n in resultado.noticias if n.titulo == "Especial Jabuti Acadêmico"
    )

    assert item.resumo == (
        "José Goldemberg é homenageado no Jabuti Acadêmico. "
        "Veja outros destaques, além de eventos e livros"
    )


@respx.mock
async def test_entidades_do_titulo_sao_resolvidas():
    """`&#237;` vira `í` — o titulo e exibido, nao e codigo."""
    mockar_todos_os_feeds()

    resultado = await noticias.buscar_noticias()

    titulos = [item.titulo for item in resultado.noticias]
    assert "Chuvas deixam 152 famílias em abrigos no Vale do Ribeira (SP)" in titulos
    assert all("&#" not in titulo for titulo in titulos)


@respx.mock
async def test_o_link_e_o_do_veiculo_e_nao_o_guid():
    """O `guid` da Agencia Brasil **nao e URL** (`1702339 at https://…`).

    Um agregador que caisse no `guid` quando ele existe — pratica comum, ja que
    nos outros dois ele e a URL — produziria um link quebrado so nesse veiculo.
    """
    mockar_todos_os_feeds()

    resultado = await noticias.buscar_noticias()

    for item in resultado.noticias:
        assert item.link.startswith("https://")
    agencia = next(
        n for n in resultado.noticias if n.veiculo == noticias.AGENCIA_BRASIL.veiculo
    )
    assert agencia.link.startswith("https://agenciabrasil.ebc.com.br/meio-ambiente/")


@respx.mock
async def test_item_sem_data_ou_sem_link_e_descartado():
    """Um item incompleto sai da lista, sem derrubar os irmaos do mesmo feed.

    Descartar, e nao inventar: sem data ele nao tem lugar na ordem cronologica,
    e sem link a materia nao pode ser aberta — as duas coisas que a pagina
    promete de cada linha.
    """
    parcial = """<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>
    <item><title>Sem data</title><link>https://exemplo.test/a</link></item>
    <item><title>Sem link</title><pubDate>Mon, 14 Sep 2026 10:00:00 +0000</pubDate></item>
    <item><title>Completa</title><link>https://exemplo.test/c</link>
      <pubDate>Mon, 14 Sep 2026 11:00:00 +0000</pubDate></item>
    </channel></rss>"""
    respx.get(noticias.AGENCIA_BRASIL.url).mock(return_value=resposta_de_feed(parcial))
    respx.get(noticias.OBSERVATORIO_DO_CLIMA.url).mock(return_value=resposta_de_feed(FEED_SEM_ITENS))
    respx.get(noticias.PESQUISA_FAPESP.url).mock(return_value=resposta_de_feed(FEED_SEM_ITENS))

    resultado = await noticias.buscar_noticias()

    assert [item.titulo for item in resultado.noticias] == ["Completa"]
    # Um item ruim nao e um feed fora do ar: o veiculo respondeu.
    assert resultado.veiculos_fora_do_ar == []


@respx.mock
async def test_manda_user_agent_proprio():
    """O Observatorio do Clima responde **403** a quase todo `User-Agent`.

    Medido contra o servico real: o CloudFront a frente do `oc.eco.br` so
    aceita a forma `Mozilla/5.0 (compatible; …)` — recusa o padrao do httpx, o
    do curl e ate o mesmo nome sem o prefixo. Este caso fixa o valor para que
    uma simplificacao futura do cabecalho falhe aqui, e nao em producao como
    uma lista misteriosamente curta.
    """
    rota = respx.get(noticias.OBSERVATORIO_DO_CLIMA.url).mock(
        return_value=resposta_de_feed(FEED_OBSERVATORIO)
    )
    respx.get(noticias.AGENCIA_BRASIL.url).mock(return_value=resposta_de_feed(FEED_SEM_ITENS))
    respx.get(noticias.PESQUISA_FAPESP.url).mock(return_value=resposta_de_feed(FEED_SEM_ITENS))

    await noticias.buscar_noticias()

    enviado = rota.calls.last.request.headers["user-agent"]
    assert enviado == noticias.USER_AGENT
    # O que o filtro do CloudFront de fato le. Asercao separada do valor exato
    # para que o motivo sobreviva a uma troca de nome ou de versao.
    assert enviado.startswith("Mozilla/5.0 (compatible;")
    # E continua nomeando quem pede: o prefixo e sintaxe, nao disfarce.
    assert "PainelDeClima" in enviado


@respx.mock
async def test_a_segunda_consulta_vem_do_cache():
    """As noticias mudam em escala de horas; o TTL evita reconsultar a cada visita."""
    mockar_todos_os_feeds()

    primeira = await noticias.buscar_noticias()
    segunda = await noticias.buscar_noticias()

    assert [item.link for item in primeira.noticias] == [
        item.link for item in segunda.noticias
    ]
    # Uma rodada de tres chamadas, nao duas.
    assert respx.calls.call_count == len(noticias.FEEDS)


@pytest.fixture
def relogio():
    """Substitui o cache das noticias por um com relogio sob controle.

    Restaura o original ao fim, como em `test_cache_http.py`: o cache e estado
    de processo compartilhado, e deixar o relogio parado no lugar faria as
    noticias nunca expirarem nos testes seguintes.
    """
    relogio = Relogio()
    original = cache_do_processo.das_noticias()
    cache_do_processo.substituir_noticias(
        Cache(ttl_segundos=TTL_DAS_NOTICIAS_SEGUNDOS, agora=relogio)
    )
    yield relogio
    cache_do_processo.substituir_noticias(original)


@respx.mock
async def test_o_cache_das_noticias_dura_mais_que_o_da_previsao(relogio):
    """Meia hora, nao dez minutos — e o teste que prende o valor.

    O caso acima so prova que ha cache; este prova **qual**. Sem ele, trocar
    `das_noticias()` por `atual()` numa limpeza futura passaria despercebido: a
    pagina continuaria correta, so reconsultaria tres feeds a cada dez minutos
    para receber a mesma lista de volta.

    Com relogio injetado, como todo teste de expiracao deste projeto: um que
    espera meia hora de verdade leva meia hora.
    """
    mockar_todos_os_feeds()

    await noticias.buscar_noticias()

    # Onze minutos: o cache da previsao ja teria expirado aqui.
    relogio.avancar(660)
    await noticias.buscar_noticias()
    assert respx.calls.call_count == len(noticias.FEEDS)

    # Passada a meia hora, reconsulta.
    relogio.avancar(TTL_DAS_NOTICIAS_SEGUNDOS)
    await noticias.buscar_noticias()
    assert respx.calls.call_count == 2 * len(noticias.FEEDS)
