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

- [ ] Cliente do INMET em módulo próprio, único lugar que conhece o formato deles
- [ ] `GET https://apiprevmet3.inmet.gov.br/avisos/ativos`, sem chave
- [ ] **HTTP/1.1 forçado** em `AsyncClient` próprio, com comentário explicando por
      quê: o servidor anuncia ALPN, não negocia HTTP/2 e derruba a conexão. A
      divergência do padrão de injeção do `open_meteo.py` é deliberada
- [ ] Dedup de `hoje` + `futuro` por `id` — as duas listas se sobrepõem
- [ ] Duplo parse de `poligono`: é GeoJSON como string escapada dentro do JSON
- [ ] Ponto-em-polígono sobre a coordenada da cidade escolhida, ordem `[lon, lat]`
- [ ] Consulta só quando `country_code` é `BR`; fora disso nem chama
- [ ] Cache com chave fixa, não por coordenada — o feed é nacional e serve todas
      as cidades brasileiras
- [ ] Falha do INMET não derruba a resposta: as condições previstas continuam

## Interface

- [ ] Seção "Alertas oficiais" acima das condições previstas, visivelmente
      distinta — a separação é estrutural, não tipográfica
- [ ] Card com tipo, severidade, janela de validade e riscos
- [ ] Recomendações (`instrucoes`) atrás de um expandir, recolhidas por padrão
- [ ] Cores oficiais do INMET por severidade (`aviso_cor`), com contraste checado
      no tema escuro — `#FFFE00` como fundo exige texto escuro
- [ ] A severidade é texto, não só cor
- [ ] Cada card declara que é do INMET
- [ ] Rodapé da seção com os telefones: 199 (Defesa Civil) e 193 (Bombeiros)
- [ ] **Três estados distintos**, nunca colapsados: sem alertas no Brasil / fora
      de cobertura / falha na consulta. Fora do Brasil a interface diz que não há
      cobertura, jamais que não há alerta
- [ ] O expandir funciona por teclado

## Painel da Visão geral

- [ ] Alerta oficial tem precedência sobre condição prevista nos dois slots
- [ ] O painel continua com dois cards e `h-faixa3` — indicador de severidade no
      painel fica fora desta fatia

## Atribuição

- [ ] `ATRIBUICAO` vira função; cada endpoint monta a sua
- [ ] `/api/condicoes` credita o INMET quando houver alertas, e não credita quando
      não houver

## Testes

- [ ] Fixtures golden capturados do feed real, com `respx`, no padrão do
      `open_meteo`
- [ ] Teste de contrato marcado `contract`, batendo no INMET de verdade
- [ ] Golden de ponto-em-polígono com pelo menos um caso dentro e um fora,
      validado contra os `geocodes` do mesmo aviso
- [ ] Caso de coordenada fora do Brasil, provando que resulta em "fora de
      cobertura" e não em "sem alertas"
- [ ] **Fixture sintético para `Grande Perigo`**, com comentário registrando que
      `id_severidade: 8` e a cor são presumidos: nenhum estava ativo durante a
      investigação, e isso não foi confirmado por observação
