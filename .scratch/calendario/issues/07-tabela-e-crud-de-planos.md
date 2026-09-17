# 07: Tabela e CRUD de planos

Status: done

**What to build:** a persistência dos planos — tabela, migração, repositório e as
rotas autenticadas que criam, listam e apagam.

O verbete *Plano* está no `CONTEXT.md`. A exigência de conta vem do
[ADR 0004](../../../docs/adr/0004-locais-salvos-exigem-conta.md).

**Blocked by:** 01

## A tabela

- [x] `planos`, seguindo o formato de `locais_salvos` em `app/db/schema.py`
- [x] `conta_id` com `ForeignKey(ondelete="CASCADE")` e índice, mais o lado do
      ORM (`cascade="all, delete-orphan"`, `passive_deletes=True`) — os dois
      lados, como `Conta` já faz, porque apagar conta por SQL direto também tem de
      levar os planos
- [x] `titulo`, `dia` (data, **sem hora** — ver abaixo), `atividade`, `criado_em`
- [x] **Nenhuma coluna de clima.** Mesma regra do `LocalSalvo`: clima guardado
      envelhece, e alguém veria a previsão de anteontem sem saber que é de
      anteontem. Ícone, temperatura e aptidão são buscados frescos e cruzados na
      leitura
- [x] `dia` é `Date`, não `DateTime`. O tipo é o que impede que uma hora entre
      por descuido, e a ausência de hora é decisão de domínio: a aptidão é diária
- [x] Decidir e registrar a representação de `atividade`. As quatro são fixas e
      vêm da regra do backend; guardar texto livre permitiria um plano cuja
      atividade nenhuma regra julga
      — **Decidido: `String(20)` com `CHECK`.** Registrado na coluna, em
      `schema.py`. O `CHECK` fecha o valor **no banco**, e não só na rota: vale
      para quem insere por SQL direto, como o índice de e-mail da `Conta` já
      faz. `ENUM` nativo daria a mesma garantia e foi rejeitado pelo custo de
      mudar — acrescentar a quinta atividade exigiria `ALTER TYPE`, que no
      Postgres não roda em toda transação, e o `downgrade` de um tipo é mais
      trabalhoso que o de uma restrição; com `CHECK`, os dois sentidos da
      migração são um `DROP`/`CREATE CONSTRAINT`
- [x] Limite de tamanho do título, com o mesmo cuidado de `locais_salvos`

## Migração

- [x] `uv run alembic revision --autogenerate`, conferindo o resultado à mão
- [x] Rodar `upgrade head` **e** `downgrade` uma vez, num banco descartável
- [x] Conferir que a URL vem de `app.config.database_url()`, como `env.py` faz

## Repositório

- [x] Métodos no ABC `Repositorio`, implementados **nas duas** classes —
      `RepositorioSql` e `RepositorioEmMemoria`. A segunda não é opcional: é o que
      faz a suíte padrão rodar sem Postgres
- [x] Criar, listar por conta, apagar por id **e conta**
- [x] Apagar exige a conta dona: apagar só por id deixaria uma conta apagar o
      plano de outra
- [x] Listagem ordenada por dia

## Rotas

- [x] `POST`, `GET` e `DELETE` sob `/api`, com o guard obrigatório da fatia 01
- [x] `401` em todas quando não há sessão válida
- [x] `404` — e nunca `403` — ao apagar plano de outra conta. `403` confirmaria que
      o plano existe, e o repo já trata indistinguibilidade como requisito em
      `conta.py`
- [x] Validação: título não vazio, dia é data válida, atividade é uma das quatro
- [x] Decidir se dia no passado é aceito na criação. Recomendação: **sim** — a
      página lida com planos passados de qualquer forma (story 28), e recusar
      criaria uma regra que a listagem depois contradiz
      — **Decidido: aceito**, pela recomendação. Registrado nas docstrings de
      `criar_plano` (no ABC) e da rota `criar`, e guardado por um caso em cada
      seam. Quem registra no sábado o que fez na sexta não está cometendo um
      erro

## Testes

- [x] Criar, listar e apagar pelo seam HTTP com `TestClient` e o repositório em
      memória — o estilo da casa (`test_conta_http.py`)
- [x] `401` nas três rotas sem sessão
- [x] Uma conta não vê os planos de outra
- [x] Uma conta não apaga o plano de outra, e recebe `404`
- [x] Apagar a conta leva os planos junto (marcado `postgres`, onde o cascade é
      de verdade)
- [x] Validação recusa título vazio e atividade inexistente
- [x] Testes de repositório nas duas implementações, como `test_repositorio.py`
      faz

## Comments

### A representação de `atividade`, que era a decisão desta fatia

`String(20)` mais `CHECK`. O que decidiu foi o **custo de mudar**: os três
candidatos dão a mesma garantia de leitura, e só divergem no dia em que a
quinta atividade existir. Com `CHECK`, os dois sentidos da migração são um
`DROP`/`CREATE CONSTRAINT`; com `ENUM` nativo, o `upgrade` é um `ALTER TYPE`
que no Postgres não roda dentro de toda transação, e o `downgrade` de um tipo
é notoriamente chato. Texto livre sem restrição foi descartado pelo motivo que
a própria issue dá.

A lista do `CHECK` é escrita em `schema.ATIVIDADES_ACEITAS` e **não** importada
de `app.models`: o que ela alimenta é SQL, que o banco guarda como texto no
catálogo e não volta a consultar — um import daria a impressão de que mexer no
`Literal` muda o banco, e não muda. O acoplamento é real e ficou guardado por
um teste (`TestAtividadesAceitas`), verificado por mutação: tirar uma atividade
de uma das listas faz o caso falhar.

### A migração, rodada nos dois sentidos

Gerada por `--autogenerate` com o banco de desenvolvimento em `head`, então o
diff trouxe **só** a tabela nova e seus dois índices — nenhum drift pendente.
Conferida à mão e rodada num banco descartável (`painel_migracao`, criado e
derrubado no fim):

- `upgrade head` a partir de um banco **vazio**: as duas migrações aplicam e o
  schema sai com `dia` em `date`, o `CHECK` com as quatro, a FK
  `ON DELETE CASCADE` e os dois índices
- `downgrade -1`: `planos` some, as outras três tabelas ficam intactas e não
  sobra índice órfão
- `upgrade` de novo, para provar que o ciclo é repetível

### O que a verificação contra o Postgres real encontrou

A suíte padrão roda no repositório em memória, então as rotas foram exercidas
com o backend ligado no Postgres de verdade. As três recusam sem sessão; o
título é aparado; a listagem sai por dia (o plano do dia 21 antes do dia 23,
apesar de ter sido criado depois); `conta_id` não aparece em resposta nenhuma;
os quatro casos de validação dão 422.

O que mais importava ali é a isolação entre contas, e ela foi medida e não
deduzida: apagar plano alheio e apagar plano inexistente devolvem respostas
**byte a byte idênticas** (`diff` limpo entre as duas), o plano da outra conta
sobrevive à tentativa, e a dona apaga o seu com 204.

### O que a revisão (`/code-review`) mudou

O eixo de spec não achou requisito faltando nem implementação errada. O de
standards achou três coisas reais:

- **Os testes de recusa conferiam o status e não a mensagem.** A classe dizia
  "recusam igual" e só um dos três casos comparava o `detail`; os dois de
  `404` não comparavam nenhum. Como a propriedade é justamente as respostas
  **não divergirem** — o risco que o `_recusar_credenciais` do `conta.py`
  registra é alguém "ajudar" detalhando uma delas —, os casos passaram a
  afirmar a mensagem, e entrou um que compara as duas respostas inteiras
- **A ordenação em memória dependia de uma prova, não da regra.** Ela ordenava
  por `dia` e contava com a estabilidade do `sorted` sobre a ordem de inserção
  do dicionário — o que só coincide com o `ORDER BY dia, id` do SQL enquanto os
  ids forem monotônicos com a inserção, que é propriedade do `count()` e não da
  regra de ordenação. Passou a ser `(dia, id)` explícito: é o lugar exato em que
  as duas implementações poderiam divergir em silêncio, que é o risco que a
  bateria compartilhada existe para cobrir
- **O teste de acoplamento estava solto no módulo**, entre uma função auxiliar e
  as classes. Virou `TestAtividadesAceitas`

Uma quarta observação — três linhas em branco em `test_repositorio.py` — foi
conferida e **não** é desta fatia: já estava no `HEAD`, e mexer nela só
aumentaria o diff.
