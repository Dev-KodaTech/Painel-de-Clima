# 03: Alertas oficiais do INMET

Status: ready-for-agent

**What to build:** a seção de alertas oficiais da página Condições, e a
precedência do alerta no painel da Visão geral. É a fatia que dá ao app o que ele
nunca teve: um aviso assinado por autoridade, com recomendação de segurança.

Decisões técnicas em
[ADR 0008](../../../docs/adr/0008-inmet-por-json-e-poligono.md); a coexistência
dos dois conceitos em
[ADR 0007](../../../docs/adr/0007-alerta-oficial-e-condicao-prevista-coexistem.md).

**Blocked by:** 01, 02

## Cliente e filtragem

- [x] Cliente do INMET em módulo próprio, único lugar que conhece o formato deles
- [x] `GET https://apiprevmet3.inmet.gov.br/avisos/ativos`, sem chave
- [x] **HTTP/1.1 forçado** em `AsyncClient` próprio, com comentário explicando por
      quê: o servidor anuncia ALPN, não negocia HTTP/2 e derruba a conexão. A
      divergência do padrão de injeção do `open_meteo.py` é deliberada
- [x] Dedup de `hoje` + `futuro` por `id` — as duas listas se sobrepõem
- [x] Duplo parse de `poligono`: é GeoJSON como string escapada dentro do JSON
- [x] Ponto-em-polígono sobre a coordenada da cidade escolhida, ordem `[lon, lat]`
- [x] Consulta só quando `country_code` é `BR`; fora disso nem chama
- [x] Cache com chave fixa, não por coordenada — o feed é nacional e serve todas
      as cidades brasileiras
- [x] Falha do INMET não derruba a resposta: as condições previstas continuam

## Interface

- [x] Seção "Alertas oficiais" acima das condições previstas, visivelmente
      distinta — a separação é estrutural, não tipográfica
- [x] Card com tipo, severidade, janela de validade e riscos
- [x] Recomendações (`instrucoes`) atrás de um expandir, recolhidas por padrão
- [x] Cores oficiais do INMET por severidade (`aviso_cor`), com contraste checado
      no tema escuro — `#FFFE00` como fundo exige texto escuro. **Medido: as
      três exigem.** Branco reprova em todas (amarelo 1,08:1, laranja 2,33:1,
      vermelho 4,00:1); o texto é preto fixo nas três, e não o token do tema,
      porque o fundo vem do INMET e não muda com o tema
- [x] A severidade é texto, não só cor
- [x] Cada card declara que é do INMET
- [x] Rodapé da seção com os telefones: 199 (Defesa Civil) e 193 (Bombeiros)
- [x] **Três estados distintos**, nunca colapsados: sem alertas no Brasil / fora
      de cobertura / falha na consulta. Fora do Brasil a interface diz que não há
      cobertura, jamais que não há alerta
- [x] O expandir funciona por teclado

## Painel da Visão geral

- [x] Alerta oficial tem precedência sobre condição prevista nos dois slots
- [x] O painel continua com dois cards e `h-faixa3` — indicador de severidade no
      painel fica fora desta fatia

## Atribuição

- [x] `ATRIBUICAO` vira função; cada endpoint monta a sua
- [x] `/api/condicoes` credita o INMET quando houver alertas, e não credita quando
      não houver

## Testes

- [~] Fixtures com `respx`, no padrão do `open_meteo` — **montados a partir do
      formato documentado no ADR 0008, não capturados do feed ao vivo**: não
      houve saída de rede para `apiprevmet3.inmet.gov.br` no ambiente da
      implementação. Quem tiver rede deve rodar `uv run pytest -m contract`
      uma vez e corrigir o que divergir
- [~] Teste de contrato marcado `contract`, batendo no INMET de verdade —
      escrito, mas **nunca executado**: sem rede no ambiente. É ele que valida
      os fixtures acima
- [x] Golden de ponto-em-polígono com pelo menos um caso dentro e um fora,
      validado contra os `geocodes` do mesmo aviso
- [x] Caso de coordenada fora do Brasil, provando que resulta em "fora de
      cobertura" e não em "sem alertas"
- [x] **Fixture sintético para `Grande Perigo`**, com comentário registrando que
      `id_severidade: 8` e a cor são presumidos: nenhum estava ativo durante a
      investigação, e isso não foi confirmado por observação

## Comments

Implementado. O cliente vive em `backend/app/services/inmet.py`, único lugar
que conhece o formato do INMET: HTTP/1.1 forçado com o comentário explicando
por quê, dedup de `hoje`+`futuro` por `id`, duplo parse do `poligono` e ray
casting próprio sobre o anel externo — sem `shapely`, porque o ADR 0008
registra que todos os avisos observados são `Polygon` simples e a dependência
compilada não se pagaria por uma função de vinte linhas.

Os três estados viraram `status_dos_alertas` no payload, e não uma lista vazia
que o frontend interpretasse. `/api/condicoes` passou a exigir `country_code`
— sem ele o backend não tem como distinguir "sem alertas" de "fora de
cobertura", que é justamente o que o ADR 0008 proíbe colapsar.

`ATRIBUICAO` virou `atribuicao(com_inmet=...)`. O painel credita o INMET pelo
que de fato **exibe**, não pelo que a consulta devolveu: com dois alertas
ativos o segundo não cabe nos dois slots, e um alerta fora da tela não é fonte
de nada ali.

### O que a revisão pegou, e foi corrigido

- O painel exibia card do INMET e **não o creditava** — só `/api/condicoes`
  tinha sido atualizado. Regressão coberta por teste.
- `KeyError` de campo ausente e `json.JSONDecodeError` de corpo malformado
  subiam como `500`. `JSONDecodeError` é `ValueError`, não `httpx.HTTPError`,
  e escapava do `except`. Os dois viram `InmetIndisponivel` agora: o ADR 0008
  promete que falha do INMET não derruba a página, e a promessa só valia para
  falha de rede.
- `country_code=br` minúsculo caía em "fora de cobertura" para coordenada
  brasileira — a falsa afirmação de segurança do ADR, disparada pela caixa em
  vez da geografia. `.upper()`, como o `repositorio.py` já fazia.
- Severidade fora da tabela caía no **amarelo**, a cor mais fraca. A escala do
  INMET cresce: uma severidade desconhecida só pode ser mais grave que a maior
  conhecida, então o padrão passou a ser o vermelho. Errar para o alarme é
  recuperável; errar para a calmaria, numa tela onde se decide sair de casa,
  não é.
- `montar_painel` e `montar_condicoes` esperavam os dois fornecedores em
  série. `asyncio.gather` nos dois: são independentes, e o timeout do INMET é
  de dez segundos.

### Não verificado

**Nada disto foi visto num browser, e o INMET nunca foi consultado de
verdade** — o ambiente não tinha saída de rede para
`apiprevmet3.inmet.gov.br` (nem Postgres para subir o backend). Os fixtures
saíram do formato documentado no ADR 0008, não de captura ao vivo, e o teste
de contrato que os valida foi escrito mas nunca executado.

Antes de considerar a fatia fechada, alguém com rede deve rodar
`uv run pytest -m contract` e abrir a página numa cidade brasileira com aviso
ativo. É o passo que confirma nomes de campo, formato de data (`inicio`/`fim`
viajam como o INMET os emite, sem reformatação) e as cores reais por
severidade.

Suíte: 366 passed. A falha de `test_o_uv_usa_o_dia_da_cidade_e_nao_a_ponta_da_janela`
é pré-existente e não relacionada — já registrada nas fichas 01 e 02, e
confirmada em `git stash` contra o código anterior a esta fatia. Frontend
typecheca e linta limpo.
