# 01: Postgres em container, com migrações

**What to build:** o projeto não tem banco, nem container, nem migrações — o
único arquivo que ele abre é o dos dados de cidades, em leitura. Este ticket
constrói a fundação sobre a qual conta, sessão e locais salvos vão assentar, e
nada mais: nenhum endpoint novo, nada visível.

Sobe um PostgreSQL em container, com **só o banco** containerizado — backend e
frontend continuam rodando como o README manda, porque o recarregamento
automático de ambos é o que torna o desenvolvimento tolerável e dentro de
container ele exige montagem de volumes que quebra com frequência.

Cria as três tabelas — contas, sessões e locais salvos — numa migração inicial.
Três e nada mais: o cache da API externa continua em memória, porque cache que
some no restart é cache funcionando, e o conjunto de cidades continua sendo o
arquivo lido no boot, porque é dado que nunca muda.

E resolve a questão que decide a qualidade de toda a suíte daqui em diante: **o
acesso ao banco entra por injeção**, do mesmo jeito que o relógio e o cache já
entram nos testes existentes. A suíte padrão roda contra um repositório em
memória e continua rodando em cerca de um segundo, sem exigir Docker de
ninguém. Um punhado de testes marcados roda contra o Postgres real sob demanda,
exatamente como o teste de contrato já faz com a API externa — é o que prova que
o schema e as migrações funcionam, e sem eles o repositório em memória
esconderia erros de SQL.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Um arquivo de composição sobe o Postgres, e só ele
- [x] A migração inicial cria as tabelas de contas, sessões e locais salvos
- [x] Aplicar as migrações num banco vazio produz o schema completo
- [x] O e-mail da conta é único no banco, sem diferenciar maiúsculas
- [x] Um local salvo pertence a uma conta, e apagar a conta leva seus locais junto
- [x] Uma sessão pertence a uma conta e tem instante de expiração
- [x] A configuração do banco vem de variável de ambiente, como a de CORS já vem
- [x] Um arquivo de exemplo documenta as variáveis; o arquivo real fica fora do git
- [x] O acesso ao banco é injetável, com uma implementação em memória para os testes
- [x] A suíte padrão roda sem Docker e sem banco, no mesmo tempo de hoje
- [x] Testes marcados rodam contra o Postgres real sob demanda, fora da execução padrão
- [x] O marcador novo está declarado junto do marcador de contrato já existente
- [x] O README diz como subir o banco e como rodar os testes que o exigem
- [x] Nenhum endpoint novo, nenhuma mudança visível
