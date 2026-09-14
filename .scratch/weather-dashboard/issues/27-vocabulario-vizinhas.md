# 27: Alinhar o frontend ao termo "cidade vizinha"

**What to build:** o frontend passa a usar *vizinha* onde hoje diz *próxima*,
que é o termo canônico registrado no `CONTEXT.md`.

**Blocked by:** —

**Status:** ready-for-agent

Surgiu ao escrever o `CONTEXT.md`: o backend já chama de *vizinha*
(`services/vizinhas.py`, `selecionar`), mas o frontend exibe o painel como
"Cidades proximas" e o componente se chama `CidadesProximas`. O glossário
escolheu **vizinha** — é o termo da spec e o que nomeia o algoritmo de seleção
por anéis.

Ticket de vocabulário, não de comportamento: nada na tela muda de função.

- [ ] `CidadesProximas.tsx` → `CidadesVizinhas.tsx`, com o componente renomeado
- [ ] Título do painel: "Cidades proximas" → "Cidades vizinhas"
- [ ] Estado vazio: "Sem cidades proximas para comparar." → "vizinhas"
- [ ] O campo `nearby` do payload **não** muda: é contrato de API, e o ticket é
      de vocabulário de interface

Referência: [CONTEXT.md](../../../CONTEXT.md), verbete *Cidade vizinha*.
