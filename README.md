# Painel de Clima

Mostra o clima de uma cidade: condições atuais, tendência horária, previsão de
sete dias na Visão geral e dezesseis na página Calendário, sol, precipitação,
condições previstas, alertas oficiais do INMET, cidades vizinhas e notícias de
clima. Os dados vêm de APIs públicas — Open-Meteo, INMET e feeds RSS —, sempre
através do backend próprio: o frontend nunca fala com API externa.

Quem tem conta ganha **planos**: o que pretende fazer num dia, cruzado na
leitura com a aptidão daquele dia para aquela atividade.

Spec: [`.scratch/weather-dashboard/spec.md`](.scratch/weather-dashboard/spec.md)
· Glossário: [`CONTEXT.md`](CONTEXT.md) · Decisões: [`docs/adr/`](docs/adr/)

## Requisitos

- Python ≥ 3.11 e [uv](https://docs.astral.sh/uv/)
- Node ≥ 20 e npm
- Docker, para o Postgres — **só o banco** roda em container

## Subir o ambiente

Três comandos. O banco sobe em container; backend e frontend rodam na máquina,
porque o recarregamento automático de ambos é o que torna o desenvolvimento
tolerável — e dentro de container ele exige montagem de volumes que quebra com
frequência. Containerizar a aplicação inteira é decisão separada, para deploy.

**Banco** (porta 5433), na raiz do projeto:

```bash
docker compose up -d
cd backend && uv run alembic upgrade head
```

A porta é a **5433**, e não a 5432: a padrão do Postgres colide com qualquer
outro projeto que tenha um banco subido, e o erro do Docker (`port is already
allocated`) não diz de quem é a culpa. Dentro do container a porta continua
sendo a 5432 — quem muda é o lado de fora.

`upgrade head` é idempotente: rodá-lo de novo num banco já migrado não faz
nada. Roda-se a cada `git pull` que traga migração nova.

**Backend** (porta 8000):

```bash
cd backend && uv run uvicorn app.main:app --reload
```

**Frontend** (porta 5173):

```bash
cd frontend && npm install && npm run dev
```

Abra http://localhost:5173. O Vite encaminha `/api` para o backend, então o
browser só vê uma origem e não há CORS em desenvolvimento.

## Testes

```bash
cd backend && uv run pytest
```

A execução padrão **não precisa de banco nem de Docker**: o acesso ao banco
entra por injeção, e a suíte usa um repositório em memória que implementa a
mesma interface do de verdade. É a propriedade mais valiosa da suíte, e há
testes que existem só para protegê-la
([`test_injecao_do_banco.py`](backend/tests/test_injecao_do_banco.py)).

Dois marcadores ficam **fora** da execução padrão, cada um por depender de algo
que a suíte não quer exigir de todo mundo:

```bash
# Bate na API real da Open-Meteo. Exige rede.
cd backend && uv run pytest -m contract

# Roda contra o Postgres de verdade. Exige o container subido.
docker compose up -d
cd backend && uv run pytest -m postgres
```

Os testes `postgres` criam e destroem um banco próprio (`painel_teste`), então
não tocam no banco de desenvolvimento. Eles aplicam as **migrações** em vez de
criar as tabelas pelo schema: é o que prova que a migração produz o schema
completo num banco vazio — com `create_all`, uma migração esquecida passaria
verde.

O que eles rodam é **a mesma bateria** que a suíte padrão roda em memória
([`TestRepositorioNoPostgres`](backend/tests/test_repositorio.py) herda a
classe inteira e só troca a fixture). É o que impede as duas implementações de
divergirem: se divergirem, o caso falha ali. Sem eles, o repositório em memória
esconderia erros de SQL.

No frontend não há suíte — o que existe é tipo e lint, e o `build` roda os dois:

```bash
cd frontend && npm run build   # tsc -b && vite build
cd frontend && npm run lint    # oxlint
```

Vale saber o que isso **não** cobre, porque já mordeu mais de uma vez: nenhum
dos dois vê semântica de CSS. A grade do Calendário já ficou sem cor nenhuma
por ordem de emissão de utilitárias, e já desenhou os dezesseis dias na coluna
errada porque um `display: contents` descarta a colocação no grid — as duas
passavam no compilador e no lint, com as classes presentes no CSS. Mudança de
layout se confere no navegador, **e no build de produção**: em dev o Tailwind
gera classe sob demanda, e uma classe que só existe lá some no `dist`.

## Endpoints

| Endpoint | Para que serve |
|---|---|
| `GET /api/cities?q=` | Candidatas de cidade para desambiguação, com estado, país e população. Nada encontrado devolve `200` com lista vazia. |
| `GET /api/weather?latitude=&longitude=&name=` | O painel da cidade escolhida. A identidade da cidade vem de `/api/cities` e viaja de volta como parâmetro. |
| `GET /api/trends?latitude=&longitude=&janela=` | O histórico climatológico de uma janela temporal (7 dias, 30 dias ou 6 meses), comparado com o mesmo período do ano anterior. |
| `GET /api/condicoes?latitude=&longitude=&country_code=` | Alertas oficiais do INMET que cobrem a cidade, e as condições severas previstas. `country_code` decide se o INMET é consultado. |
| `GET /api/horizonte?latitude=&longitude=` | Os dezesseis dias da página Calendário, cada um declarando de que lado da fronteira do dia 8 está, e a aptidão dos sete primeiros. |
| `GET /api/noticias` | Notícias de clima e meio ambiente dos três veículos. **A única rota sem parâmetro**: as matérias são nacionais. Feed fora do ar vira `status` no corpo, não erro. |
| `POST /api/cadastro` | Cria a conta com e-mail e senha, **já abre a sessão** e devolve o cookie. `409` se o e-mail já tem conta. |
| `POST /api/entrada` | Valida as credenciais e abre uma sessão nova. `401` para senha errada **e** para e-mail inexistente, com a mesma resposta. |
| `POST /api/saida` | Apaga a linha da sessão e expira o cookie. `200` mesmo sem sessão. |
| `GET /api/quem-sou` | A conta da sessão, ou `{"conta": null}`. É o que o frontend consulta ao abrir o app. |
| `POST /api/planos` | Cria um plano (título, dia, atividade) na conta da sessão. **Exige conta.** Dia no passado é aceito. |
| `GET /api/planos` | Os planos da conta, ordenados por dia. **Exige conta** — `401`, e não lista vazia, para quem não tem sessão. |
| `DELETE /api/planos/{id}` | Apaga o plano, se for de quem está pedindo. `204`. Plano de outra conta devolve `404` — nunca `403`, que confirmaria a existência. |

As três rotas de `/api/planos` são a **primeira escrita autenticada do app**:
todo o resto é leitura pública ou a própria conta. Elas passam pelo guard
[`conta_exigida`](backend/app/dependencias.py), que recusa sem distinguir cookie
ausente de sessão vencida.

A documentação interativa fica em http://localhost:8000/docs, gerada dos
modelos Pydantic.

### Conta e sessão

Cadastrar **já entra**: quem acabou de provar que sabe a senha não deveria ter
de digitá-la de novo na tela seguinte. Demonstrável por linha de comando:

```bash
curl -c cookies.txt -X POST localhost:8000/api/cadastro \
  -H 'Content-Type: application/json' \
  -d '{"email":"ana@exemplo.com","senha":"correia-de-bateria"}'

curl -b cookies.txt localhost:8000/api/quem-sou
```

Entrar e sair fecham o ciclo — e sair de verdade apaga a linha:

```bash
curl -c cookies.txt -X POST localhost:8000/api/entrada \
  -H 'Content-Type: application/json' \
  -d '{"email":"ana@exemplo.com","senha":"correia-de-bateria"}'

curl -b cookies.txt -c cookies.txt -X POST localhost:8000/api/saida
curl -b cookies.txt localhost:8000/api/quem-sou   # {"conta":null}
```

A sessão é um cookie `HttpOnly`, `SameSite=Lax`, `Secure` fora de
desenvolvimento, com linha na tabela — nunca um token no armazenamento do
navegador, que seria legível por qualquer script da página e não teria como ser
revogado antes de expirar. Ver [ADR 0005](docs/adr/0005-sessao-em-cookie-nao-jwt.md).

Cinco detalhes que surpreendem:

- **`/api/quem-sou` responde `200` mesmo sem sessão**, com `{"conta": null}`.
  Visitante sem conta é o estado normal de quem nunca entrou, não uma falha;
  `401` obrigaria o frontend a tratar como erro o caso mais comum que existe.
- **A senha é guardada como hash Argon2id** e não sai em resposta alguma, nem
  de erro. Há um teste que lê o corpo cru de cinco respostas só para garantir
  isso ([`test_conta_http.py`](backend/tests/test_conta_http.py)).
- **O CORS mudou junto**: a sessão viaja em cookie, e cookie só atravessa
  origem com `allow_credentials=True` — que por sua vez proíbe
  `allow_origins=["*"]`. Em desenvolvimento nada disso aparece, porque o proxy
  do Vite faz o browser ver uma origem só.
- **A recusa da entrada é uma só** para senha errada e e-mail inexistente —
  mesmo status e mesmo corpo. Duas respostas diferentes deixariam qualquer um
  descobrir quais e-mails têm conta, testando um por um. A entrada sem conta
  ainda verifica a senha contra um hash de descarte, para gastar o mesmo tempo:
  sem isso, a diferença de ~40 ms entregaria pelo relógio o que as mensagens
  iguais escondem.
- **`/api/saida` responde `200` sem sessão nenhuma.** Quem chega ali sem cookie
  queria estar fora, e está; um `401` distinguiria o identificador que um dia
  existiu do que nunca existiu. Uma conta pode ter várias sessões, e sair de uma
  não derruba as outras.

### Planos

Com o cookie em mãos, o ciclo inteiro por linha de comando:

```bash
curl -b cookies.txt -X POST localhost:8000/api/planos \
  -H 'Content-Type: application/json' \
  -d '{"titulo":"Lavar as cortinas","dia":"2026-09-19","atividade":"lavar_roupa"}'

curl -b cookies.txt localhost:8000/api/planos
curl -b cookies.txt -X DELETE localhost:8000/api/planos/1 -o /dev/null -w '%{http_code}\n'
```

A isolação entre contas não é dedução: apagar plano alheio e apagar plano
inexistente devolvem **o mesmo status e o mesmo corpo**, e há um caso
([`test_o_plano_alheio_e_o_inexistente_respondem_igual`](backend/tests/test_planos_http.py))
que compara as duas respostas em vez de só conferir o `404` de cada uma — que é
a propriedade de verdade. `403` no plano alheio confirmaria que ele existe, e
quem testasse identificadores mapearia os planos dos outros sem ler nenhum.

### O contrato do payload

Seis detalhes que surpreendem:

- `current.high` e `current.low` vêm do bloco **diário** da Open-Meteo, que não
  os fornece em `current`.
- Os horários viajam **sem sufixo de fuso** (`2026-09-14T03:00`) e são horário
  de parede da cidade consultada, acompanhados de `timezone` e
  `utc_offset_seconds`. Interpretá-los como UTC desloca tudo em horas.
- `nearby[].distance_km` é **obrigatório**. Numa cidade isolada as vizinhas
  estão a milhares de quilômetros, e "Auckland — 4.094 km" é honesto onde
  "Auckland" sozinha sugeriria uma vizinhança que não existe.
- `nearby[].latitude` e `nearby[].longitude` vêm **exatas**, ao contrário de
  `distance_km`, que vem arredondada ao quilômetro na mesma linha. A distância
  é um número lido; a coordenada é consumida por um mapa, e arredondá-la poria
  o marcador longe do ponto que mediu a distância.
- Em `/api/horizonte`, o dia do **horizonte longo** chega com `icon`,
  `description` e `aptidoes` vazios, e isso é a regra e não a borda: o backend
  não envia o que a interface não deve exibir. A partir do dia 8 a fonte troca
  de modelo e a confiança cai, então não há céu a afirmar nem aptidão a julgar —
  só a probabilidade de chuva
  ([ADR 0010](docs/adr/0010-dezesseis-dias-e-a-fronteira-do-dia-oito.md)). Cada
  dia **declara** de que lado está, em vez de deixar a fronteira como regra de
  índice que os dois lados precisariam manter iguais.
- Ainda em `/api/horizonte`, a **borda vem incompleta**: medido contra o serviço
  real, máxima, mínima e chuva do último dia podem vir `null`, variando com a
  cidade e a hora local. A célula omite o que não veio; ela não some.

## Páginas

Sete, alcançáveis pela barra lateral. Seis estão construídas; **Ajustes** existe
como rota e mostra o que vai entrar nela.

| Rota | Página | |
|---|---|---|
| `/` | Visão geral — o grid de nove painéis | ✓ |
| `/tendencia` | Tendência — histórico climatológico e métricas da janela temporal | ✓ |
| `/vizinhas` | Cidades vizinhas — tabela comparativa e mapa da região | ✓ |
| `/condicoes` | Condições — alertas do INMET e condições previstas, em duas seções | ✓ |
| `/calendario` | Calendário — dezesseis dias, aptidão e os planos de quem tem conta | ✓ |
| `/noticias` | Notícias — matérias de clima dos três veículos | ✓ |
| `/ajustes` | Ajustes | — |

**Locais salvos** aparece no glossário e já tem tabela no banco, mas ainda não
tem rota nem página: o `CONTEXT.md` conta oito páginas e a barra mostra sete, e
a diferença é essa. Quando entrar, as duas contagens voltam a bater.

Duas páginas fogem do padrão "a mesma URL mostra o mesmo para todo mundo":

- **Notícias** é a única que não é sobre a cidade escolhida — as matérias são
  nacionais e continuam as mesmas em Sorocaba e em Belém
  ([ADR 0009](docs/adr/0009-noticias-por-rss-nao-por-api.md)). Por isso o
  cabeçalho esconde a busca ali, como em Ajustes.
- **Calendário** é **mista**, e é a única assim: a previsão e a aptidão são
  função da cidade e viajam na URL; só a faixa de planos é função da conta. Sem
  conta, a grade e a aptidão funcionam inteiras e no lugar da faixa vai um
  convite — a página não exige conta para nada além dos planos.

**A cidade escolhida mora na URL**, não em estado de componente — ver
[ADR 0002](docs/adr/0002-cidade-na-url.md). São seis parâmetros
(`lat`, `lon`, `name`, `cc`, `country`, `admin1`) porque `/api/weather` exige
`country_code` e usa os outros para montar o `location`. Consequências:
`/vizinhas?lat=52.52&lon=13.41&name=Berlin&cc=DE&country=Germany&admin1=Land+Berlin`
é um link que abre a mesma cidade na mesma página, e trocar de página não
refaz a requisição.

Em produção o servidor precisa devolver `index.html` para qualquer caminho, ou
recarregar em `/vizinhas` dá 404. O dev server e o `vite preview` já fazem
isso; deploy continua fora de escopo.

Envelope e sino são **decoração inerte**, não botões: não há e-mail nem
notificação, e um botão que aceita o clique sem responder promete o que não
cumpre. Dois saíram desta lista ao ganharem função — o toggle sol/lua, com o
tema escuro, e o avatar com o ícone de saída, com a conta: o avatar virou o
e-mail de quem está entrado, e a saída, um `<button>` que encerra a sessão de
verdade.

## Conta e sessão no frontend

O estado da conta vive na **rota de layout**, junto do painel, e chega às
páginas pelo contexto do outlet — a mesma mecânica que o painel já usa. É
consultado **uma vez** ao abrir o app, em `/api/quem-sou`; navegar entre
páginas não o refaz, e o que o mantém em dia depois disso são o cadastro, a
entrada e a saída, que já sabem o que mudou.

Cadastrar **entra direto**: o backend abre a sessão e carimba o cookie na
própria resposta do cadastro, então não há uma chamada de entrada em seguida.

`credentials: "include"`, nos dois helpers de `api/client.ts`, são os **únicos
pontos do frontend que sabem que existe sessão**. Nenhum componente lê, escreve
ou anexa cookie — nem conseguiria: o cookie é `HttpOnly` e não é legível por
script algum, inclusive o nosso ([ADR 0005](docs/adr/0005-sessao-em-cookie-nao-jwt.md)).

Cadastro e entrada **não são páginas da barra lateral** e ficam fora de
`PAGINAS`: são telas que se visita uma vez, alcançáveis pelo cabeçalho de
qualquer página. Os links preservam a cidade da URL, então entrar a partir de
um painel carregado volta para o mesmo painel.

As outras páginas continuam funcionando **sem conta nenhuma**, como sempre
funcionaram: a entrada não é pedágio para nada que já existia. O Calendário é o
caso que mostra até onde isso vai: ele tem conteúdo de conta e mesmo assim serve
a grade, a aptidão e o detalhe do dia inteiros para quem nunca entrou.

**Sessão vencida no meio de um envio** é caminho próprio, e não uma falha
qualquer. O `401` de uma rota de conta vira `SessaoExpirada` no cliente, e quem
o trata oferece o link de entrada em vez de "tente de novo" — tentar outra vez
com a mesma sessão morta falha igual. O formulário de plano **não limpa o que
foi digitado** nesse caminho: quem escreveu "lavar as cortinas da sala" e viu a
sessão vencer entra de novo e a frase continua no campo. É o único formulário do
app em que havia texto a perder, porque é a única escrita autenticada.

## Cidade inicial e tema

O painel abre já preenchido quando dá para saber qual cidade mostrar. A ordem é
**cidade detectada → última cidade → estado vazio**, e toda falha cai para o
degrau seguinte em silêncio.

*Detectada* quer dizer resolvida **por nós** a partir da coordenada — o
navegador entrega coordenada, nunca cidade. E ela só é buscada quando
`navigator.permissions.query` responde que a permissão **já foi concedida**:
nenhum pop-up é disparado no carregamento, nunca. Um pedido automático no
primeiro acesso é negado por reflexo, e o browser lembra a negação.

O tema claro/escuro vive no atributo `data-tema` do `<html>`, carimbado por um
**script inline no `index.html`** antes do primeiro paint — com `useEffect`,
quem usa escuro veria a página branca por 100–300 ms em toda visita. A chave do
armazenamento está duplicada entre o HTML e `src/tema.ts`, e as duas precisam
concordar; é o preço de não piscar.

O tema escuro é só um segundo bloco de variáveis em
[`index.css`](frontend/src/index.css): as utilitárias do Tailwind v4 apontam
para `var(--color-*)`, então nenhum componente muda. **Duas exceções que
surpreendem:**

- A **sombra não** é variável na utilitária — o Tailwind assa o valor em tempo
  de build. Por isso o aro que separa cartão de fundo no escuro entra
  sobrescrevendo `--tw-shadow`, um nome interno do Tailwind. Se um dia os
  cartões escuros perderem o contorno, é aí que se olha.
- `--color-brand` **não** clareia no escuro, ao contrário do resto da paleta.
  Sobre cartão branco, azul-sobre-fundo e branco-sobre-azul dão a mesma razão de
  contraste; sobre cartão escuro elas divergem, e o que decide é o texto branco
  de 10 px na coluna de hoje. Para o azul como *texto* existe
  `--color-brand-text`, usado só onde o azul é texto.

## Configuração

| Variável | Padrão | Para que serve |
|---|---|---|
| `CORS_ORIGINS` | vazio | Origens permitidas, separadas por vírgula. Só é necessária quando frontend e backend forem servidos de origens diferentes; em dev o proxy do Vite dispensa. |
| `DATABASE_URL` | o banco local na 5433 | A URL do Postgres. O esquema precisa ser `postgresql+psycopg://` — o driver é o psycopg 3, e sem o sufixo o SQLAlchemy procura o psycopg2 e reclama de um pacote que ninguém pediu. |
| `AMBIENTE` | `producao` | Só `desenvolvimento` muda alguma coisa: tira o `Secure` do cookie de sessão, que em `http://localhost` impediria o cookie de voltar. O padrão é o seguro — quem não configura nada leva `Secure`. |

As três têm padrão no código, então um `.env` vazio funciona em desenvolvimento.
[`backend/.env.example`](backend/.env.example) documenta as três; o `.env` real
não entra no git.

### O banco

Quatro tabelas — **contas**, **sessões** e **locais salvos** pela migração
inicial, **planos** pela segunda. Quatro e nada mais: o cache da API externa
continua em memória, porque cache que some no restart é cache funcionando, e o
conjunto de cidades do GeoNames continua sendo o arquivo lido no boot, porque é
dado que nunca muda.

**Nem `locais_salvos` nem `planos` guardam clima.** É a mesma regra nas duas, e
pelo mesmo motivo: clima guardado envelhece, e alguém veria a previsão de
anteontem sem saber que é de anteontem. O plano guarda título, dia e atividade;
a previsão e a aptidão são buscadas frescas e cruzadas na leitura.

Cinco garantias moram no **schema**, e não no código que escreve nele — é o que
as mantém verdadeiras para quem insere por outro caminho:

- o e-mail da conta é único **sem diferenciar maiúsculas**, por um índice
  funcional sobre `lower(email)`;
- apagar uma conta leva suas sessões, seus locais salvos e seus planos junto,
  por `ON DELETE CASCADE`;
- um local salvo não se repete dentro da mesma conta, por unicidade de
  `(conta_id, identidade)` — e `identidade` é a coordenada arredondada a duas
  casas mais o código do país, porque comparar pelo nome falharia com grafias
  diferentes da mesma cidade;
- a atividade de um plano é uma das quatro, por um `CHECK`. Fechar o valor no
  banco vale para quem insere por SQL direto; `ENUM` nativo daria a mesma
  garantia e foi rejeitado pelo custo de mudar — a quinta atividade exigiria um
  `ALTER TYPE`, que no Postgres não roda em toda transação;
- `planos.dia` é `DATE` e não `TIMESTAMP`. A ausência de hora é decisão de
  domínio — a aptidão é diária —, e o tipo é o que impede que uma hora entre por
  descuido: um `datetime` aceito na rota seria truncado em silêncio, e quem
  mandasse `14:00` acreditaria que ela foi guardada.

Para criar uma migração depois de mexer em
[`backend/app/db/schema.py`](backend/app/db/schema.py):

```bash
cd backend && uv run alembic revision --autogenerate -m "o que mudou"
```

Revise o arquivo gerado antes de aplicá-lo — o `--autogenerate` não detecta
renomeação de coluna, que ele vê como uma coluna apagada e outra criada.

## Cidades vizinhas: o dataset local

A Open-Meteo não tem busca por proximidade nem por região — procurar por
"California" devolve apenas lugares *chamados* California, nunca Los Angeles.
As cidades vizinhas saem de um dataset local: o dump
[`cities15000`](https://download.geonames.org/export/dump/) do GeoNames
(CC BY 4.0), **versionado comprimido** em
[`backend/app/data/cities15000.zip`](backend/app/data/cities15000.zip).

Versionado, e não baixado no build, porque um passo de download falha offline.
Comprimido (3,2 MB) e não expandido (8,4 MB) porque descomprimir custa ~29 ms
dos ~214 ms da carga e poupa 5 MB no repositório. A carga acontece no startup,
via `lifespan`, e a busca é linear — nesta escala nenhum índice espacial se
justifica.

Para atualizar o dump (ele muda poucas vezes por ano), basta substituir o zip.

Ao mexer no carregamento, atenção à coluna: `feature_code` é a **`[7]`**. A
`[6]` é `feature_class`, que vale `'P'` nas 34.136 linhas — filtrá-la por
`PPL` devolve **zero cidades em silêncio**, sem exceção alguma, e o painel de
vizinhas fica permanentemente vazio. O teste de carga
(`test_dataset_carrega_as_cidades_do_dump`) existe para travar essa regressão.

## Estrutura

- `backend/` — FastAPI. Busca, combina e traduz os dados da Open-Meteo.
- `frontend/` — React + TypeScript + Vite, Tailwind v4.
- `compose.yaml` — o Postgres, e só ele.

No backend, o banco mora em quatro lugares com papéis distintos:
`app/db/schema.py` é o schema, `app/db/repositorio.py` é o acesso (a interface
e as duas implementações), `app/db/transacao.py` é o `engine` e a unidade de
trabalho, e `app/repositorio_do_processo.py` é o ponto de injeção — a mesma
mecânica de `app/cache_do_processo.py`, e de propósito: quem sabe ler um sabe
ler o outro.

`transacao.py` não se chama `sessao.py` porque `CONTEXT.md` reserva *sessão*
para a prova de que quem está pedindo é o dono da conta. A sessão do SQLAlchemy
é outra coisa, e dois sentidos no mesmo nome dentro do mesmo pacote é o tipo de
colisão que faz alguém ler `sessao.criar()` e entender o contrário.

O Tailwind v4 é CSS-first: os tokens de design ficam num bloco `@theme` em
[`frontend/src/index.css`](frontend/src/index.css). Não existe
`tailwind.config.js` nem `postcss.config.js` — quem vem da v3 vai procurá-los.
# Painel-de-Clima
