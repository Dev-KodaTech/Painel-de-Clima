# A sessão é um cookie `HttpOnly` com linha no banco, não um JWT

A sessão vive em duas partes: um cookie `HttpOnly`, `SameSite=Lax`, `Secure` em
produção, e uma linha na tabela de sessões. O backend lê o cookie, encontra a
linha, e sabe de quem é a requisição. Sair apaga a linha.

A alternativa era um JWT no `localStorage`, que é o que a maioria dos tutoriais
ensina e por isso merece o registro — quem abrir este projeto esperando JWT
precisa saber que a ausência é deliberada.

## Por que não JWT

**Um token no `localStorage` é legível por qualquer script da página.** O cookie
`HttpOnly` não é — nem pelo nosso próprio código. Num app que carrega Leaflet,
Recharts e o que mais vier de CDN, essa diferença é a distância entre uma
dependência comprometida roubar a sessão ou não.

**JWT não revoga.** Um token válido por uma hora continua válido por uma hora
depois do logout; o servidor não tem como recusá-lo sem manter uma lista de
revogados — que é uma tabela de sessões com passos a mais. Se o resultado é uma
tabela de qualquer jeito, começar com ela é mais simples.

**O frontend não gerencia nada.** `pegar<T>()` em `frontend/src/api/client.ts` é
o único ponto por onde as requisições passam, e ganha `credentials: "include"` e
nada mais. Com JWT, cada chamada precisaria anexar um header, e o cliente
herdaria a lógica de renovação.

## Consequences

**O CORS muda, e de um jeito que não perdoa.** `allow_credentials=True` proíbe
`allow_origins=["*"]` — a origem tem de ser explícita. Em desenvolvimento isso
não aparece, porque o Vite faz proxy de `/api` e o browser vê uma origem só; o
problema nasce inteiro no primeiro deploy que separar frontend de backend, longe
de onde a decisão foi tomada. Está escrito aqui por isso.

`allow_methods=["GET"]` também deixa de bastar: cadastro, login e salvar são
`POST`, e remover é `DELETE`.

**Sessões expiradas acumulam.** Linhas vencidas não somem sozinhas. Uma limpeza
periódica resolve; enquanto não existir, a tabela cresce. Preferível ao caminho
oposto, em que um token vencido continua sendo aceito.

**Uma conta pode ter várias sessões.** Dois navegadores, duas linhas. Sair de um
não derruba o outro, e isso é o comportamento certo.
