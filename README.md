# Painel de Clima

Painel único que mostra o clima de uma cidade: condições atuais, tendência
horária, previsão de sete dias, sol, precipitação, condições previstas e
cidades vizinhas. Os dados vêm da Open-Meteo, sempre através do backend
próprio — o frontend nunca fala com a API externa.

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

Dois detalhes do contrato que surpreendem:

- `current.high` e `current.low` vêm do bloco **diário** da Open-Meteo, que não
  os fornece em `current`.
- Os horários viajam **sem sufixo de fuso** (`2026-09-14T03:00`) e são horário
  de parede da cidade consultada, acompanhados de `timezone` e
  `utc_offset_seconds`. Interpretá-los como UTC desloca tudo em horas.

## Configuração

| Variável | Padrão | Para que serve |
|---|---|---|
| `CORS_ORIGINS` | vazio | Origens permitidas, separadas por vírgula. Só é necessária quando frontend e backend forem servidos de origens diferentes; em dev o proxy do Vite dispensa. |

## Estrutura

- `backend/` — FastAPI. Busca, combina e traduz os dados da Open-Meteo.
- `frontend/` — React + TypeScript + Vite, Tailwind v4.

O Tailwind v4 é CSS-first: os tokens de design ficam num bloco `@theme` em
[`frontend/src/index.css`](frontend/src/index.css). Não existe
`tailwind.config.js` nem `postcss.config.js` — quem vem da v3 vai procurá-los.
