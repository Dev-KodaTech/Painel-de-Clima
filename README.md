# Painel de Clima

Mostra o clima de uma cidade: condições atuais, tendência horária, previsão de
sete dias, sol, precipitação, condições previstas e cidades vizinhas. Os dados
vêm da Open-Meteo, sempre através do backend próprio — o frontend nunca fala
com a API externa.

Spec: [`.scratch/weather-dashboard/spec.md`](.scratch/weather-dashboard/spec.md)

## Requisitos

- Python ≥ 3.11 e [uv](https://docs.astral.sh/uv/)
- Node ≥ 20 e npm

## Subir o ambiente

Dois comandos, em dois terminais.

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

O teste de contrato bate na API real e fica fora da execução padrão. Para
rodá-lo sob demanda:

```bash
cd backend && uv run pytest -m contract
```

## Endpoints

| Endpoint | Para que serve |
|---|---|
| `GET /api/cities?q=` | Candidatas de cidade para desambiguação, com estado, país e população. Nada encontrado devolve `200` com lista vazia. |
| `GET /api/weather?latitude=&longitude=&name=` | O painel da cidade escolhida. A identidade da cidade vem de `/api/cities` e viaja de volta como parâmetro. |

A documentação interativa fica em http://localhost:8000/docs, gerada dos
modelos Pydantic.

Quatro detalhes do contrato que surpreendem:

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

## Páginas

Seis, alcançáveis pela barra lateral. Só a **Visão geral** está construída; as
outras cinco existem como rota e mostram o que vai entrar nelas.

| Rota | Página |
|---|---|
| `/` | Visão geral — o grid de nove painéis |
| `/tendencia` | Tendência |
| `/vizinhas` | Cidades vizinhas |
| `/condicoes` | Condições previstas |
| `/semana` | Sete dias |
| `/ajustes` | Ajustes |

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

Envelope, sino, avatar e o ícone de saída da barra lateral são **decoração
inerte**, não botões: não há cadastro, e um botão que aceita o clique sem
responder promete o que não cumpre. O toggle sol/lua saiu desta lista — com o
tema escuro implementado, ele é um `<button>` de verdade.

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

O Tailwind v4 é CSS-first: os tokens de design ficam num bloco `@theme` em
[`frontend/src/index.css`](frontend/src/index.css). Não existe
`tailwind.config.js` nem `postcss.config.js` — quem vem da v3 vai procurá-los.
