# 27: Alinhar o frontend ao termo "cidade vizinha"

**What to build:** o frontend passa a usar *vizinha* onde hoje diz *próxima*,
que é o termo canônico registrado no `CONTEXT.md`.

**Blocked by:** —

**Status:** resolved

Surgiu ao escrever o `CONTEXT.md`: o backend já chama de *vizinha*
(`services/vizinhas.py`, `selecionar`), mas o frontend exibe o painel como
"Cidades proximas" e o componente se chama `CidadesProximas`. O glossário
escolheu **vizinha** — é o termo da spec e o que nomeia o algoritmo de seleção
por anéis.

Ticket de vocabulário, não de comportamento: nada na tela muda de função.

- [x] `CidadesProximas.tsx` → `CidadesVizinhas.tsx`, com o componente renomeado
- [x] Título do painel: "Cidades proximas" → "Cidades vizinhas"
- [x] Estado vazio: "Sem cidades proximas para comparar." → "vizinhas"
- [x] O campo `nearby` do payload **não** muda: é contrato de API, e o ticket é
      de vocabulário de interface

Referência: [CONTEXT.md](../../../CONTEXT.md), verbete *Cidade vizinha*.

### Achados da revisao

Nada aplicado: os dois eixos passaram limpos. O diff e de 3 arquivos, 10
insercoes e 10 remocoes, todas identificador ou literal de string.

Descartado:

- A varredura pediu conta dos sete `proxim*` que sobraram no frontend. Todos
  sao lingua comum, nao o termo de dominio: "cidade mais proxima" em
  `cidadeInicial.ts` e `api/client.ts` fala da regra dos 50 km, onde o conceito
  e *cidade detectada* e o `CONTEXT.md` usa essa mesma frase; "nos proximos 7
  dias", "proxima visita" e o `const proximo` do toggle de tema sao temporais.
  Ficam.
- "comparar com a regiao em volta", no comentario de topo do componente.
  *Regiao* esta na lista `_Avoid_` do verbete, mas ali e adverbio, nao nome do
  conceito — o proprio `CONTEXT.md` escreve "apresentada para comparacao
  regional". Fica.
- O `docs/agents/triage-labels.md` nao lista `resolved` entre os cinco rotulos,
  e este ticket usa `resolved`. Nao e defeito deste ticket: os 22 fechados do
  diretorio usam `resolved`, e a secao de wayfinding do `issue-tracker.md` e
  que governa aqui, por existir `map.md`. Fica registrado como deriva de doc.

Fora de escopo, anotado so para nao se perder: os nomes de arquivo
`03-regioes-proximas.md` e `08-criterio-proximidade.md` e a prosa do backend
(`services/vizinhas.py`, nomes de teste) sao anteriores ao glossario e este
ticket e de interface.
