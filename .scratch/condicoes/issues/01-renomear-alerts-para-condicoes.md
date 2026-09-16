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

- [x] `WeatherResponse.alerts` vira `WeatherResponse.condicoes`
- [x] O modelo `Alerta` vira `CondicaoPrevista`, com a descrição do campo revista:
      ela hoje diz "no maximo duas", e a razão do limite é o layout do painel
- [x] `backend/app/services/alertas.py` vira `condicoes.py`; `derivar()` mantém o
      nome, que continua correto
- [x] O tipo do frontend em `api/types.ts` acompanha, e o componente
      `CondicoesPrevistas.tsx` lê o campo novo
- [x] A suíte `test_alertas.py` vira `test_condicoes.py` e passa sem mudança de
      comportamento — os golden de Wellington, Miami, Innsbruck e Reykjavik
      continuam valendo, e os testes de borda de limiar (59.9/60.0 e o
      equivalente de chuva) continuam idênticos
- [x] Nenhuma mudança visível na Visão geral
- [x] Nenhum resquício de `alerts`/`Alerta` no backend ou no frontend, exceto nas
      ADRs, que são registro histórico e não se editam para acompanhar o código

## Comments

Implementado. Suíte completa roda verde (326 passed; a única falha,
`test_o_uv_usa_o_dia_da_cidade_e_nao_a_ponta_da_janela`, é pré-existente e
não relacionada — confirmado reproduzindo em `git stash`). Frontend
typecheca e builda limpo.

Achado fora do escopo desta ficha, não corrigido aqui: `frontend/src/navegacao.tsx`
ainda descreve a página `/condicoes` como "Condicoes previstas" / "Ainda nao
construida" e conta seis páginas na barra — desatualizado frente ao
`CONTEXT.md` já editado nesta sessão (que renomeia a página para "Condições",
com duas seções, e sobe a contagem para oito). Fica para a ficha que
efetivamente construir a página (02), já que hoje ela ainda não existe.
