"""Trechos dos tres feeds RSS, gravados dos servicos reais.

Fixtures **golden**: sao o XML como os veiculos o servem, reduzido a dois itens
cada e com o corpo das materias cortado, mas sem nenhuma normalizacao. As
armadilhas de formato foram preservadas de proposito, porque sao justamente o
que o agregador existe para absorver:

- **Agencia Brasil**: `description` com HTML **duas vezes escapado**
  (`&lt;p&gt;`), precedido de um logotipo em `<img>` e de um `<p>` de
  centralizacao. O texto que interessa esta dentro de um `<strong>`, depois de
  ~400 caracteres de marcacao. O `guid` **nao e URL** (`1702339 at https://…`),
  entao nao serve de link. Traz `<imagem-destaque>`, elemento fora de qualquer
  namespace declarado.
- **Observatorio do Clima**: CDATA com o rodape do WordPress — "O post <a…>
  apareceu primeiro em <a…>Observatorio do Clima</a>" — colado no fim de toda
  materia. Sem corte, esse rodape entraria no resumo de todos os dez itens.
- **Pesquisa FAPESP**: o unico `description` limpo dos tres. Serve de controle:
  se a limpeza estragar este, estragou um texto que ja estava bom.

Os tres usam `pubDate` em RFC 822, e **os offsets divergem** (`-0300` na
Agencia Brasil, `+0000` nos outros dois) — e o que obriga a ordenacao a
comparar instantes, nunca texto.
"""

#: Agencia Brasil, editoria meio-ambiente. Dois itens, o HTML duplamente
#: escapado mantido tal como chega.
FEED_AGENCIA_BRASIL = """<?xml version="1.0" encoding="utf-8" ?><rss version="2.0" xml:base="https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml/424656" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Feed Editoria</title>
    <link>https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml/424656</link>
    <description></description>
    <language>pt-br</language>
     <atom:link href="https://agenciabrasil.ebc.com.br/rss/424656/feed.xml" rel="self" type="application/rss+xml" />
      <item>
    <title>Chuvas deixam 152 fam&#237;lias em abrigos no Vale do Ribeira (SP)</title>
    <link>https://agenciabrasil.ebc.com.br/meio-ambiente/noticia/2026-09/chuvas-deixam-152-familias-em-abrigos-no-vale-do-ribeira-sp</link>
    <imagem-destaque>https://imagens.ebc.com.br/x/1170x700/smart/foto.jpg?itok=QNjC90g0</imagem-destaque>    <description>  &lt;p&gt;&lt;p style=&quot;text-align:center;&quot;&gt;&lt;a class=&quot;&quot; href=&quot;https://agenciabrasil.ebc.com.br/meio-ambiente/noticia/2026-09/chuvas-deixam-152-familias-em-abrigos-no-vale-do-ribeira-sp&quot;&gt;
                    &lt;img src=&quot;https://cdn.jsdelivr.net/gh/sergiosdlima/assets-ebc@1.0.0/abr/assets/images/logo-agenciabrasil.svg&quot; alt=&quot;Logo Ag&#234;ncia Brasil&quot; style=&quot;height: 54px;&quot;&gt;
\t\t\t\t&lt;/a&gt;&lt;/p&gt;&lt;strong&gt;Ao menos 152 fam&#237;lias seguem em abrigos tempor&#225;rios na regi&#227;o do Vale do Ribeira, sul do estado de S&#227;o Paulo, ap&#243;s fortes chuvas atingirem a regi&#227;o entre sexta-feira (11) e domingo (13), causando inunda&#231;&#245;es e transbordamento de rios.&lt;/strong&gt;&lt;img src=&quot;https://agenciabrasil.ebc.com.br/ebc.png?id=1702339&amp;amp;o=rss&quot; style=&quot;width:1px; height:1px; display:inline;&quot; /&gt;&lt;/p&gt;</description>
    <pubDate>Mon, 14 Sep 2026 21:52:00 -0300</pubDate>
    <dc:creator>Ag&#234;ncia Brasil</dc:creator>
    <guid isPermaLink="false">1702339 at https://agenciabrasil.ebc.com.br</guid>
  </item>
      <item>
    <title>Ibama aprova plano de emerg&#234;ncia para a Bacia da Foz do Amazonas</title>
    <link>https://agenciabrasil.ebc.com.br/meio-ambiente/noticia/2026-09/ibama-aprova-plano-de-emergencia</link>
    <description>  &lt;p&gt;&lt;strong&gt;O Ibama aprovou o plano de prote&#231;&#227;o &#224; fauna apresentado pela Petrobras.&lt;/strong&gt;&lt;/p&gt;</description>
    <pubDate>Sun, 13 Sep 2026 10:02:00 -0300</pubDate>
    <guid isPermaLink="false">1702001 at https://agenciabrasil.ebc.com.br</guid>
  </item>
  </channel>
</rss>
"""

#: Observatorio do Clima. O rodape "O post … apareceu primeiro em …" fecha a
#: `description` dos dois itens, como no feed real.
FEED_OBSERVATORIO = """<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"
\txmlns:content="http://purl.org/rss/1.0/modules/content/"
\txmlns:dc="http://purl.org/dc/elements/1.1/"
\txmlns:atom="http://www.w3.org/2005/Atom"
\t>
<channel>
\t<title>Observat&#243;rio do Clima</title>
\t<atom:link href="https://oc.eco.br/feed/" rel="self" type="application/rss+xml" />
\t<link>https://oc.eco.br/</link>
\t<description>Site oficial do OC | Observat&#243;rio do clima</description>
\t<lastBuildDate>Wed, 16 Sep 2026 15:48:35 +0000</lastBuildDate>
\t<language>pt-BR</language>
\t<item>
\t\t<title>Entre enchentes e secas, clima desafia gest&#227;o da &#225;gua no Brasil</title>
\t\t<link>https://oc.eco.br/entre-enchentes-e-secas-clima-desafia-gestao-da-agua-no-brasil/</link>
\t\t<dc:creator><![CDATA[Aldem Bourscheit]]></dc:creator>
\t\t<pubDate>Wed, 16 Sep 2026 15:47:23 +0000</pubDate>
\t\t<category><![CDATA[Not&#237;cias]]></category>
\t\t<category><![CDATA[mudan&#231;as clim&#225;ticas]]></category>
\t\t<guid isPermaLink="false">https://oc.eco.br/?p=42283</guid>
\t\t<description><![CDATA[<p>Caderno eleitoral do OC pede maior prote&ccedil;&atilde;o de rios e aqu&iacute;feros, controle dos usos da &aacute;gua e prepara&ccedil;&atilde;o efetiva para secas e inunda&ccedil;&otilde;es</p>
<p>O post <a href="https://oc.eco.br/entre-enchentes-e-secas-clima-desafia-gestao-da-agua-no-brasil/">Entre enchentes e secas, clima desafia gest&atilde;o da &aacute;gua no Brasil</a> apareceu primeiro em <a href="https://oc.eco.br">Observat&oacute;rio do Clima</a>.</p>
]]></description>
\t</item>
\t<item>
\t\t<title>Desmatamento na Amaz&#244;nia cai pelo terceiro ano seguido</title>
\t\t<link>https://oc.eco.br/desmatamento-na-amazonia-cai-pelo-terceiro-ano-seguido/</link>
\t\t<pubDate>Mon, 14 Sep 2026 09:15:00 +0000</pubDate>
\t\t<guid isPermaLink="false">https://oc.eco.br/?p=42210</guid>
\t\t<description><![CDATA[<p>Queda de 11% consolida a tend&ecirc;ncia iniciada em 2023, segundo dados do Inpe.</p>
<p>O post <a href="https://oc.eco.br/desmatamento-na-amazonia-cai-pelo-terceiro-ano-seguido/">Desmatamento na Amaz&ocirc;nia cai pelo terceiro ano seguido</a> apareceu primeiro em <a href="https://oc.eco.br">Observat&oacute;rio do Clima</a>.</p>
]]></description>
\t</item>
</channel>
</rss>
"""

#: Revista Pesquisa FAPESP. O `link` traz os parametros `utm_*` com `&#038;`,
#: como o WordPress os escreve.
FEED_FAPESP = """<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"
\txmlns:content="http://purl.org/rss/1.0/modules/content/"
\txmlns:dc="http://purl.org/dc/elements/1.1/"
\txmlns:atom="http://www.w3.org/2005/Atom"
\t>
<channel>
\t<title>Revista Pesquisa Fapesp</title>
\t<atom:link href="https://revistapesquisa.fapesp.br/feed/" rel="self" type="application/rss+xml" />
\t<link>https://revistapesquisa.fapesp.br</link>
\t<description>Revista Pesquisa Fapesp</description>
\t<language>pt-BR</language>
\t<item>
\t\t<title>Especial Jabuti Acad&#234;mico</title>
\t\t<link>https://revistapesquisa.fapesp.br/especial-jabuti-academico/?utm_source=rss&#038;utm_medium=rss</link>
\t\t<dc:creator><![CDATA[Marcelo Soares]]></dc:creator>
\t\t<pubDate>Fri, 11 Sep 2026 12:03:43 +0000</pubDate>
\t\t<category><![CDATA[Not&#237;cias]]></category>
\t\t<guid isPermaLink="false">https://revistapesquisa.fapesp.br/?p=577054</guid>
\t\t<description><![CDATA[Jos&eacute; Goldemberg &eacute; homenageado no Jabuti Acad&ecirc;mico. Veja outros destaques, al&eacute;m de eventos e livros]]></description>
\t</item>
\t<item>
\t\t<title>Oceano mais quente muda a rota dos cardumes</title>
\t\t<link>https://revistapesquisa.fapesp.br/oceano-mais-quente/?utm_source=rss</link>
\t\t<pubDate>Wed, 09 Sep 2026 12:44:50 +0000</pubDate>
\t\t<guid isPermaLink="false">https://revistapesquisa.fapesp.br/?p=576900</guid>
\t\t<description><![CDATA[Pesquisa acompanhou a sardinha no Atl&acirc;ntico Sul por seis anos]]></description>
\t</item>
</channel>
</rss>
"""

#: XML que o parser nao consegue ler: a tag `<item>` nunca fecha e o documento
#: termina no meio. Um feed servindo isto nao pode derrubar o agregador — e um
#: dos tres modos de falha que o ADR 0009 exige absorver, ao lado do erro de
#: rede e do status de erro.
FEED_MALFORMADO = """<?xml version="1.0" encoding="UTF-8"?><rss version="2.0">
<channel>
\t<title>Feed truncado</title>
\t<item>
\t\t<title>Materia que nunca fecha
"""

#: RSS valido e sem item nenhum. Distinto do malformado: aqui o veiculo
#: **respondeu certo**, so nao tem materia — nao e falha, e nao deve contar
#: como feed fora do ar.
FEED_SEM_ITENS = """<?xml version="1.0" encoding="UTF-8"?><rss version="2.0">
<channel>
\t<title>Veiculo sem materias</title>
\t<link>https://exemplo.test/</link>
</channel>
</rss>
"""
