# Locais salvos exigem conta, e é por isso que existe um banco

Até aqui o app não guardava nada do usuário além de duas chaves no
`localStorage` — o tema e a última cidade. A política estava escrita, em
`frontend/src/janelaNaUrl.ts`:

> "Nao vai para o `localStorage`: a URL ja atende compartilhar e recarregar, e o
> armazenamento continua restrito a ultima cidade e ao tema."

Locais salvos rompe essa frase, e a frase precisa ser reescrita junto com esta
decisão. A lista passa a viver no **PostgreSQL**, atrás de uma conta com e-mail
e senha, e o projeto ganha Docker, Alembic, SQLAlchemy e autenticação.

## A alternativa rejeitada era mais barata, e foi rejeitada mesmo assim

`localStorage` resolveria a funcionalidade inteira sem backend nenhum: um array
de query strings, revalidado na leitura por `cidadeDosParametros`, seguindo a
convenção que `ultimaCidade.ts` já estabeleceu. Zero dependências novas, zero
senhas para guardar, uma tarde de trabalho.

O que ela não faz é atravessar dispositivos — e o objetivo declarado desta
entrega é **demonstrar a stack completa**. Postgres, container, migrações e
sessão são o produto aqui; a lista de cidades é o pretexto honesto para eles.
Registrar isso importa porque, olhando só o código, a proporção parece errada:
três tabelas e um sistema de autenticação para guardar nomes de cidades. Sem
este parágrafo, a próxima pessoa concluiria que alguém exagerou por engano.

O escopo foi contido pelo mesmo motivo: e-mail, senha e sessão. **Sem**
recuperação de senha, verificação de e-mail ou OAuth — cada um desses é um
subsistema, e nenhum demonstra nada que os três primeiros já não demonstrem.

## Consequences

**Passamos a guardar senhas de outras pessoas.** É a consequência que não
aparece no dia do commit e não vai embora: hash com Argon2 ou bcrypt não é
detalhe de implementação, é a obrigação que esta decisão cria. Nenhuma senha
em log, em erro ou em resposta.

**Duas filosofias de estado passam a conviver.** O [ADR 0002](0002-cidade-na-url.md)
pôs a cidade na URL para que todo link fosse um link de verdade. Isso continua
valendo para seis páginas. Locais salvos é a sétima e é o oposto: a mesma URL
mostra listas diferentes para contas diferentes, e o link não carrega nada.

A regra que separa as duas:

> **Dado que o conteúdo é função da URL, ele vai na URL; dado que é função de
> quem está olhando, ele vai no banco.**

**Quem não tem conta não vê a estrela.** Salvar deslogado em `localStorage` e
migrar ao entrar foi rejeitado: fundir lista anônima com lista da conta tem
casos de conflito — a mesma cidade dos dois lados, ordem, duplicatas — que
custam mais código que a funcionalidade inteira. Um local salvo pertence a uma
conta, e essa regra não tem exceção.

**Reverter é caro.** Tirar o banco significa tirar contas, sessões, o container
e as migrações, e decidir o que fazer com as listas que já existirem. É o que
torna esta decisão registrável em vez de óbvia.
