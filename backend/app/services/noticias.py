"""Agregador dos feeds RSS de noticias de clima e meio ambiente.

Unico lugar do backend que conhece o formato dos feeds, no mesmo espirito de
`open_meteo.py` e `inmet.py`. Por que RSS e nao uma API de noticias — e os
numeros da verificacao — esta no
[ADR 0009](../../../docs/adr/0009-noticias-por-rss-nao-por-api.md).

Tres coisas separam este cliente dos outros dois:

1. **Falha parcial e o caminho normal, nao a excecao.** O INMET fora do ar
   deixa `/api/condicoes` sem alertas e pronto; aqui sao tres fornecedores
   independentes, e o ADR 0009 exige que um deles ausente nao tire a pagina do
   ar. Por isso a funcao publica nao levanta: devolve um `Agregado` que diz
   **quais** veiculos nao responderam.
2. **`User-Agent` proprio, e num formato especifico.** Medido contra o servico
   real: o CloudFront a frente do `oc.eco.br` responde **403** ao
   `python-httpx/…` e a qualquer UA que nao comece por `Mozilla/5.0
   (compatible; …)`. Sem o cabecalho certo, um dos tres veiculos simplesmente
   nunca apareceria — e o sintoma seria uma lista curta, nao um erro. Ver
   `USER_AGENT`, que documenta o que foi testado.
3. **XML de terceiros, sem versao nem contrato.** O ADR 0009 ja aceita a
   consequencia: feeds quebram e mudam de formato sem aviso. Todo parsing aqui
   trata a ausencia de campo como item descartado, nunca como excecao que sobe.

Sem filtro regional, de proposito: as noticias sao nacionais e sao
apresentadas como tais. A alternativa — casar o nome do estado no titulo —
esvaziaria a lista quase sempre e faria a mesma materia aparecer para uma
cidade e sumir para outra por acaso de redacao (ADR 0009).
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
from xml.etree import ElementTree

import httpx

from app import cache_do_processo

# `StatusDasNoticias` vem de `models`, e nao e redefinido aqui: e o mesmo
# arranjo de `StatusDosAlertas`, que mora em `models.py` e e importado por
# `services/weather.py`. Dois `Literal` identicos em dois arquivos divergiriam
# no dia em que um terceiro estado aparecesse.
from app.models import Noticia, StatusDasNoticias

#: Quem se identifica ao pedir o feed.
#:
#: **O prefixo `Mozilla/5.0 (compatible; …)` e obrigatorio, e foi medido.** O
#: CloudFront a frente do `oc.eco.br` responde 403 a qualquer coisa fora dessa
#: forma: `PainelDeClima/1.0 (…)` e ate `curl/8.7.1` sao recusados, e
#: `PainelDeClima/1.0 Mozilla/5.0` tambem — o token tem de vir na frente. Nao e
#: o nome que o filtro le, e o formato.
#:
#: A forma `(compatible; Nome/Versao)` e a convencao de robo educado, a mesma
#: que buscadores usam: passa no filtro **e** continua nomeando quem esta
#: pedindo. Nao ha aqui nenhum navegador, sistema ou motor inventado — o que se
#: declara e verdade, so escrita na sintaxe que o fornecedor aceita.
#:
#: **Nao simplifique este valor numa limpeza futura.** Tirar o prefixo apaga um
#: dos tres veiculos da pagina, e o sintoma seria uma lista permanentemente
#: curta, nao um erro. `test_noticias.py` fixa o valor, e o teste de contrato
#: bate no feed real.
USER_AGENT = "Mozilla/5.0 (compatible; PainelDeClima/1.0; +agregador de RSS)"

#: Dez segundos, como no INMET. Os tres feeds sao paginas estaticas de alguns
#: kilobytes; o que este limite protege e o caso do servidor que aceita a
#: conexao e nunca responde — sem ele, a pagina inteira ficaria pendurada no
#: veiculo mais lento.
TIMEOUT = httpx.Timeout(10.0)


@dataclass(frozen=True)
class Feed:
    """Um veiculo e o endereco do seu feed.

    `veiculo` e o nome que a interface credita, e nao o `<title>` do canal: o
    da Agencia Brasil e "Feed Editoria", que nao diz a ninguem quem publicou.
    A licenca pede credito, e um credito so cumpre o seu papel se nomear quem
    de fato escreveu (ADR 0009).
    """

    veiculo: str
    url: str


AGENCIA_BRASIL = Feed(
    veiculo="Agência Brasil",
    url="https://agenciabrasil.ebc.com.br/rss/meio-ambiente/feed.xml",
)
OBSERVATORIO_DO_CLIMA = Feed(
    veiculo="Observatório do Clima",
    url="https://www.oc.eco.br/feed/",
)
PESQUISA_FAPESP = Feed(
    veiculo="Pesquisa FAPESP",
    url="https://revistapesquisa.fapesp.br/feed/",
)

#: Os tres feeds, nesta ordem. A ordem **nao** governa a lista exibida, que e
#: cronologica; governa so a ordem em que os veiculos fora do ar sao nomeados,
#: para que a mensagem de falha seja estavel entre requisicoes.
FEEDS = (AGENCIA_BRASIL, OBSERVATORIO_DO_CLIMA, PESQUISA_FAPESP)

#: A chave fixa do cache. Como no INMET, e pela mesma razao: a consulta e
#: nacional e nao tem parametro nenhum — nao ha coordenada a incorporar, porque
#: nao ha filtro regional (ADR 0009).
CHAVE_DE_CACHE = "noticias:rss"

#: Quantos itens a pagina traz, do conjunto ja ordenado.
#:
#: Os feeds trazem 10, 10 e 30 itens; sem teto, a FAPESP dominaria metade de
#: uma lista de cinquenta. Trinta e o suficiente para uma pagina de leitura, e o
#: corte vem **depois** da ordenacao — os mais recentes de qualquer veiculo.
MAXIMO_DE_ITENS = 30

@dataclass(frozen=True)
class Agregado:
    """O que a agregacao produziu, com a procedencia da lista junto.

    A lista sozinha e ambigua — vazia por calmaria ou por falha, curta por
    haver pouca materia ou por um veiculo fora do ar. Os campos ao lado dela
    sao o que torna cada caso legivel por quem exibe.

    **Distinto de `NoticiasResponse`, e nao um duplicado dele.** Os dois se
    parecem hoje, mas a resposta carrega `attribution` — texto pronto para
    exibir — e este modulo nao sabe nem deve saber como se credita um veiculo.
    Devolver `NoticiasResponse` daqui faria o agregador montar a linha de
    credito, que e decisao de payload, e o router viraria um repassador. E a
    mesma fronteira que `open_meteo.py` mantem ao devolver `dict` cru em vez de
    `WeatherResponse`.
    """

    noticias: list[Noticia]
    status: StatusDasNoticias
    #: Os veiculos que nao responderam, na ordem de `FEEDS`. Vazio no caminho
    #: normal. Nomeados, e nao contados: "o Observatorio do Clima nao
    #: respondeu" diz a quem le por que a lista esta curta, e "1 veiculo fora
    #: do ar" nao diz.
    veiculos_fora_do_ar: list[str]
    #: Os que responderam — o complemento exato do campo acima.
    #:
    #: Os **dois**, e nao um so com o outro derivado: quem credita precisa da
    #: lista positiva (creditar quem nao forneceu nada seria impreciso) e quem
    #: avisa precisa da negativa. Deriva-las uma da outra em dois lugares
    #: diferentes e o que faz as duas discordarem no dia em que um terceiro
    #: estado aparecer.
    veiculos_que_responderam: list[str]


async def buscar_noticias() -> Agregado:
    """As noticias dos tres feeds, em ordem cronologica decrescente.

    **Nao levanta.** E a diferenca central em relacao a `inmet.py` e a
    `open_meteo.py`: com tres fornecedores independentes, a falha de um e um
    resultado a relatar, nao um erro a propagar (ADR 0009). Quem chama nunca
    precisa de `try`; le `status` e `veiculos_fora_do_ar`.

    Cache **proprio**, e nao o das consultas por coordenada: aquele tem TTL de
    dez minutos, calibrado no ciclo de atualizacao da previsao, e serviria para
    reconsultar tres feeds a cada dez minutos para receber a mesma lista de
    volta. Noticia muda em escala de horas. Ver `TTL_DAS_NOTICIAS_SEGUNDOS`.
    """
    return await cache_do_processo.das_noticias().obter(CHAVE_DE_CACHE, _buscar)


async def _buscar() -> Agregado:
    async with httpx.AsyncClient(
        timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}, follow_redirects=True
    ) as client:
        # Em paralelo, e nao em sequencia: tres feeds a 10 s de timeout cada
        # somariam 30 s de espera no pior caso, e o pior caso e justamente o
        # que esta pagina precisa atravessar bem.
        resultados = await asyncio.gather(
            *(_buscar_feed(client, feed) for feed in FEEDS)
        )

    noticias: list[Noticia] = []
    fora_do_ar: list[str] = []
    # A lista positiva e guardada aqui, e nao recalculada por quem credita: e
    # esta varredura que sabe quem respondeu, e reconstrui-la depois filtrando
    # `FEEDS` contra a lista negativa seria derivar duas vezes o que se soube
    # uma.
    responderam: list[str] = []
    for feed, itens in zip(FEEDS, resultados):
        if itens is None:
            fora_do_ar.append(feed.veiculo)
            continue
        responderam.append(feed.veiculo)
        noticias.extend(itens)

    noticias.sort(key=lambda item: item.publicada_em, reverse=True)

    return Agregado(
        noticias=noticias[:MAXIMO_DE_ITENS],
        # `indisponivel` exige que **todos** tenham falhado. Dois fora do ar
        # ainda e `ok` com uma lista curta e dois veiculos nomeados — a pagina
        # tem o que mostrar, e diz o que falta.
        status="indisponivel" if len(fora_do_ar) == len(FEEDS) else "ok",
        veiculos_fora_do_ar=fora_do_ar,
        veiculos_que_responderam=responderam,
    )


async def _buscar_feed(client: httpx.AsyncClient, feed: Feed) -> list[Noticia] | None:
    """Os itens de um feed, ou `None` se ele nao pode ser lido.

    `None`, e nao lista vazia: sao os dois casos que o ADR 0009 proibe
    colapsar. Um feed que responde sem materia devolve `[]` e nao entra em
    `veiculos_fora_do_ar`; um que falha devolve `None` e entra.

    As tres formas de falhar caem aqui juntas porque produzem o mesmo efeito
    para quem le — rede, status de erro e XML que o parser recusa. A ultima e a
    que o ADR previu ao aceitar "parsing de XML de terceiros": um feed truncado
    no meio e um `ParseError`, nao um `HTTPError`.
    """
    try:
        response = await client.get(feed.url)
        response.raise_for_status()
        return _itens_do_xml(response.text, feed.veiculo)
    except (httpx.HTTPError, ElementTree.ParseError):
        return None


def _itens_do_xml(corpo: str, veiculo: str) -> list[Noticia]:
    """Os `<item>` de um documento RSS, ja convertidos.

    Varre com `iter`, e nao pelo caminho `channel/item`: os tres feeds sao RSS
    2.0 sem namespace nos elementos que importam, mas um deles declara quatro
    namespaces no `<rss>` e a Agencia Brasil ainda inclui um elemento proprio
    (`<imagem-destaque>`). `iter("item")` atravessa isso sem depender da forma
    exata da arvore.
    """
    raiz = ElementTree.fromstring(corpo)
    itens = [_para_noticia(item, veiculo) for item in raiz.iter("item")]
    # Os `None` sao os itens incompletos — sem data ou sem link. Descartados um
    # a um: um item defeituoso nao diz nada sobre os irmaos do mesmo feed, e
    # jogar o feed inteiro fora por causa dele perderia nove materias boas.
    return [item for item in itens if item is not None]


def _para_noticia(item: ElementTree.Element, veiculo: str) -> Noticia | None:
    """Um `<item>` como a interface o consome, ou `None` se incompleto.

    Data e link sao obrigatorios, e a razao e a mesma para os dois: sao o que a
    pagina promete de cada linha. Sem data o item nao tem lugar na ordem
    cronologica — e adivinha-la como "agora" o poria no topo, acima de materia
    de verdade. Sem link a linha nao leva a lugar nenhum.

    **O link vem de `<link>`, nunca do `<guid>`.** Nos feeds do WordPress o
    `guid` e uma URL e a tentacao de usa-lo como reserva e grande; na Agencia
    Brasil ele e `1702339 at https://agenciabrasil.ebc.com.br`, que produziria
    um link quebrado num veiculo so.
    """
    link = _texto(item.find("link"))
    publicada_em = _data(_texto(item.find("pubDate")))
    if link is None or publicada_em is None:
        return None

    return Noticia(
        titulo=_texto(item.find("title")) or "(sem titulo)",
        veiculo=veiculo,
        link=link,
        publicada_em=publicada_em,
        resumo=_resumo(_texto(item.find("description"))),
    )


def _texto(elemento: ElementTree.Element | None) -> str | None:
    """O texto de um elemento, ja sem espaco nas bordas, ou `None`.

    O parser resolve as entidades XML (`&#237;`, `&amp;`) e o conteudo de
    CDATA sozinho — o que sobra escapado e o HTML **dentro** do texto, que
    `_resumo` trata.
    """
    if elemento is None or elemento.text is None:
        return None
    texto = elemento.text.strip()
    return texto or None


def _data(bruta: str | None) -> datetime | None:
    """A `pubDate` RFC 822 como `datetime` com fuso, ou `None`.

    **Com fuso, sempre.** Os tres feeds divergem no offset — `-0300` na Agencia
    Brasil, `+0000` nos outros dois —, e e por isso que a ordenacao compara
    `datetime` e nao o texto: por letra, "Mon, 14 Sep" viria antes de "Wed, 16
    Sep". Uma data ingenua na mistura levantaria `TypeError` na comparacao, e
    seria um `500` causado por um veiculo que so escreveu a data de outro
    jeito.
    """
    if bruta is None:
        return None
    try:
        data = parsedate_to_datetime(bruta)
    except (TypeError, ValueError):
        return None
    return data if data.tzinfo is not None else None


#: O rodape que o WordPress cola no fim de toda `description`: "O post <a>…</a>
#: apareceu primeiro em <a>Veiculo</a>." Presente no Observatorio do Clima e na
#: Pesquisa FAPESP. Nao e resumo da materia — repete o titulo e o veiculo, que
#: a linha ao lado ja mostra.
_RODAPE_DO_WORDPRESS = re.compile(r"O post\b.*?apareceu primeiro em\b.*$", re.S)

#: Uma tag HTML qualquer. O `description` dos tres feeds e HTML: a Agencia
#: Brasil o serve **duas vezes escapado**, e os outros dois dentro de CDATA.
_TAG_HTML = re.compile(r"<[^>]*>")

#: Espaco em branco repetido, incluindo as quebras de linha que sobram quando as
#: tags saem.
_ESPACO_REPETIDO = re.compile(r"\s+")

#: Onde o resumo e cortado. Duas linhas de texto numa lista: o suficiente para
#: decidir se a materia interessa, que e tudo o que um resumo precisa fazer
#: quando o titulo ja esta logo acima.
_LIMITE_DO_RESUMO = 280


def _resumo(bruto: str | None) -> str:
    """O `description` como texto corrido, sem HTML e sem rodape.

    Os tres veiculos servem HTML aqui, em tres formatos diferentes, e a ordem
    das operacoes importa:

    1. `unescape` **duas vezes**, por causa da Agencia Brasil: la o corpo chega
       como `&lt;p&gt;`, ou seja, HTML escapado dentro de XML — o parser
       desfez uma camada e sobrou a outra. Nos outros dois a segunda passada
       nao tem o que fazer, porque CDATA ja entrega o HTML cru.
    2. Tirar as tags. So depois do passo 1: antes dele, o HTML da Agencia
       Brasil ainda e texto comum e nenhuma regex de tag o alcanca.
    3. `unescape` de novo, para as entidades que estavam **dentro** do texto
       (`&nbsp;`, `&ccedil;`) e que so agora ficaram expostas.
    4. Cortar o rodape do WordPress e normalizar o espaco.

    O que sai da Agencia Brasil ainda comeca depois de um logotipo e de um
    `<p>` de centralizacao — isso some no passo 2, junto com os `<img>` de
    rastreamento de 1x1 pixel que o feed carrega.
    """
    if bruto is None:
        return ""

    texto = unescape(unescape(bruto))
    texto = _TAG_HTML.sub(" ", texto)
    texto = unescape(texto)
    texto = _RODAPE_DO_WORDPRESS.sub("", texto)
    texto = _ESPACO_REPETIDO.sub(" ", texto).strip()

    if len(texto) <= _LIMITE_DO_RESUMO:
        return texto
    # Corta na palavra, e nao no caractere: um resumo terminando em "inunda"
    # parece dado corrompido, e nao texto abreviado.
    cortado = texto[:_LIMITE_DO_RESUMO].rsplit(" ", 1)[0]
    return f"{cortado}…"
