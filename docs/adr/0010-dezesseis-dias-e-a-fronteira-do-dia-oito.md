# Dezesseis dias, não trinta, e o dia 8 é uma fronteira visível

A página Calendário foi pedida com "previsão detalhada para os próximos 15 ou 30
dias". Ela mostra **16**, que é o teto do endpoint que o app já usa, e desenha
uma fronteira no dia 8, a partir da qual os dias aparecem com menos precisão
declarada — sem ícone de céu e sem aptidão.

Trinta dias não foi recusado por limite técnico. **É possível sem chave**, e a
ausência desse parágrafo faria a próxima pessoa reabrir a questão achando que
ninguém procurou.

## O que existe, e por que nenhuma das duas serve

`forecast_days` aceita no máximo 16 em `api.open-meteo.com/v1/forecast`. Acima
disso a API recusa:

```
forecast_days=30 → {"error":true,"reason":"Forecast days is invalid. Allowed range 0 to 16."}
```

Há dois caminhos para ir além, ambos sem chave e livres para uso não comercial:

- **`ensemble-api.open-meteo.com/v1/ensemble`** — 35 dias, `models=gfs05`, 31
  membros, com agregados diários.
- **`seasonal-api.open-meteo.com/v1/seasonal`** — 183 dias, 50 membros, ECMWF
  SEAS5.

O ensemble foi o candidato sério para os 30 dias, e falha por duas razões
independentes:

**Não tem `weather_code`.** A grade do app é feita de ícone por dia, e o ícone
sai do código WMO. Uma tira de 30 dias pelo ensemble não conseguiria desenhar o
que os 7 dias já desenham — seria outra coisa, visualmente pior, no mesmo lugar.

**A resolução cai para ~50 km**, contra os 2–11 km do ICON que serve a primeira
semana. O dado do dia 25 não é o dado do dia 2 com mais incerteza; é um dado de
outra granularidade espacial.

## O motivo de fundo: aos 30 dias não há o que prever

Medido no ensemble sazonal, São Paulo, dia 30, `temperature_2m_max` entre os 50
membros:

```
mínimo 19,0 °C   máximo 35,3 °C   desvio-padrão 4,5 °C
```

Uma faixa de 16 °C. Imprimir um número só naquela célula esconde a incerteza
inteira e apresenta ruído como sinal — que é exatamente o que o
[ADR 0001](0001-condicao-prevista-nao-e-alerta.md) construiu vocabulário para
impedir, do outro lado do mesmo problema. O app que se recusa a chamar de
*alerta* uma condição que ninguém assinou não pode imprimir um ícone de sol
confiante para 16 de outubro.

A literatura é consistente com a medida: a skill determinística decai até a
climatologia por volta do **dia 10–14**, e para precipitação — campo menor e
mais caótico — colapsa antes, por volta do **dia 7–10**.

A Open-Meteo, vale registrar, **serve 16 dias e em nenhum lugar afirma que eles
são bons**. Procuramos: a documentação principal, a do GFS e o blog. A afirmação
mais forte encontrada é *"after 3 days of forecasts, weather models diverge
noticeably"*. A ausência de qualquer promessa sobre o dia 14 é, ela mesma, o
achado.

## A fronteira do dia 8 não é estética: é troca de modelo

A Open-Meteo não documenta o encadeamento de modelos do `best_match`. Foi
descoberto comparando `best_match` com cada modelo, em Paris,
`temperature_2m_max`:

```
dias  0–7 : best_match == icon_seamless   (idêntico)
dias  8–14: best_match ≈ ecmwf_ifs025     (|dif| ≤ 0,3 °C)
dia  15   : best_match == gfs_seamless    (idêntico)
```

ICON (2–11 km) até o dia 7, ECMWF IFS 0,25° (~25 km) do 8 ao 15, GFS no 16. E a
emenda **aparece no dado**: para o mesmo dia 7, ICON dizia 27,4 °C e ECMWF dizia
22,7 °C — **4,7 °C de desacordo na costura**.

Isso significa que uma série contínua de 16 dias tem um degrau por volta do dia
8 que não é meteorologia, é troca de fonte. Desenhá-la como uma curva só faria o
app exibir uma mudança de tempo que não vai acontecer.

Daí a fronteira ser visível em vez de disfarçada: ela já existe no dado, e a
escolha é entre mostrá-la ou deixar que ela se apresente como previsão.

## A incerteza que existe de graça, e a que não existe

No endpoint padrão, até o dia 16, há **probabilidade de precipitação** real,
derivada de concordância entre membros do ensemble:

```
precipitation_probability_max, precipitation_probability_mean, precipitation_probability_min
```

Não há equivalente para temperatura — não existe `temperature_2m_max_spread` no
endpoint gratuito. Para spread de temperatura seria preciso o ensemble e o
cálculo sobre `_member01..31` à mão.

Por isso o horizonte longo troca o ícone pela probabilidade de chuva: é o único
canal de incerteza honesto disponível sem trocar de API.

### A borda da janela vem incompleta

Medido na implementação, em 16 de setembro de 2026, e **não previsto quando
este registro foi escrito**: a API devolve as dezesseis *datas* sempre, mas os
*valores* da ponta podem vir `null`. Em Berlim, o dia 16 vinha sem variável
alguma e a probabilidade faltava também no dia 15; em Cairo, só o dia 16; em
São Paulo e Wellington, nada faltava — no mesmo instante.

Varia com a cidade e com a hora local, então não é estado que uma fixture
capture sozinha: os dezesseis dias preenchidos são um caso, não *o* caso. A
consequência é de modelagem — maxima, mínima e chuva são opcionais no payload,
como já eram em `DiaDoHistorico` pela mesma razão (o arquivo também é incompleto
nas bordas). Declará-las obrigatórias fazia a resposta inteira falhar na
validação: a página abria em erro por causa de uma célula na ponta da grade.

O dia incompleto **continua na grade**, com a data. Descartá-lo faria a
contagem de dezesseis e a fronteira do dia 8 deixarem de casar, e a célula
sumiria sem dizer por quê.

## Consequences

**A aptidão para no dia 7**, e não no 16. Ela depende de precipitação e umidade,
cuja skill colapsa primeiro; e a decisão que ela informa é de 1 a 5 dias — nunca
se decide hoje se lava roupa daqui a doze. A grade mostra 16 dias; só os sete
primeiros são julgados.

**O glossário ganha um par de termos, não um.** *Horizonte curto* e *horizonte
longo* nomeiam os dois lados da fronteira. Um nome só — "previsão estendida" —
prometeria extensão sem dizer que a qualidade cai, que é a metade que importa.

**Os números deste registro não serão remedidos.** O seam de 4,7 °C, o σ de
4,5 °C e o mapeamento de modelos vieram de sondagem à API viva em setembro de
2026. Quem duvidar precisa refazer a sondagem; quem só ler o código não vai
encontrar nada disso, porque o código terá apenas `DIAS_DE_PREVISAO = 16` e uma
constante de fronteira.

**Reverter é caro** na direção de encolher: a grade, a fronteira, a aptidão e o
vocabulário assumem 16. Na direção de crescer é pior — exige trocar de API,
perder o ícone e reescrever a apresentação em faixas.
