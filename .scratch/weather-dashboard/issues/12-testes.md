# Estratégia de teste

Type: grilling
Status: resolved
Blocked by: 09, 11

## Question

O que merece teste no spec?

## Answer

Priorizado por onde erros **de fato ocorreram** durante este mapa, não por cobertura teórica. Três bugs reais apareceram enquanto o mapa era construído, e os três viram teste.

### Backend: pytest, por prioridade

**1. Parsing da resposta da Open-Meteo** — a fonte dos erros observados.

- **`results` ausente**: quando o geocoding não acha nada, a chave **some** em vez de vir vazia ([ticket 01](01-campos-open-meteo.md)). `d["results"]` levanta `KeyError` em vez de devolver "cidade não encontrada". *Bug observado na leitura da API.*
- **Índice de coluna do `cities15000`**: filtrar `feature_code` por `[6]` em vez de `[7]` devolve **zero** cidades, silenciosamente ([ticket 13](13-geolocation.md)). *Bug cometido nesta sessão.* Teste: carregar o dataset e afirmar `len(rows) > 30000`.
- **Timestamps sem offset**: são horário de parede local; tratá-los como UTC desloca o gráfico em horas ([ticket 09](09-payload.md)). Teste: uma cidade com offset não-zero, afirmando que a hora sobrevive ao round-trip.

**2. Derivação de pseudo-alertas** — lógica própria, com limiares, e onde a primeira regra proposta estava errada.

- Wellington (rajada 86 km/h em 5 de 7 dias) → **1 card**, não 5. *Este é o teste de regressão do dedup por categoria* ([ticket 07](07-regra-alertas.md)).
- Cairo e Singapura → **zero** alertas (estado vazio é caminho normal, não exceção).
- Miami → chuva **e** tempestade, dois cards distintos.
- Fronteiras: 59,9 vs 60,0 km/h; 19,9 vs 20,0 mm.

Fixtures gravadas de `probe-alertas.json`, que já tem as 6 cidades com perfis contrastantes.

**3. Mapeamento WMO** — tabela pura, ~28 casos, quebra em silêncio.

Todo código emitido tem texto e ícone; código desconhecido cai em fallback em vez de `KeyError`. Casos 96/99 (documentados como Europa Central) incluídos.

**4. Cache** — acerto, expiração por TTL, arredondamento da chave.

Relógio injetado, sem `sleep`. Coordenadas próximas arredondando para a mesma chave é a parte que erra na prática.

**5. Seleção de cidades próximas** — os casos que já falharam com critérios ingênuos ([ticket 08](08-criterio-proximidade.md)).

Berlim → vizinhas reais, não subúrbios. Basileia → mistura três países. Reykjavik e Papeete → degradam para anéis largos em vez de retornar vazio. Honolulu **não** retorna megalópole chinesa — *regressão do critério de raio fixo que falhou.*

### Rede: mockada, com um teste de contrato à parte

Testes unitários usam **fixtures gravadas** via `respx` (casa com `httpx`, do [ticket 11](11-scaffold.md)). Determinísticos, offline, rápidos.

**Um** teste de contrato bate na API real, marcado `@pytest.mark.contract` e **fora da suíte padrão** (`-m "not contract"`). Ele afirma apenas que os campos usados continuam presentes — não valores. Roda sob demanda. Justificativa: a Open-Meteo é dependência externa sem versionamento; quando mudar o formato, o erro precisa ser legível, não um `KeyError` em produção. Mas fazer a suíte depender de rede a torna intermitente.

### Frontend: sem testes unitários

TypeScript já cobre a classe de erro que mais importa aqui (campo errado do payload), via os tipos do [ticket 09](09-payload.md). Componentes de apresentação sem lógica própria não rendem testes úteis — o critério é fidelidade visual, julgada olhando, como no [ticket 10](10-tokens-visuais.md).

**Uma exceção**, se a implementação revelar dor: a formatação de datas e horas a partir dos timestamps sem offset. É a lógica que o TS não protege.

### Fora de escopo

E2E (Playwright), testes de carga, e testes visuais de regressão. Um app de uma página com dois endpoints não os justifica; acrescentam infraestrutura de CI que o destino (o spec) não pede.
