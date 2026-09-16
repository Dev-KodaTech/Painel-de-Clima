# Alertas do INMET pelo JSON e por ponto-em-polígono, não pelo CAP

Os alertas oficiais vêm de `GET https://apiprevmet3.inmet.gov.br/avisos/ativos`,
sem chave. A decisão que merece registro não é *usar o INMET* — é ter escolhido o
endpoint JSON proprietário em vez do CAP 1.2, que é o padrão internacional e a
escolha que um leitor futuro esperaria.

## Por que não o CAP

O INMET publica CAP 1.2 de verdade em `/avisos/rss/{id}`, um alerta por
requisição. Parecia o caminho certo: formato padronizado, parser de prateleira,
portável para outras fontes no futuro.

**O CAP do INMET não traz `<geocode>`.** Nenhum — verificado nos avisos ativos. A
lista de municípios vai num `<parameter>` como texto corrido, que não é
machine-readable. O JSON proprietário deles traz `geocodes` (códigos IBGE) *e*
`poligono`. O padrão, neste caso, carrega menos estrutura que o formato próprio.

Além disso o CAP custa uma requisição por alerta, e acrescenta só `urgency`,
`certainty` e `responseType` — campos que a interface não usa. Se um dia usarmos,
o caminho é buscar o CAP sob demanda para os alertas que já sabemos aplicáveis,
não trocar a fonte principal.

O `/avisos/rss` (sem id) não é alternativa: é RSS 2.0 com uma tabela HTML dentro
de CDATA.

## Por que polígono e não os códigos de município

Os dois vêm no payload, e os dois funcionam — foram testados um contra o outro, e
concordam: para o aviso 55733, o ponto-em-polígono coloca Curitiba dentro e São
Paulo fora, e os `geocodes` dizem o mesmo.

O polígono ganha por ser autocontido. Usar `geocodes` exigiria manter uma tabela
coordenada → município do IBGE, que é um segundo dado para versionar, atualizar e
errar. O app já sabe a coordenada da cidade escolhida; ray casting sobre um
`Polygon` simples não precisa de mais nada. Todos os avisos observados são
`Polygon`, não `MultiPolygon`.

## Consequences

**O cliente do INMET não usa o `AsyncClient` injetado.** O servidor anuncia ALPN
mas não negocia HTTP/2 e derruba a conexão: sem forçar HTTP/1.1, a requisição
falha com connection reset. Isso diverge do padrão de injeção do `open_meteo.py`,
e a divergência é deliberada — a peculiaridade é de um fornecedor e fica
encapsulada no módulo que fala com ele. Sem o comentário explicando, alguém
"limpa" isso e quebra a integração de um jeito difícil de diagnosticar.

**Fora do Brasil, a ausência de alerta é uma afirmação que não podemos fazer.** A
API não recebe coordenada: devolve sempre o conjunto nacional, e o filtro é
nosso. Uma coordenada em Buenos Aires resulta em lista vazia, indistinguível de
"nenhum aviso ativo". Por isso a consulta só acontece quando `country_code` é
`BR`, e fora disso a interface diz que não há cobertura em vez de dizer que não
há alerta. Tratar os dois como o mesmo estado seria afirmar segurança sobre uma
região da qual não temos dado.

**O feed é nacional e o cache é uma entrada só.** São ~270 KB que servem todas as
cidades brasileiras, então a chave é fixa e não derivada de coordenada — o
primeiro uso do `cache.py` que não indexa por lat/lon.

**Falha do INMET não derruba a página.** A seção de alertas informa que não foi
possível consultar; as condições previstas continuam. Um fornecedor secundário
não pode levar junto a funcionalidade principal, e cair em silêncio para lista
vazia seria a mesma falsa afirmação de segurança descrita acima.

**A severidade máxima nunca foi observada.** `Perigo Potencial` (6) e `Perigo`
(7) foram vistos ao vivo; `Grande Perigo` não estava ativo. O valor 8 e sua cor
são presumidos, o fixture correspondente é sintético, e isso está marcado no
código — é o tipo de suposição que passa despercebida até o dia em que importa.

**A atribuição deixa de ser uma constante única.** A licença do INMET pede que se
cite a fonte, mas creditá-lo no rodapé de Wellington seria impreciso. Cada
endpoint passa a montar a sua, e `ATRIBUICAO` vira função.
