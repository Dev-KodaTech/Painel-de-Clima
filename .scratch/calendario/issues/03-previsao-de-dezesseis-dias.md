# 03: Previsão de dezesseis dias no backend

Status: ready-for-agent

**What to build:** o endpoint que serve os dezesseis dias da cidade escolhida,
com a fronteira do dia 8 explícita no payload.

Decisões em
[ADR 0010](../../../docs/adr/0010-dezesseis-dias-e-a-fronteira-do-dia-oito.md).

**Blocked by:** nada

## A chamada

- [x] `forecast_days=16` numa chamada **nova**, não na `buscar_previsao()`
      existente. A de 7 dias serve cinco páginas que não leem o dia 12, e engordá-la
      faria todas pagarem — mesmo raciocínio do
      [ADR 0003](../../../docs/adr/0003-historico-e-buscado-na-pagina.md) e da
      separação de `buscar_uv()`
- [x] Variáveis diárias: as sete de `VARIAVEIS_DIARIAS` mais
      `precipitation_probability_max`. A probabilidade é o **único** canal de
      incerteza gratuito no endpoint padrão (não existe spread de temperatura) e é
      o que o horizonte longo exibe no lugar do número seco
- [x] Sem bloco `hourly` — a página é diária, e 16 dias de horas seriam 384 pontos
      que ninguém lê
- [x] `timezone=auto`, como as outras chamadas
- [x] Cache na família de 10 minutos (`atual()`), chave por coordenada
      arredondada com prefixo próprio — não pode colidir com `previsao:`, que
      guarda 7 dias com outras variáveis

## A fronteira no payload

- [x] Uma constante nomeada para o primeiro dia do horizonte longo (dia 8), com
      docstring explicando que ela espelha a troca ICON → ECMWF e **não** é
      preferência de layout
- [x] Cada dia do payload declara a qual horizonte pertence. Um campo explícito,
      não uma regra de índice que o frontend redescobre — se a Open-Meteo mudar o
      encadeamento, o ajuste é aqui e não em dois lugares
- [x] O horizonte longo **não** carrega `icon` nem `description`: o backend não
      envia o que a interface não deve exibir. Enviar e confiar que o frontend
      ignore é como o campo `alerts` do ADR 0001 — o dado sugere um uso que a
      regra proíbe
- [x] `precipitation_probability_max` presente em todos os dias; a interface a
      usa só no longo, mas o dado é o mesmo

## Endpoint

- [x] Rota nova sob `/api`, com os mesmos parâmetros de coordenada das outras
- [x] `503` com `MSG_INDISPONIVEL` quando a Open-Meteo falha, como as demais
- [x] `attribution` pela função de atribuição, não pela constante — o padrão que
      a página Notícias estabeleceu
- [x] Modelos Pydantic em `app/models.py`, espelhando o payload 1:1

## Testes

- [x] Fixture golden de 16 dias, com `respx`
- [x] O payload traz exatamente 16 dias
- [x] Os sete primeiros vêm marcados como horizonte curto e trazem `icon`
- [x] Do oitavo em diante vêm como horizonte longo e **não** trazem `icon`
- [x] `precipitation_probability_max` presente em todos
- [x] Falha da API externa vira `503`, não `500`
- [x] Cache: duas requisições à mesma coordenada fazem **uma** chamada externa —
      contando requisições, como `test_cache_http.py` faz
- [x] A chave do cache não colide com a de `buscar_previsao()`: pedir o painel e
      depois os 16 dias faz duas chamadas externas, não uma
- [x] Teste de contrato marcado (`@pytest.mark.contract`) contra a API viva,
      verificando que `forecast_days=16` ainda é aceito e que
      `precipitation_probability_max` ainda vem preenchido

## Risco a registrar no código

O ADR 0010 mediu a troca de modelo em setembro de 2026. Se a Open-Meteo mudar o
encadeamento, a fronteira do dia 8 deixa de casar com a troca real e o app passa
a desenhar uma fronteira no lugar errado — sem erro nenhum, o que é pior. O teste
de contrato é o que avisa.

## Comments

**Implementado.** `/api/horizonte`, com `buscar_horizonte()` em `open_meteo.py`,
`montar_horizonte()` em `weather.py` e os modelos `DiaDoHorizonte` /
`HorizonteResponse`. Cache com prefixo `horizonte:`, na família de 10 minutos.

**Um achado contra a API viva, que mudou o payload.** O teste de contrato pegou
logo na primeira execução: a Open-Meteo devolve as dezesseis **datas** sempre,
mas os *valores* da ponta podem vir `null` — em Berlim, o dia 16 sem variável
alguma e a probabilidade faltando também no 15; em Cairo, só o 16; em São Paulo
e Wellington, nada faltava, tudo no mesmo instante.

Com `high`, `low` e `precipitation_mm` obrigatórios — que é o que a fixture
golden de dezesseis dias preenchidos sugeria —, a validação do Pydantic
derrubava a resposta inteira e a página abria em erro por causa de uma célula na
ponta da grade. Medido: `/api/horizonte` para Berlim respondia `500`.

Os três passaram a ser opcionais, pela mesma razão que `DiaDoHistorico` já os
tinha assim (o arquivo também é incompleto nas bordas). O dia incompleto
**continua na grade**, com a data: descartá-lo faria a contagem de dezesseis e a
fronteira do dia 8 deixarem de casar. Registrado no ADR 0010, numa seção nova, e
coberto por `FORECAST_DEZESSEIS_COM_BORDA_INCOMPLETA` — a golden sozinha esconde
o caso.

**Consequência para a fatia 06 (aptidão na grade):** a célula pode não ter
número para exibir. A interface precisa de um estado para "o dado não veio",
distinto de "sem aptidão por ser horizonte longo" — são coisas diferentes, e a
story 14 já pede que o segundo seja explicado.

**Fora do escopo desta fatia**, como o ticket define: a grade (04), a aptidão
(05/06) e os planos (07/08). A frase da barra lateral já tinha mudado num commit
anterior.

### Da revisão

**O risco registrado não tem alarme automático, e não dá para ter.** O ticket
diz que *"o teste de contrato é o que avisa"* se a Open-Meteo mudar o
encadeamento de modelos. O teste verifica o que é verificável — que
`forecast_days=16` ainda é aceito, que 17 ainda é recusado, que a probabilidade
cobre o horizonte longo — mas **não** o mapeamento ICON/ECMWF/GFS em si: isso
exigiria sondar `best_match` contra cada modelo e comparar, que é o trabalho
manual que o ADR 0010 registra.

Ou seja: a fronteira do dia 8 sair do lugar continua sendo um risco **documentado
e não detectado**. Fica aqui em vez de virar um teste que promete mais do que
cumpre.

**Uma guarda a mais, não pedida:** `buscar_horizonte()` recusa uma janela com
menos de dezesseis dias, como `OpenMeteoIndisponivel`. Sem ela, uma resposta
truncada viraria uma grade menor com a fronteira ainda no lugar certo — dias
faltando sem erro nenhum, que é o mesmo modo de falhar em silêncio que o prefixo
próprio da chave de cache existe para impedir. Coberto por
`test_uma_janela_mais_curta_nao_vira_uma_grade_silenciosamente_menor`.
