# 02: Renomear `/semana` para `/calendario`

Status: done

**What to build:** a renomeação da entrada da barra lateral — caminho, título e a
frase do `oQueVem` —, de "Sete dias" em `/semana` para "Calendário" em
`/calendario`.

Fatia isolada porque é a que conserta a promessa falsa, e ela já é um defeito
hoje: a página promete "a previsao dos sete dias expandida" e a Visão geral já
mostra os sete dias. Regra do
[ADR 0006](../../../docs/adr/0006-vizinhas-e-comparacao-nao-lista-longa.md) — a
frase da barra muda junto com a página, e não depois.

**Blocked by:** nada

## A renomeação

- [x] `caminho: "/calendario"` e `titulo: "Calendário"` em
      `frontend/src/navegacao.tsx`
      — **entregue como `"Calendario"`, sem acento.** Todo literal de
      `navegacao.tsx` é sem acento ("Visao geral", "Tendencia", "Condicoes",
      "Noticias"), e acentuar só este destoaria. O `titulo` é visível: vira
      `aria-label`, `title` e o `<h2>` da `PaginaVazia`. Se a preferência for o
      acento correto na tela, a troca é de uma linha — mas então vale trocar os
      sete de uma vez, e não só este. `CONTEXT.md` e `README.md`, que são prosa,
      seguem acentuados
- [x] `oQueVem` reescrito: dezesseis dias, a fronteira, aptidão e planos. **Não
      pode prometer o que as fatias seguintes ainda não entregaram** — enquanto a
      página for `PaginaVazia`, a frase descreve o que vem, e é isso que o campo
      significa
- [x] O ícone continua `IconeCalendario` — ele sempre foi de calendário; era o
      nome que destoava
- [x] Verificar se `/semana` aparece em mais algum lugar do frontend além de
      `navegacao.tsx` e ajustar
- [x] A página continua sendo de cidade: **não** ganha `semCidade`, então mantém a
      busca no cabeçalho

## Sobre redirecionar `/semana`

- [x] Decidir e registrar: `/semana` nunca foi uma página construída, só um stub.
      Um redirect existe para não quebrar link compartilhado, e não há link
      compartilhado de uma página que nunca mostrou nada
- [x] Recomendação: **sem redirect**, e `/semana` cai no `NaoEncontrada` como
      qualquer rota inexistente. Se for adicionado mesmo assim, que seja com
      comentário dizendo por quanto tempo se espera mantê-lo

## Verificação

- [x] A barra lateral mostra "Calendário" e navega para `/calendario`
- [x] O `aria-label` e o `title` do link acompanham o novo nome
- [x] A cidade escolhida continua viajando no link da barra (o `search` que
      `BarraLateral.tsx` já propaga)
- [x] `CONTEXT.md` já foi atualizado nesta sessão — o verbete *Página* lista
      Calendário. Conferir que o código e o glossário concordam
