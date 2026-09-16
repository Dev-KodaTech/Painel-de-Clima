# 01: Guard de sessão

Status: concluida

**What to build:** uma dependência do FastAPI que resolve a sessão do cookie e
recusa com `401` quando não há conta, para que rotas autenticadas deixem de
repetir a mesma verificação à mão.

Fatia isolada de propósito, como a `01` de `condicoes` foi. **Não é infraestrutura
desta feature**: a issue 05 de `locais-salvos` precisa exatamente do mesmo guard e
foi especificada antes. Sai aqui porque é aqui que ela bloqueia — quem
implementar `locais-salvos` primeiro deve consumir esta fatia, não reescrevê-la.

**Blocked by:** nada

## O que existe hoje

- [x] Ler `conta_da_sessao()` em `backend/app/routers/conta.py:234` antes de
      escrever qualquer coisa: ela já colapsa os três casos de "sem sessão
      válida" (cookie ausente, linha inexistente, linha expirada) num `None`
      único, para que não se possa sondar identificadores. Esse comportamento é
      requisito, não detalhe
- [x] O relógio da expiração é o da aplicação, injetável — é por isso que a função
      mora no router e não no repositório. O guard herda essa restrição

## O guard

- [x] Uma dependência (`Depends`) que devolve a `Conta` autenticada
- [x] `401` quando não há sessão válida, com a mesma indistinguibilidade dos três
      casos que `conta_da_sessao()` já garante
- [x] Nenhuma mensagem de erro que revele se o e-mail existe, se a sessão expirou
      ou se o cookie faltou
- [x] Uma segunda forma, opcional, que devolve `Conta | None` sem recusar — a
      página Calendário é mista e precisa responder previsão para quem não tem
      conta. **Sem isso a fatia 08 não consegue ser parcialmente pública**
- [x] Onde a função mora: decidir entre manter em `conta.py` e importar, ou mover
      para um módulo próprio. Registrar a escolha em docstring — o repo documenta
      escolhas estruturais
- [x] `/api/quem-sou` passa a usar o guard opcional, provando que o
      comportamento não mudou

## Testes

- [x] Rota de teste protegida devolve `401` sem cookie
- [x] `401` com cookie de sessão inexistente
- [x] `401` com sessão expirada, usando o relógio injetável — sem esperar 7 dias
- [x] `200` com sessão válida, e a conta correta chega ao handler
- [x] As três recusas são indistinguíveis entre si no corpo e no status
- [x] O guard opcional devolve `None` em vez de recusar, nos três casos
- [x] `/api/quem-sou` continua com o comportamento atual — a suíte existente
      passa sem alteração

## Notas

O backend não tem middleware de autenticação e isso é deliberado. Esta fatia
**não** introduz middleware: uma dependência explícita por rota mantém visível
quais rotas exigem conta, que é o que uma varredura do `routers/` deve conseguir
responder.

## Como ficou

**Módulo próprio: `backend/app/dependencias.py`.** `conta_da_sessao()` mudou-se
de `routers/conta.py` para lá, e o guard nasceu ao lado dela. A escolha está
registrada na docstring do módulo, com o motivo: importar de `routers/conta.py`
faria `routers/locais.py` e `routers/calendario.py` dependerem de um terceiro
router — uma aresta entre features que não descreve relação de domínio nenhuma,
só a ordem em que as coisas foram escritas.

Três nomes públicos:

- `conta_da_sessao(repositorio, id_da_sessao)` — a função de antes, intacta,
  ainda recebendo o repositório de quem já o tem em mãos.
- `conta_opcional` — `Depends` que devolve `Conta | None`, sem recusar.
- `conta_exigida` — `Depends` que devolve `Conta` ou levanta `401`.

`conta_exigida` é construída **sobre** `conta_opcional`, e não ao lado: as duas
leem o cookie do mesmo jeito e só divergem no que fazem com a ausência. Duas
leituras independentes divergiriam no dia em que uma fosse ajustada, e a que
ficasse para trás seria a que decide quem entra.

A recusa é `MSG_SEM_SESSAO = "Entre para continuar."` — uma constante só para os
três casos, pela mesma razão que `MSG_CREDENCIAIS_INVALIDAS` é uma só para os
dois modos de errar a entrada.

### Testes

`backend/tests/test_guard_de_sessao.py`, dez casos contra um `FastAPI` montado
no próprio arquivo com uma rota por forma do guard. **Nenhuma rota de sonda foi
publicada em produção**: as rotas reais que exigem conta chegam nas fatias 08 e
na 05 de `locais-salvos`, e o guard não precisava esperar por elas para ser
provado.

Um caso a mais do que a ficha pediu:
`test_cada_cookie_traz_a_sua_conta_e_nao_a_da_outra`, com duas contas vivas ao
mesmo tempo. A ficha pedia "a conta correta chega ao handler", e com uma conta só
na tabela esse caso passaria mesmo se o guard devolvesse "a conta que existe" —
que é o bug que os consumidores não poderiam absorver, com os planos de uma
pessoa aparecendo para outra. Verificado por mutação: trocar
`conta_por_id(encontrada.conta_id)` por `conta_por_id(1)` derruba **só** esse
caso, e nenhum dos outros nove.

Os dois casos que carregam a propriedade central da fatia:
`test_as_tres_recusas_sao_indistinguiveis_entre_si` compara status e corpo
inteiro das três, e ainda afirma que o status é `401` — três respostas que
regredissem juntas para `200` continuariam iguais, e um teste só de igualdade
passaria dizendo que a rota está protegida enquanto deixava entrar qualquer um.
`test_a_recusa_nao_revela_o_email_a_expiracao_nem_o_cookie` varre o texto cru
atrás de "expir", "cookie", "sessao" e do e-mail.

### Verificado

Suíte: **400 passed** (era 391 antes da fatia; 9 novos, zero regressões).
`test_conta_http.py` passa **sem uma linha alterada**, que é o que a ficha pedia
como prova de que `/api/quem-sou` não mudou de comportamento.

O contrato OpenAPI de `/api/quem-sou` foi comparado antes e depois: o parâmetro
de cookie continua saindo com o mesmo nome, lugar (`in: cookie`) e schema. Mover
a leitura do cookie para dentro de um `Depends` não deslocou a superfície da API.

### Fica para quem consumir

**A forma `Depends` abre a própria transação.** `conta_opcional` chama
`repositorio_do_processo.atual()`, que abre uma transação de verdade. Hoje isso
não custa nada: o único consumidor é `/api/quem-sou`, que só lê a conta e não
abriria outra de qualquer jeito.

Custa na primeira rota que **exige conta e consulta o banco** — a fatia 05 de
`locais-salvos`, e a 08 daqui. Lá o handler abrirá a segunda transação, e a
conta terá sido lida numa transação diferente da que lê os dados que ela
autoriza. Duas saídas, e a escolha é de quem chegar primeiro:

1. um repositório por requisição, que as duas pontas compartilham; ou
2. a rota recebe `conta_exigida` e abre a sua transação como já faria, aceitando
   as duas — que é o que o `quem-sou` faz hoje e é barato enquanto a leitura da
   conta for uma consulta só.

`conta_da_sessao()` continuar sendo função comum, e não só uma dependência, é o
que mantém a saída (1) disponível sem reescrever o guard. **Não foi resolvido
aqui de propósito**: a solução é infraestrutura que atinge todas as rotas, e esta
fatia é isolada.

### Não verificado

**A suíte marcada `postgres` não rodou** — o Postgres do `compose.yaml` não
estava de pé neste ambiente. Ela está excluída da execução padrão por desenho e
estava igualmente fora no baseline, então não houve regressão mascarada; ainda
assim, quem tiver Docker deve rodar `uv run pytest -m postgres` antes de
considerar a fatia fechada, porque é ela que exerce o `SELECT` da sessão contra
o SQL de verdade — o caminho que este guard passou a percorrer em toda rota
autenticada.

Nada aqui foi visto num browser, e não havia o que ver: a fatia é inteira de
backend e não acrescenta nenhuma rota à aplicação.
