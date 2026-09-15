# 30: Página Tendência — histórico climatológico e métricas avançadas

**What to build:** a página `/tendencia`, hoje vazia, passa a ser a página de
análise do painel: histórico climatológico comparando a janela atual com o mesmo
período do ano anterior, métricas de chuva, umidade, vento e índice UV, e um
filtro temporal de 7 dias, 30 dias ou 6 meses.

**Blocked by:** —

**Status:** done

Origem: enunciado do usuário, mais três decisões de costura tomadas antes de
escrever a spec (endpoint próprio, Recharts, termo novo no glossário). Os
números de API abaixo foram **medidos** contra o serviço real em 2026-09-15, não
estimados — ver *Notas de investigação*.

## Problem Statement

O painel responde "como está o tempo agora e nos próximos sete dias". Não
responde nenhuma pergunta que exija olhar para trás ou para além de uma semana:

- **Este mês está fora do normal?** Não há com o que comparar. A pessoa vê 24 °C
  e não sabe se é quente para setembro naquela cidade.
- **Choveu muito este mês?** A precipitação existe no painel, mas só como sete
  barras diárias previstas. Não há acumulado, e sete dias não são um mês.
- **Como varia a umidade ao longo do dia? E o vento? E o UV?** Nenhum dos três
  existe no payload. O vento aparece uma única vez, como texto dentro do card de
  uma condição prevista ("Rajadas de 86 km/h"), e nunca como série.
- **E se eu quiser ver outro período?** Tudo é fixo: 24 horas no gráfico de
  tendência, 7 dias em todo o resto.

A página `/tendencia` já existe na barra lateral desde o [ticket 28](28-navegacao.md)
e hoje mostra só uma frase dizendo o que vai entrar ali.

## Solution

A página Tendência deixa de ser a versão em tela cheia dos cartões da Visão
geral e passa a ser a **página de análise**: o único lugar do app que olha para
trás.

Três partes, de cima para baixo:

1. **Filtro temporal** — 7 dias, 30 dias ou 6 meses. Escolhe a *janela temporal*
   que governa a página inteira; todo gráfico e toda métrica abaixo reagem a ele.
2. **Histórico climatológico** — a temperatura da janela escolhida sobreposta à
   do **mesmo período do ano anterior**, em duas séries no mesmo gráfico. É a
   comparação que responde "está fora do normal?".
3. **Métricas avançadas** — chuva acumulada em mm, variação da umidade, vento
   (velocidade e direção dominante) e índice UV, cada uma com o seu gráfico e o
   seu número de resumo.

Os dados do passado vêm da **API de arquivo** da Open-Meteo (reanálise ERA5), um
segundo endpoint do mesmo fornecedor, que o backend passa a consumir. Como todo
o resto, o frontend não fala com ela: quem chama é o backend, por um endpoint
novo e próprio.

## User Stories

### Janela temporal

1. Como visitante, quero escolher entre 7 dias, 30 dias e 6 meses, para analisar
   o período que me interessa em vez de um recorte fixo.
2. Como visitante, quero que a janela escolhida valha para a página inteira, para
   não precisar ajustar cada gráfico separadamente.
3. Como visitante, quero que a janela escolhida entre na URL, para compartilhar
   "Berlim, últimos 6 meses" como um link que abre exatamente isso.
4. Como visitante, quero que a janela sobreviva ao recarregar a página, pela
   mesma razão que a cidade sobrevive.
5. Como visitante que trocou de janela, quero ver que algo está carregando, para
   saber que o clique foi registrado.
6. Como visitante, quero que trocar de cidade preserve a janela que escolhi, para
   comparar duas cidades no mesmo período sem reconfigurar nada.
7. Como visitante, quero ver escrito o intervalo de datas que estou vendo, para
   saber que "30 dias" termina ontem e não hoje.

### Histórico climatológico

8. Como visitante, quero ver a temperatura da janela atual num gráfico, para
   perceber a tendência ao longo de semanas, não só de um dia.
9. Como visitante, quero ver sobreposta a temperatura do mesmo período do ano
   anterior, para julgar se o período atual está fora do normal.
10. Como visitante, quero que as duas séries sejam visualmente distinguíveis,
    para não confundir o ano passado com este.
11. Como visitante, quero passar o mouse sobre o gráfico e ver os valores dos
    dois anos naquela data, para comparar dia a dia sem estimar a olho.
12. Como visitante, quero ver a diferença média entre os dois períodos em números,
    para ter a conclusão sem precisar interpretar o gráfico.
13. Como visitante, quero que a comparação use a mesma data do calendário e não o
    mesmo dia da semana, para comparar setembro com setembro.
14. Como visitante numa cidade do hemisfério sul, quero que a comparação funcione
    igual, porque "mesmo período do ano anterior" não depende de estação.
15. Como visitante, quero saber quando o ano anterior não tem dado disponível,
    em vez de ver uma série sumir sem explicação.

### Métricas avançadas

16. Como visitante, quero ver quanto choveu acumulado na janela, em mm, para saber
    se o período foi seco ou chuvoso.
17. Como visitante, quero ver a chuva acumulada do ano anterior ao lado, para
    saber se este período foi mais seco que o normal.
18. Como visitante, quero ver a chuva distribuída ao longo da janela, para
    distinguir "choveu todo dia um pouco" de "choveu tudo num dia só".
19. Como visitante, quero ver quantos dias choveu na janela, porque 60 mm em três
    dias e 60 mm em vinte dias são períodos diferentes.
20. Como visitante, quero ver a variação da umidade do ar ao longo da janela,
    para entender o conforto do período.
21. Como visitante, quero ver a umidade mínima e máxima do período, para saber a
    amplitude e não só a média.
22. Como visitante, quero ver a velocidade do vento ao longo da janela, para
    identificar os períodos ventosos.
23. Como visitante, quero ver a direção dominante do vento, para saber de onde
    ele vem.
24. Como visitante, quero a direção do vento em pontos cardeais e não só em graus,
    porque "noroeste" se lê e "312°" se calcula.
25. Como visitante, quero ver o índice UV ao longo do dia, para saber a que horas
    a exposição ao sol é mais forte.
26. Como visitante, quero ver o índice UV classificado em faixas (baixo, moderado,
    alto, muito alto, extremo), para saber o que o número significa.
27. Como visitante, quero saber que o índice UV só existe para os próximos dias e
    não para o passado, em vez de ver um gráfico vazio sem explicação.
28. Como visitante, quero ver a unidade de toda métrica exibida, para não supor
    que a velocidade está em m/s.

### Estados e bordas

29. Como visitante que abriu a Tendência sem cidade escolhida, quero ser instruído
    a buscar uma, como em qualquer outra página.
30. Como visitante, quero uma mensagem compreensível quando o histórico não
    carrega, sem perder o resto da página que já carregou.
31. Como visitante numa cidade cujo arquivo é incompleto, quero ver os dias que
    existem, e não a página inteira falhar.
32. Como visitante, quero que a página carregue o histórico **só quando eu abri-la**,
    para que as outras cinco páginas não fiquem mais lentas por causa dela.
33. Como visitante que voltou para a Visão geral e retornou à Tendência, quero que
    o histórico não seja rebuscado, para a navegação ser instantânea.
34. Como visitante em tela estreita, quero que os gráficos continuem legíveis, para
    a página não ser exclusiva de desktop.
35. Como visitante de leitor de tela, quero que cada gráfico tenha um resumo em
    texto, porque uma série de 180 pontos não se lê ponto a ponto.
36. Como visitante, quero que os horários e datas sejam os da cidade consultada,
    pela mesma razão que valem no resto do painel.

### Operação e código

37. Como operador, quero que o histórico seja cacheado, para que trocar de janela
    e voltar não gaste cota da API externa.
38. Como operador, quero que o dado do ano anterior tenha vida mais longa no cache
    que o dado recente, porque o passado não muda.
39. Como desenvolvedor, quero um endpoint separado do painel, para que o custo do
    histórico não recaia sobre quem só abriu a Visão geral.
40. Como desenvolvedor, quero tipos que descrevam a resposta do histórico, para que
    um campo errado quebre na compilação.
41. Como desenvolvedor, quero que a janela temporal seja um conjunto fechado de
    valores, para que uma janela inválida seja rejeitada na borda e não vire uma
    requisição de dez anos à API externa.
42. Como desenvolvedor, quero testar a página pelo mesmo tipo de costura que já uso
    para o painel, para não inventar um segundo jeito de testar.

## Implementation Decisions

### A costura: um endpoint próprio

**`GET /api/trends`**, novo, separado de `/api/weather`. Parâmetros: a mesma
coordenada que o painel já usa (`latitude`, `longitude`) mais `janela`
(`7d` | `30d` | `6m`).

Engordar o `/api/weather` foi rejeitado: as outras cinco páginas leem o mesmo
`WeatherResponse` pela rota de layout ([ADR 0002](../../../docs/adr/0002-cidade-na-url.md)),
e um bloco histórico dentro dele faria a Visão geral esperar a chamada do
arquivo antes de pintar. O payload do painel tem ~3,5 KB; o histórico de 6 meses
com duas séries dobra isso, para dado que cinco das seis páginas nunca leem.

O frontend chamando `archive-api.open-meteo.com` direto também foi rejeitado:
contraria `CONTEXT.md` ("Só o backend fala com ela; o frontend nunca") e perde o
cache.

**Esta é a única costura nova do ticket.** A página lê a cidade do contexto do
`Shell`, como as outras; o que ela busca sozinha é só o histórico.

### Onde mora a requisição do histórico

**Na página**, não no `Shell`. É a exceção deliberada à regra do ADR 0002, e o
motivo é o que o próprio ADR usou para rejeitar a terceira opção: uma requisição
que toda troca de página refaz. Aqui vale o inverso — o `Shell` buscando o
histórico faria as seis páginas pagarem por ele.

A consequência a aceitar: sair da Tendência e voltar refaz a requisição. O cache
do backend absorve, e a história 33 é atendida por ele, não por estado no cliente.

### O contrato de `/api/trends`

Um bloco por parte da página, pelo mesmo princípio do payload do painel — cada
gráfico lê uma chave e não precisa saber de qual bloco da API externa o campo
veio:

- `periodo` — as datas de início e fim da janela atual e da janela do ano
  anterior, mais o rótulo da janela. Existe para a história 7: a interface não
  recalcula datas.
- `serie` — um ponto por dia da janela atual: data, máxima, mínima, chuva em mm,
  umidade média, velocidade máxima do vento, direção dominante.
- `comparacao` — a mesma forma, para o mesmo período do ano anterior. Lista vazia
  quando o arquivo não cobre o período (história 15).
- `uv` — separado das séries, e **não** é um campo de `serie`. Ver abaixo.
- `resumo` — os números prontos: chuva acumulada nos dois períodos, dias com
  chuva, umidade mínima/média/máxima, vento máximo, direção dominante em pontos
  cardeais, e a diferença média de temperatura entre os dois períodos.
- `units` — como no painel, para que a interface nunca tenha unidade escrita no
  código. Ganha `humidity` (`%`) e `uv` (sem unidade, é um índice).

O resumo é calculado **no backend**. Média, acumulado e contagem sobre 180 pontos
são a mesma operação para qualquer cliente, e mantê-la aqui evita que a página
reimplemente estatística.

**Direção dominante**: o backend converte graus em ponto cardeal (16 rumos) e
manda os dois — o grau para o gráfico, o rumo para o texto (história 24). A
conversão é circular: a média aritmética de 350° e 10° é 180°, que é o rumo
exatamente oposto ao correto. A média vetorial é obrigatória aqui.

### O índice UV não existe no passado

Medido contra o serviço real: `uv_index_max` é aceito pela API de arquivo e
devolve **`null` para todos os dias**, com unidade `"undefined"`. A reanálise
ERA5 não tem UV. Na API de previsão o mesmo campo devolve valores normais.

Consequência, que não é detalhe de implementação mas regra de produto: **o UV
nunca participa da comparação com o ano anterior, e nunca cobre 30 dias ou 6
meses.** Ele é exibido para a janela de previsão disponível (o dia corrente hora
a hora, e a máxima dos sete dias), com um rótulo dizendo por quê (história 27).

Por isso `uv` é um bloco irmão de `serie`, e não uma coluna dela: um campo dentro
de `serie` seria `null` em 173 dos 180 pontos, e todo consumidor teria de saber
disso. A forma do payload é que deve carregar o fato.

### As duas APIs da Open-Meteo

O cliente da API externa passa a conhecer **dois hosts**, não um:

| Host | Papel | Já usado? |
|---|---|---|
| `api.open-meteo.com` | previsão, UV, o painel inteiro | sim |
| `archive-api.open-meteo.com` | reanálise ERA5, o passado | **novo** |

Ambos são Open-Meteo e CC-BY 4.0, então a atribuição já existente continua
válida e não muda.

O arquivo **não tem lag relevante**: medido, cobre até o dia corrente
(2026-09-15 retornou dado para 2026-09-15). Isso dispensa a costura que seria
necessária se houvesse um vão de cinco dias entre o fim do arquivo e o início da
previsão — não há vão, e a janela atual sai inteira do arquivo.

**Duas chamadas ao arquivo, não uma**: uma para a janela atual, outra para o
mesmo período do ano anterior. A API aceita um único intervalo por requisição, e
pedir de setembro do ano passado até hoje traria 365 dias para usar 60.

### Custo, medido

| Janela | Bytes (uma chamada, 5 variáveis) |
|---|---|
| 6 meses, 3 variáveis | 5.471 |
| 6 meses, 5 variáveis | 7.041 |

A chamada mais cara da página — 6 meses, duas chamadas, cinco variáveis — pesa
~14 KB e responde em menos de 1 s. Não há aqui o dilema de banda que justificou
as duas chamadas do painel; o arquivo é barato.

### Cache

Reaproveita o cache em memória com TTL que já existe, com **duas famílias de
chave** e TTLs diferentes (história 38):

- janela atual: TTL de 10 minutos, o mesmo do painel — o dia corrente ainda muda.
- janela do ano anterior: TTL longo (24 h). O passado não muda; reconsultá-lo a
  cada 10 minutos gasta cota para receber os mesmos números.

A chave inclui a coordenada arredondada **e a janela**, pelo mesmo motivo que a
chave do painel inclui a coordenada: duas janelas da mesma cidade são consultas
diferentes.

O `Cache` atual recebe o TTL no construtor, não por chamada. Duas instâncias —
uma por TTL — é a mudança menor e não altera a mecânica já testada.

### Validação da janela

`janela` é um conjunto fechado (`7d`, `30d`, `6m`), validado na borda HTTP como
um `Literal`, do mesmo jeito que `Alerta.kind` já é. Um valor livre viraria
aritmética de data com entrada arbitrária, e "6000d" é uma requisição de dezesseis
anos à API externa. Valor fora do conjunto é `422`, pelo validador, sem código
nosso.

### Recharts

Entra como dependência do frontend, conforme pedido. ~100 KB gzip, contra zero
hoje.

Vale registrar o que isso cria, porque a decisão foi tomada de olhos abertos:
`TendenciaTemperatura.tsx` e `Precipitacao.tsx` continuam SVG desenhado à mão, e
o projeto passa a ter **dois vocabulários de gráfico**. A troca é consciente — a
página de análise precisa de tooltip, eixo duplo e legenda, que os SVGs atuais
não têm e que seriam trabalho manual considerável.

O que o Recharts **não** traz de graça e continua sendo nosso:

- **Nenhum timestamp passa por `new Date()`.** A regra de `formato.ts` vale
  igual: os timestamps são horário de parede da cidade, e o eixo do Recharts
  recebe texto já formatado por nós, nunca um `Date`.
- **Cores por variável CSS.** Os gráficos existentes usam `var(--color-brand)` e
  `var(--color-line)`, que é o que faz o tema escuro funcionar sem uma única
  variante `dark:` ([ticket 29](29-cidade-inicial-e-tema.md)). Cor literal no
  Recharts quebraria o tema escuro nesta página e só nela.
- **Responsividade.** `ResponsiveContainer` dentro da coluna de conteúdo, que já
  é `min-w-0` no `Shell` — sem isso a coluna cresce até caber o maior filho.

### Vocabulário novo

`CONTEXT.md` ganha dois termos, e a descrição da página Tendência em
`navegacao.tsx` é emendada (ela hoje promete "a tendência horária de temperatura
e a precipitação em tela cheia", que deixa de ser o que a página é):

**Histórico climatológico** — a série de dias passados de uma cidade, vinda da
reanálise, sempre apresentada em comparação com o mesmo período do ano anterior.
Distinto de *previsão*: um é medição do passado, o outro é modelo do futuro, e
misturá-los numa só série faria a fronteira entre medido e previsto desaparecer
no meio do gráfico. _Avoid_: histórico, passado, dados antigos.

**Janela temporal** — o período que a página Tendência analisa: 7 dias, 30 dias
ou 6 meses. É uma escolha da pessoa e governa a página inteira. Distinta dos
*sete dias* da previsão, que são fixos e não se escolhem. _Avoid_: período,
range, intervalo, filtro.

A palavra **Tendência** mantém o nome da página, mas o glossário passa a
registrar que ela nomeia a página de análise — e que o *painel* homônimo da
Visão geral (a curva horária de um dia) continua sendo outra coisa. Sem esse
registro, "tendência" repete o problema que o glossário desfez com "painel".

### Módulos

Backend:

- **Cliente da API externa** — ganha a chamada ao arquivo. Continua o único lugar
  que conhece o formato da Open-Meteo.
- **Histórico** (novo) — resolve a janela em datas, monta as duas chamadas e casa
  as duas séries.
- **Resumo** (novo) — os agregados e a média vetorial da direção do vento. Puro,
  sem rede.
- **Modelos** — os novos tipos do payload, como sempre espelhando 1:1.
- **Router** — o endpoint novo, com o mesmo tratamento de `OpenMeteoIndisponivel`
  que os dois existentes.

Frontend:

- **Página Tendência** — substitui a `PaginaVazia` na rota `/tendencia`. Trata os
  estados de carregamento e erro **dela**, sem interferir nos estados do painel
  que vêm do `Shell`.
- **Cliente da API** — `buscarTendencia`, ao lado de `buscarPainel`. Mesmo
  tratamento de erro, mesma tradução para `ErroDoPainel`.
- **Tipos** — espelhando o novo payload.
- **Formato** — as funções novas de exibição (rumo cardeal, faixa de UV,
  acumulado em mm).

## Testing Decisions

Um bom teste aqui verifica **o que sai da costura**, não como o módulo chegou
lá. Concretamente: nenhum teste espia o interior do cache, monta um `DataFrame`
intermediário ou verifica que uma função privada foi chamada.

A costura preferida é a que o repositório já usa: **`TestClient` + `respx`**,
batendo no endpoint HTTP com a API externa mockada, como `test_weather.py`. É a
costura mais alta disponível — exercita router, serviço, modelos e serialização
de uma vez, e continua válida se os módulos internos forem reorganizados.

### Testes de costura HTTP (o grosso)

Arquivo novo, irmão de `test_weather.py`, com fixtures novas em `fixtures.py`
gravadas do serviço real, incluindo as armadilhas:

- as três janelas produzem os intervalos de data corretos, inclusive a do ano
  anterior;
- a janela do ano anterior usa a mesma data de calendário;
- `janela` fora do conjunto fechado é `422`;
- arquivo sem dado para o ano anterior devolve `comparacao` vazia e a atual
  íntegra — não erro (história 15);
- `uv_index_max` vindo como `null` em todos os dias do arquivo **não** vira uma
  série de nulos no payload (a armadilha medida);
- série curta — arquivo incompleto — devolve os dias que existem (história 31);
- API externa fora do ar vira `503` com mensagem legível, como nos outros dois
  endpoints;
- o payload traz um bloco por parte da página, como `test_painel_traz_um_bloco_por_painel_da_interface`
  faz para o painel.

### Testes de unidade (só onde há regra própria)

Direção dominante e os agregados do resumo ganham teste direto, pelo mesmo
critério que deu teste próprio a `alertas` e `vizinhas`: são regra nossa, não
repasse de dado. O caso obrigatório é a média circular — 350° e 10° devem dar
0°/norte, e uma média aritmética daria 180°/sul. É o tipo de erro que passa
despercebido num teste de costura porque o número parece plausível.

### Cache

Estendendo `test_cache_http.py`, que já prova "duas consultas, uma chamada
externa" sem espiar o interior do cache. Acrescenta: janelas diferentes da mesma
cidade são chamadas diferentes, e o dado do ano anterior sobrevive ao TTL curto
(com o relógio injetado de `conftest.py`, nunca esperando de verdade).

### Contrato

`test_contract.py` ganha um caso para o arquivo, no mesmo estilo — verifica
presença de campo, nunca valor. **Inclusive o caso do UV nulo**: se um dia a
Open-Meteo passar a servir UV histórico, queremos saber, porque a regra de
produto muda junto.

### Frontend

Não há infraestrutura de teste no frontend hoje (sem vitest, sem nenhum
`*.test.tsx`). Este ticket **não** a introduz: montá-la é decisão de projeto que
merece ticket próprio, e enfiá-la aqui de carona faria este ticket entregar duas
coisas não relacionadas. A verificação do frontend é manual, contra as três
janelas e as bordas listadas nas histórias 29-36.

## Out of Scope

- **Exportar os dados** (CSV, PNG do gráfico). Nada no enunciado pede.
- **Janelas arbitrárias** ("de 3 de março a 12 de maio"). Três janelas fechadas
  são o que o enunciado pede, e são o que mantém a validação trivial.
- **Comparar com mais de um ano anterior**, ou com a normal climatológica de 30
  anos. Cada ano extra é mais uma chamada; a normal de 30 anos é outro produto.
- **Comparar duas cidades** na mesma tela. A página é sobre uma cidade, como
  todas as outras.
- **Migrar `TendenciaTemperatura` e `Precipitacao` para Recharts.** Decidido
  explicitamente: os dois vocabulários coexistem. Se essa migração for desejada,
  é ticket próprio, sem depender deste.
- **As outras quatro páginas vazias** (`/vizinhas`, `/condicoes`, `/semana`,
  `/ajustes`). Cada uma é ticket próprio.
- **Persistir a janela escolhida entre sessões.** Ela vai na URL, o que já atende
  compartilhar e recarregar; `localStorage` continua restrito à última cidade e
  ao tema, conforme a exceção estreita do [ticket 29](29-cidade-inicial-e-tema.md).
- **Infraestrutura de teste no frontend**, conforme acima.

## Further Notes

### Notas de investigação (medido em 2026-09-15, serviço real)

Quatro fatos que mudaram a spec, todos verificados contra a API e não supostos:

1. **O arquivo cobre até o dia corrente.** Consulta a 2026-09-15 devolveu dado
   para 2026-09-15. Eu esperava um lag de ~5 dias, que exigiria costurar o fim do
   arquivo com o início da previsão. Não é preciso.
2. **`uv_index_max` no arquivo devolve `null` sempre**, com `daily_units` igual a
   `"undefined"` — a resposta é `200`, não erro. É a armadilha central deste
   ticket: um consumidor desatento plota uma linha reta no zero e ninguém nota.
   Na API de previsão o mesmo campo devolve valores normais (`[3.55, 2.05, ...]`).
3. **Umidade, vento e direção existem no arquivo** como `relative_humidity_2m_mean`,
   `wind_speed_10m_max` e `wind_direction_10m_dominant`, com valores reais. Só o
   UV falta.
4. **6 meses de dado são baratos**: 7.041 bytes com cinco variáveis, resposta em
   menos de 1 s. O dilema de banda que levou o painel a fazer duas chamadas não
   se repete aqui.

### Sobre o nome do bloco `alerts`

Não muda nada aqui, mas vale a nota: a Tendência é a primeira página a exibir
vento como **série**, e não como texto dentro do card de uma condição prevista. A
tensão que o [ADR 0001](../../../docs/adr/0001-condicao-prevista-nao-e-alerta.md)
registrou continua contida — o vento na Tendência é medição, não aviso, e nenhum
rótulo de severidade acompanha esses gráficos.

### O que fica mais frágil depois deste ticket

O `Shell` continua sendo o único lugar que busca o painel, mas passa a **não ser
mais o único lugar que busca**. Quem acrescentar a sétima página vai encontrar
dois precedentes contraditórios e precisa saber qual seguir: dado que várias
páginas leem vai no `Shell`; dado que só uma página lê vai nela. A regra é essa,
e está escrita aqui porque o código sozinho não a contaria.


## Comments

### Implementação (2026-09-15)

Entregue como especificado. O que vale registrar:

**Uma correção de spec, medida.** A spec dizia que a ponta da janela deveria ser
"hoje na cidade consultada", estimado pela longitude. Isso quebra: em Wellington
(UTC+12) já é dia 16 enquanto o arquivo só vai até o dia 15 em UTC, e o arquivo
responde `400` — que chegava ao usuário como `503`, com a página inteira sem
abrir. A ponta foi ancorada em **UTC**, que é o calendário em que a reanálise é
publicada. Verificado ao vivo em Wellington, Honolulu e Berlim. Há teste de
regressão (`test_o_arquivo_nunca_e_pedido_alem_do_dia_corrente_em_utc`).

**Fora do previsto na spec**: o [ADR 0003](../../../docs/adr/0003-historico-e-buscado-na-pagina.md).
A spec previa a exceção ao ADR 0002 e escreveu a regra ("dado que várias páginas
leem vai no Shell; dado que só uma página lê vai nela") no corpo do ticket, mas
um ticket fechado não é onde a sétima página vai procurar. A regra virou ADR.

**Verificação do frontend** (manual, como a spec definiu): as três janelas, tema
claro e escuro, 1280 px e 420 px, sem cidade e com o backend fora do ar. Sem
erros de console em nenhum caso.

### Achados da revisão (`/code-review`, 2026-09-15)

Três bugs reais, todos confirmados contra o serviço antes de corrigir:

1. **O índice UV vinha vazio em Wellington.** A correção do fuso (acima) vazou
   para o filtro do UV: a janela termina no dia corrente em **UTC**, mas a
   previsão vem com `timezone=auto` e seus timestamps são horário de parede.
   Em UTC+12 as duas datas discordam e o filtro não casava com hora nenhuma —
   o painel inteiro ficava vazio. O dia do UV passa a vir da própria previsão,
   que é o único bloco da página que não vem do arquivo. Medido nas três
   cidades; há teste de regressão.

2. **As duas séries eram casadas por índice, não por data.** Funciona enquanto
   as duas listas vêm completas — e o contrato do ticket 31 prevê explicitamente
   série curta. Com um buraco na cabeça de qualquer uma delas, todo tooltip
   compararia setembro com agosto, e o desalinhamento seria **invisível**: as
   duas curvas continuariam plausíveis. Passa a casar por mês-dia.

3. **As duas janelas saíam com comprimentos diferentes em ano bissexto.** Recuar
   as duas pontas em separado parecia equivalente e não era: uma janela que
   atravessa 29 de fevereiro tem um dia a menos no ano anterior, quebrando o
   invariante de que a comparação depende. A ponta anterior passa a ser a única
   recuada, e o início é derivado dela. Verificado em ~3,3 anos de datas.

Além disso: `_Avoid_: período` no glossário era largo demais — proibia a palavra
para a *escolha* e para o *intervalo de datas*, que são coisas distintas e ambas
precisam de nome. A entrada foi reescrita para separar as duas (a janela é
"6 meses", o período é "17 mar — 15 set"), o que era a distinção que faltava.
Sem isso, o campo `periodo` do payload contradizia em silêncio a regra que este
próprio ticket adicionou.

Refatorações da revisão: moldura comum dos três painéis de métrica
(`PainelDeMetrica`), a série-por-dia extraída para `grafico.ts`, e a remoção de
um `as Janela` sobre texto — o furo que a união fechada existe para impedir.
