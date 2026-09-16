# Página Condições e página Notícias

Status: ready-for-agent

Origem: sessão de grilling + domain-modeling. Decisões registradas em
[ADR 0007](../../docs/adr/0007-alerta-oficial-e-condicao-prevista-coexistem.md),
[ADR 0008](../../docs/adr/0008-inmet-por-json-e-poligono.md) e
[ADR 0009](../../docs/adr/0009-noticias-por-rss-nao-por-api.md).

## Problem Statement

A barra lateral oferece "Condições previstas" e a página não existe. A frase
promete "as condicoes severas derivadas da previsao, sem o limite de dois cards
do painel", e — como já aconteceu com Cidades vizinhas — **a promessa é falsa**.

Tirar o limite de dois cards não revela lista nenhuma. O `derivar()` em
`backend/app/services/alertas.py` deduplica para **um card por categoria**, e as
categorias são três. Removido o teto, o resultado máximo é três itens, e o
detalhe por dia já foi colapsado dentro de `also_days: int`. Não há o que
destravar.

Há um problema maior por trás. Todo aviso de tempo severo do app é **derivado por
nós** de limiares sobre a previsão. Nenhum vem de autoridade, nenhum traz
recomendação de segurança, e o
[ADR 0001](../../docs/adr/0001-condicao-prevista-nao-e-alerta.md) construiu todo
um vocabulário para impedir que sejam confundidos com alerta — porque alerta é a
categoria em que pessoas tomam decisão de segurança, e a nossa não é.

O que falta na página Condições não é uma lista mais longa. É o alerta de
verdade.

## Solution

**A página Condições**, com duas seções separadas e rotuladas:

**Alertas oficiais** — os avisos do INMET que cobrem a cidade escolhida, com
severidade oficial, janela de validade, riscos e recomendações de segurança. Só
no Brasil; fora dele a seção declara que não há cobertura, e nunca que não há
alerta.

**Condições previstas** — um item **por dia que dispara**, sem o dedup por
categoria e sem o teto de dois. É o que faz "lista cronológica" significar
alguma coisa: a semana de Wellington vira cinco itens de vento com datas reais,
em vez de um card dizendo "(+4 dias)".

**A página Notícias**, separada — matérias de clima e meio ambiente de três
feeds RSS públicos, nacionais, cada uma com o seu veículo.

A renomeação de `alerts` para `condicoes` no payload é pré-requisito do resto,
pela condição de revogação que o próprio ADR 0001 declarou.

## User Stories

### Condições previstas

1. Como visitante, quero abrir a página Condições pela barra lateral, para ver os avisos de tempo severo da cidade escolhida.
2. Como visitante, quero ver um item para **cada dia** que dispara uma condição, para saber quais dias são afetados e não só quantos.
3. Como visitante, quero ver os itens em ordem cronológica, para planejar a semana.
4. Como visitante, quero ver o valor que disparou cada condição, para julgar a gravidade em vez de confiar no rótulo.
5. Como visitante, quero ver em cada card que aquilo é derivado da previsão, para não confundir com aviso oficial.
6. Como visitante numa semana calma, quero uma mensagem clara de que não há condição severa, para não achar que a página falhou.

### Alertas oficiais

7. Como visitante no Brasil, quero ver os alertas do INMET que cobrem a minha cidade, para saber o que a autoridade meteorológica está avisando.
8. Como visitante, quero ver a severidade oficial de cada alerta, para distinguir Perigo Potencial de Grande Perigo.
9. Como visitante, quero ver a severidade nas cores oficiais do INMET, para reconhecer o mesmo código que vejo no noticiário.
10. Como visitante, quero ver a janela de validade de cada alerta, para saber quando começa e quando termina.
11. Como visitante, quero ver os riscos descritos pelo INMET, para entender o que pode acontecer.
12. Como visitante, quero abrir as recomendações de segurança de um alerta, para saber o que fazer.
13. Como visitante, quero que as recomendações comecem recolhidas, para conseguir ler a lista de alertas sem rolar por parágrafos repetidos.
14. Como visitante, quero ver que o alerta é do INMET, para saber que é oficial e não nosso.
15. Como visitante, quero ver os telefones de emergência junto da seção, para não precisar procurá-los em outro lugar.
16. Como visitante fora do Brasil, quero ver que não há cobertura de alertas oficiais na minha região, e **não** que não há alertas.
17. Como visitante, quero que a página continue útil quando o INMET estiver fora do ar, para não perder também as condições previstas.
18. Como visitante, quero que a falha de consulta ao INMET seja declarada, para não interpretar a ausência como segurança.
19. Como visitante no Brasil sem alertas ativos, quero uma mensagem de que não há alertas para a região, para distinguir de falha.
20. Como visitante, quero que as duas seções sejam visivelmente distintas, para não confundir o que é oficial com o que é nosso.
21. Como visitante na Visão geral, quero que um alerta oficial apareça no painel, para não precisar abrir a página para descobrir que existe.

### Notícias

22. Como visitante, quero abrir a página Notícias pela barra lateral, para ler novidades sobre clima e meio ambiente.
23. Como visitante, quero ver as notícias em ordem cronológica, para ler as mais recentes primeiro.
24. Como visitante, quero ver o veículo de cada notícia, para julgar o que estou lendo.
25. Como visitante, quero ver a data de cada notícia, para saber se é atual.
26. Como visitante, quero abrir a notícia no site do veículo, para ler a matéria completa.
27. Como visitante, quero que a página funcione quando um dos feeds estiver fora do ar, para não perder as notícias dos outros.

### Transversais

28. Como visitante sem cidade escolhida, quero uma instrução para buscar uma, em vez de uma página vazia ou quebrada.
29. Como visitante, quero ver o estado de carregamento, para saber que algo está acontecendo.
30. Como visitante, quero ver o crédito das fontes usadas naquela página, para saber de onde vem o que estou lendo.
31. Como visitante no tema escuro, quero que as duas páginas acompanhem o tema, inclusive as cores de severidade.
32. Como visitante de teclado, quero expandir e recolher as recomendações sem mouse.
33. Como visitante com leitor de tela, quero que a severidade seja anunciada como texto, e não apenas por cor.

## Implementation Decisions

**`alerts` vira `condicoes`.** Pré-requisito, não preferência — ADR 0007. Toca o
contrato da API, o painel da Visão geral, os tipos do frontend e a suíte de
testes. É a fatia 01, isolada de propósito.

**A página busca o próprio dado.** Endpoint novo `GET /api/condicoes`, buscado na
página. Segue a regra do
[ADR 0003](../../docs/adr/0003-historico-e-buscado-na-pagina.md): só uma página
lê, então vai nela. Sai quase de graça — a previsão já está no cache de 10
minutos que `/api/weather` acabou de popular.

**Os limiares não mudam.** Os mesmos 60 km/h, 20 mm e códigos WMO de tempestade,
com a calibração medida que já está documentada em `alertas.py`. Afrouxá-los para
esta página faria o mesmo dia ser severo aqui e calmo na Visão geral.

**O INMET entra pelo JSON, filtrado por ponto-em-polígono.** ADR 0008. Cliente
próprio com HTTP/1.1 forçado, dedup de `hoje`+`futuro` por `id`, duplo parse de
`poligono`. Consulta só quando `country_code` é `BR`.

**Notícias por RSS agregado.** ADR 0009. Nenhuma API de notícias tem nível
gratuito utilizável em produção.

**Notícias são página própria.** Não são sobre a cidade escolhida; o resto do app
é. Ver o verbete *Notícia* no `CONTEXT.md`.

**A frase da barra lateral muda junto.** Regra do
[ADR 0006](../../docs/adr/0006-vizinhas-e-comparacao-nao-lista-longa.md), escrita
depois que uma frase prometeu o que a página não entregava. É o mesmo erro que
esta feature está corrigindo — não repetir.

**A atribuição vira função.** Hoje `ATRIBUICAO` é constante única em
`models.py:34`. INMET e veículos aparecem em algumas páginas e não em outras.

## Riscos registrados

- **`Grande Perigo` (id_severidade 8) nunca foi observado** — nenhum estava ativo
  durante a investigação. O valor e a cor são presumidos; o fixture é sintético e
  precisa dizer isso.
- **O feed do INMET é estado do mundo**, não dado estável: os fixtures golden
  envelhecem, e um teste de contrato marcado é o que avisa quando o formato muda.
- **A licença do INMET é ambígua** — `<copyright>public domain</copyright>`
  convive com "desde que citada a fonte". Creditamos: é a leitura segura.
- **Três feeds de dez itens** — a página Notícias é pequena e depende de
  terceiros.
