# 01: `alerts` vira `condicoes` no payload

Status: ready-for-agent

**What to build:** a renomeação que o
[ADR 0001](../../../docs/adr/0001-condicao-prevista-nao-e-alerta.md) declarou
como pré-requisito de exibir alerta oficial, e que o
[ADR 0007](../../../docs/adr/0007-alerta-oficial-e-condicao-prevista-coexistem.md)
agora executa.

O campo `alerts` de `/api/weather` passa a se chamar `condicoes`, e o tipo
`Alerta` passa a se chamar `CondicaoPrevista`. O módulo `alertas.py` passa a se
chamar `condicoes.py`.

Nada muda na tela. É o prefactor que torna a fatia do INMET possível sem
ambiguidade — feito antes e à parte, porque misturá-lo com a integração faria uma
mudança de contrato viajar escondida dentro de uma funcionalidade.

**Blocked by:** None (can start immediately)

- [ ] `WeatherResponse.alerts` vira `WeatherResponse.condicoes`
- [ ] O modelo `Alerta` vira `CondicaoPrevista`, com a descrição do campo revista:
      ela hoje diz "no maximo duas", e a razão do limite é o layout do painel
- [ ] `backend/app/services/alertas.py` vira `condicoes.py`; `derivar()` mantém o
      nome, que continua correto
- [ ] O tipo do frontend em `api/types.ts` acompanha, e o componente
      `CondicoesPrevistas.tsx` lê o campo novo
- [ ] A suíte `test_alertas.py` vira `test_condicoes.py` e passa sem mudança de
      comportamento — os golden de Wellington, Miami, Innsbruck e Reykjavik
      continuam valendo, e os testes de borda de limiar (59.9/60.0 e o
      equivalente de chuva) continuam idênticos
- [ ] Nenhuma mudança visível na Visão geral
- [ ] Nenhum resquício de `alerts`/`Alerta` no backend ou no frontend, exceto nas
      ADRs, que são registro histórico e não se editam para acompanhar o código
