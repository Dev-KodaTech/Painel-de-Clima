# Painel de Clima (Weather Dashboard)

Status: ready-for-agent

Origem: [mapa do wayfinder](map.md), 14 tickets resolvidos. Cada decisão abaixo remete ao ticket que a resolveu.

## Problem Statement

Uma pessoa quer saber como está o tempo numa cidade e como estará nos próximos dias. Hoje isso exige abrir um serviço de previsão genérico, e as informações que interessam — temperatura agora, tendência ao longo do dia, os próximos sete dias, nascer e pôr do sol, chuva prevista, se há algo severo a caminho — ficam espalhadas por abas e telas diferentes, cada uma com publicidade e ruído em volta.

Falta um painel único, denso e legível, onde digitar o nome de uma cidade mostra tudo isso de uma vez.

## Solution

Uma aplicação web de página única com nove painéis num grid de desktop. A pessoa digita o nome de uma cidade, escolhe entre as candidatas quando há ambiguidade, e vê imediatamente: condições atuais, tendência horária de temperatura, previsão de sete dias, nascer e pôr do sol, precipitação diária, condições severas previstas e a temperatura em cidades vizinhas. Opcionalmente, um botão usa a localização do navegador para sugerir a cidade.

Os dados vêm da API pública Open-Meteo, que não exige chave. O frontend nunca fala com a Open-Meteo: consome apenas o backend próprio, que busca, combina, traduz e serve tudo pronto.

## User Stories

1. Como visitante, quero digitar o nome de uma cidade, para ver o clima dela sem navegar por menus.
2. Como visitante que digitou um nome ambíguo, quero escolher entre as cidades candidatas, para não receber o clima da Springfield errada.
3. Como visitante escolhendo entre candidatas, quero ver estado, país e população de cada uma, para distingui-las com segurança.
4. Como visitante, quero ver a temperatura atual em destaque, para saber a informação mais importante num relance.
5. Como visitante, quero ver a sensação térmica, para me vestir adequadamente e não só pela temperatura medida.
6. Como visitante, quero ver a descrição do tempo em palavras ("Nublado", "Pancadas de chuva"), para interpretar sem decorar códigos.
7. Como visitante, quero ver um ícone que represente as condições, para reconhecer o tempo visualmente antes de ler.
8. Como visitante, quero ver a máxima e a mínima do dia, para saber o que esperar das próximas horas.
9. Como visitante, quero ver o nome e o país da cidade exibida, para confirmar que é a que pedi.
10. Como visitante, quero ver a data de hoje na cidade consultada, para me situar quando ela está em outro fuso.
11. Como visitante, quero ver a tendência de temperatura ao longo do dia num gráfico, para saber quando esfria ou esquenta.
12. Como visitante, quero ver marcada a hora atual no gráfico, para me localizar na curva.
13. Como visitante, quero ver a previsão dos próximos sete dias, para planejar a semana.
14. Como visitante, quero ver ícone, máxima e mínima de cada dia da semana, para comparar os dias rapidamente.
15. Como visitante, quero ver o dia de hoje destacado entre os sete, para me orientar na sequência.
16. Como visitante, quero ver o horário do nascer do sol, para planejar atividades matinais.
17. Como visitante, quero ver o horário do pôr do sol, para saber quanto resta de luz natural.
18. Como visitante, quero ver a precipitação prevista para cada um dos sete dias, para saber quando levar guarda-chuva.
19. Como visitante, quero ver as precipitações comparadas visualmente em barras, para identificar o dia mais chuvoso sem ler números.
20. Como visitante, quero ser avisado de condições severas previstas, para me preparar com antecedência.
21. Como visitante, quero que cada aviso diga qual dia e qual a intensidade, para julgar a gravidade.
22. Como visitante, quero que os avisos deixem claro que são derivados da previsão, para não confundi-los com alertas oficiais de defesa civil.
23. Como visitante numa semana tranquila, quero ver que não há condições severas, para ter certeza de que o painel funcionou e não ficou em branco por erro.
24. Como visitante, quero ver a temperatura de cidades vizinhas, para comparar com a região em volta.
25. Como visitante vendo cidades vizinhas, quero saber a distância de cada uma, para avaliar o quão relevante é a comparação.
26. Como visitante numa cidade isolada, quero que as vizinhas mostradas façam sentido geográfico, mesmo que distantes.
27. Como visitante numa cidade de fronteira, quero ver vizinhas de países diferentes, porque proximidade importa mais que nacionalidade.
28. Como visitante, quero clicar num botão para usar minha localização, para não precisar digitar o nome da minha cidade.
29. Como visitante, quero que minha localização seja pedida só quando eu clicar, para não ser importunado ao abrir a página.
30. Como visitante que negou a permissão de localização, quero usar o painel normalmente pela busca, sem mensagens de erro insistentes.
31. Como visitante longe de qualquer cidade cadastrada, quero que nada seja sugerido, em vez de receber uma cidade a centenas de quilômetros.
32. Como visitante, quero ver um indicador de carregamento enquanto os dados chegam, para saber que a aplicação está trabalhando.
33. Como visitante que digitou uma cidade inexistente, quero uma mensagem clara de que não foi encontrada, para corrigir o que digitei.
34. Como visitante, quero uma mensagem compreensível quando o serviço de clima está fora do ar, para saber que o problema não é meu.
35. Como visitante, quero ver de onde vêm os dados, para julgar sua confiabilidade.
36. Como visitante, quero que os horários exibidos sejam os da cidade consultada, para que "pôr do sol às 19:23" signifique 19:23 lá.
37. Como operador, quero que consultas repetidas à mesma cidade sejam servidas de cache, para não esgotar a cota da API externa.
38. Como desenvolvedor, quero que o frontend consuma apenas o backend próprio, para que a fonte de dados possa mudar sem tocar na interface.
39. Como desenvolvedor, quero tipos que descrevam a resposta da API, para que um campo errado quebre na compilação e não em produção.
40. Como desenvolvedor, quero rodar backend e frontend localmente com dois comandos, para começar a trabalhar sem configuração elaborada.

## Implementation Decisions

### Arquitetura geral

Dois projetos independentes na raiz — `backend/` (Python, FastAPI) e `frontend/` (React, TypeScript, Vite, Tailwind) — sem monorepo: nada é compartilhado além do formato JSON, e um workspace só acrescentaria cerimônia. ([ticket 11](issues/11-scaffold.md))

Ferramentas escolhidas por estarem instaladas na máquina de desenvolvimento, não por preferência abstrata: **uv** (poetry, pipenv e pdm ausentes) e **npm** (pnpm, yarn e bun ausentes). Python mínimo 3.11; FastAPI exige ≥3.10. HTTP via **httpx** (async, casa com FastAPI).

**Tailwind v4**, que é CSS-first: os tokens vão num bloco `@theme` no CSS, e não existe `tailwind.config.js` nem `postcss.config.js`. Quem conhece a v3 vai procurar esses arquivos.

Em desenvolvimento, o Vite encaminha `/api` para o backend, o que dispensa CORS — o browser só vê a origem do Vite. O middleware de CORS fica configurado mesmo assim, lendo origens permitidas de variável de ambiente e vazio por padrão; sem isso, o primeiro deploy que separe as origens quebra com um erro obscuro.

### Contrato da API

Dois endpoints. ([ticket 06](issues/06-contrato-backend.md))

**`GET /api/cities`** — resolve texto ou coordenada em candidatas de cidade. Aceita `q` (texto) **ou** `lat`+`lon`, mutuamente exclusivos; ambos ou nenhum é `400`. No modo texto devolve as candidatas para desambiguação; no modo coordenada, no máximo uma. Separado do endpoint de clima porque dispara a cada tecla digitada e não pode arrastar a previsão junto. ([ticket 13](issues/13-geolocation.md))

**`GET /api/weather`** — recebe a cidade e devolve o painel completo, um objeto por painel da interface: `location`, `current`, `hourly`, `daily`, `sun`, `alerts`, `nearby`, `units`, `attribution`. Cerca de 3,5 KB minificado. Agrupado em vez de achatado, para que cada painel leia uma chave e o frontend não precise saber de qual bloco da API externa cada campo veio. ([ticket 09](issues/09-payload.md))

Detalhes do contrato que não são óbvios:

- `current.high` e `current.low` vêm do bloco diário, não do atual — a API externa não os fornece em `current`, embora o design os mostre no card de hoje.
- Um único bloco `daily` alimenta dois painéis (previsão da semana e precipitação); o design mostra os mesmos sete dias em ambos.
- `hourly` traz as **24 horas do dia corrente**, 00:00 a 23:00. A API externa começa o bloco horário à meia-noite, não "agora": às 02:00 quase tudo seria futuro, às 22:00 quase tudo passado. O frontend marca a hora atual na curva.
- `nearby[].distance_km` é obrigatório. Para uma cidade isolada, "Auckland — 4.094 km" é honesto; o mesmo item sem a distância seria enganoso.
- `units` é fixo (`°C`, `mm`, `km/h`, `km`) e viaja no payload mesmo assim, para que o frontend nunca tenha unidade escrita no código.
- `attribution` é uma string pronta; CC-BY 4.0 é exigido pela Open-Meteo e pelo GeoNames.

### Módulos do backend

- **Cliente da API externa** — faz as requisições e trata as armadilhas de formato descritas abaixo.
- **Geocodificação** — resolve nome em candidatas; resolve coordenada em cidade via dataset local.
- **Cidades vizinhas** — seleciona as vizinhas a partir do dataset local.
- **Alertas** — deriva as condições severas da previsão.
- **Tabela WMO** — traduz código em texto e nome de ícone.
- **Cache** — em memória, TTL de 10 minutos, chave por coordenada arredondada. Os dados da fonte atualizam a cada ~15 minutos, então um dicionário com timestamp basta; sem Redis.
- **Modelos** — Pydantic espelhando o payload 1:1, servindo de contrato e gerando o schema OpenAPI.

### Duas chamadas à API externa, não uma

A Open-Meteo aceita **múltiplas coordenadas numa única requisição** (`latitude=a,b,c&longitude=x,y,z`), devolvendo um array na ordem de entrada, com `timezone=auto` resolvido por localização. Testado com até 200 pares. ([ticket 08](issues/08-criterio-proximidade.md))

Mas as variáveis pedidas valem para **todas** as coordenadas: não há como pedir "tudo para a cidade principal, só temperatura para as vizinhas". Medido:

| Estratégia | Bytes | Requisições |
|---|---|---|
| Uma chamada, 6 coordenadas, todas as variáveis | 32.791 | 1 |
| **Duas chamadas (principal completa + vizinhas só `current`)** | **7.417** | **2** |

Duas chamadas economizam **77% de banda** e custam 2 de 10.000 requisições diárias — a cota é irrelevante aqui, e o cache reduz mais. Banda vence.

### Seleção de cidades vizinhas

Não existe busca por proximidade na API externa, e **não existe busca por região**: procurar por "California" devolve apenas lugares chamados California (incluindo uma no Missouri com 4.396 habitantes), nunca Los Angeles. A seleção é local, sobre o dump **cities15000** do GeoNames (3,2 MB comprimido, 8 MB em disco, 34.136 linhas, CC-BY 4.0), versionado no repositório — baixá-lo no build acrescentaria um passo que falha offline.

Carregado no startup via `lifespan`: **85 ms** para parsear, **8,8 MB** em memória. Busca linear com haversine resolve em 40–55 ms; nenhum índice espacial é necessário nesta escala.

**Índices das colunas** (base zero, verificados no arquivo real de 19 campos): `[1]` nome, `[4]` latitude, `[5]` longitude, `[6]` **feature_class**, `[7]` **feature_code**, `[8]` país, `[10]` admin1, `[14]` população, `[17]` fuso. Filtrar por `[6]` em vez de `[7]` devolve **zero cidades, silenciosamente** — erro cometido durante a investigação.

O algoritmo, derivado de tentativas que falharam:

1. filtrar `feature_code` iniciando em `PPL`
2. excluir o que está a menos de ~15 km (a própria cidade)
3. percorrer anéis de raio crescente: 100 / 250 / 600 / 1500 / 5000 / 25000 km
4. em cada anel, tomar as de maior população
5. exigir ~25 km de separação entre as escolhidas

Duas abordagens mais simples foram testadas e descartadas: "maior cidade num raio fixo, expandindo" mandou Reykjavik para Londres e Honolulu para megalópoles chinesas a 8.000 km; pontuar por população dividida pela distância devolveu subúrbios (Berlim → Heiligensee, Teltow). A escala de anéis é o que trata isolamento — regiões densas nunca saem do primeiro anel. Fronteiras nacionais funcionam sem caso especial porque nada no algoritmo olha o país: Basileia devolve naturalmente Mulhouse (FR), Freiburg (DE) e Berna (CH).

### Derivação das condições severas

A Open-Meteo **não tem alertas meteorológicos** — confirmado por três vias: os 14 produtos não incluem alertas, `/v1/alerts` e `/v1/warnings` devolvem 404, `current=weather_alerts` devolve 400, e o mantenedor declara não haver plano. Um segundo provedor exigiria chave de API, contra a restrição do projeto. Os avisos são derivados da própria previsão. ([tickets 02](issues/02-alertas-derivados.md) e [07](issues/07-regra-alertas.md))

Três categorias, **no máximo um card por categoria**, representando o pior dia:

| Categoria | Gatilho | Card mostra |
|---|---|---|
| Tempestade | `weather_code` ∈ {95, 96, 99} | primeiro dia, "(+N)" se houver mais |
| Vento | `wind_gusts_10m_max` ≥ 60 km/h | pior dia, valor, "(+N dias)" |
| Chuva | `precipitation_sum` ≥ 20 mm | pior dia, valor, "(+N)" |

Ordenados por data, no máximo dois exibidos. Um nível de severidade só.

**O dedup por categoria é a parte essencial**, não um refinamento. Sem ele, Wellington (cidade litorânea) dispara cinco dos sete dias com o mesmo aviso de vento: numa cidade assim, vento forte é o clima normal, e cinco cards idênticos são ruído. Testado em seis cidades de perfis opostos, o resultado com dedup fica entre **zero e dois cards** — exatamente o que o layout comporta.

Limiar **relativo ao clima da própria cidade** foi testado e **rejeitado por ser perigoso**: usando 1,5× a mediana da semana, Wellington tem mediana de rajada de 76 km/h, então 86 km/h conta como "normal" e nenhum aviso de vento é emitido numa semana com rajadas de 86. Perigo é absoluto, não relativo.

Calor e frio extremos ficam de fora: exigiriam limiar relativo ao clima local (30 °C é notícia em Reykjavik e rotina em Cuiabá), e o atalho relativo acabou de se mostrar falho.

### Localização pelo navegador

Reverse geocoding **não existe** na API externa. Resolve-se localmente com o mesmo dataset já carregado: nenhuma dependência, download ou requisição a mais. ([ticket 13](issues/13-geolocation.md))

**Raio máximo de 50 km.** Medido em 12 coordenadas de densidade oposta, há um corte natural e nenhum meio-termo: toda área povoada acerta abaixo de 5 km (Berlim 0,0; Tóquio 0,1; Londres 2,2; Fairbanks 4,3) e o caso seguinte já salta para 95 km (Amazônia), depois 149 km (Atacama), 341 km (interior da Austrália), 1.043 km (Pacífico). Qualquer limiar entre 10 e 90 km produz resultado idêntico nesses casos.

Acima de 50 km, **não sugerir nada**: cair no estado inicial com o campo vazio. Sugerir Alice Springs a quem está a 341 km dela é pior que o silêncio.

O fluxo é acionado **por um botão**, nunca no carregamento: pedido automático no primeiro acesso é negado por reflexo, e o browser lembra a negação — queima a única chance. Obtida a coordenada, o frontend resolve a cidade e **carrega o painel direto**, sem pedir confirmação: o usuário já pediu ao clicar, e o nome fica visível no campo de busca para correção.

### Armadilhas de formato da API externa

Três detalhes que quebram a integração em silêncio se ignorados: ([ticket 01](issues/01-campos-open-meteo.md))

1. **A chave `results` desaparece** da resposta do geocoding quando nada é encontrado — não vem como lista vazia. Acessá-la direto levanta exceção em vez de produzir "cidade não encontrada".
2. **`weather_code` vem apenas como inteiro.** Não há campo de texto; a unidade é literalmente `"wmo code"`. Os ~28 códigos emitidos (0–3, 45, 48, 51–57, 61–67, 71–77, 80–86, 95–99) precisam de tabela própria para virar texto e ícone. A tradução mora no **backend**, para que o frontend não conheça a tabela WMO e a regra "todo dado vem do backend" continue honesta.
3. **Os timestamps vêm sem sufixo de fuso** (`2026-09-14T06:38`). Com `timezone=auto` são horário local da cidade; interpretá-los como UTC desloca todo o gráfico em horas. Viajam no payload exatamente como vieram, acompanhados de `timezone` e `utc_offset_seconds`, e o frontend os trata como horário de parede.

Resultados fuzzy são o quarto detalhe, menos grave: buscar "Springfield" também traz "Palmyra". As candidatas devem ser exibidas com estado e país para que a escolha seja informada.

### Interface

Grid de **três faixas com proporções próprias**, não doze colunas — forçar um grid de 12 não reproduz as larguras do design: ([ticket 10](issues/10-tokens-visuais.md))

| Faixa | Proporções | Painéis |
|---|---|---|
| 1 | `1.05fr 1.5fr` | card do dia, tendência de temperatura |
| 2 | `1.35fr .75fr 1.1fr` | previsão da semana, hoje (sol), cidades próximas |
| 3 | `1.2fr 1fr` | precipitação, condições previstas |

Shell de `64px 1fr` (barra lateral fixa e conteúdo), gap de 16 px, padding de card 18 px.

Tokens, como bloco `@theme` do Tailwind v4 — extraídos do design de referência:

```css
@theme {
  --color-page:       #eceef6;  /* fundo lavanda acinzentado */
  --color-card:       #ffffff;
  --color-ink:        #1f2430;  /* texto primário */
  --color-ink-2:      #6b7280;  /* secundário */
  --color-ink-3:      #9ca3af;  /* terciário, eixos */
  --color-accent:     #f5a524;  /* laranja da temperatura grande */
  --color-brand:      #3b6ef5;  /* azul: pílula, dia ativo, barras, linha */
  --color-brand-soft: #e8eefe;
  --color-line:       #eef0f6;
  --radius-card:  20px;
  --radius-inner: 14px;
  --shadow-card:  0 8px 24px -12px rgb(31 36 48 / .18);
  --font-sans: Poppins, system-ui, sans-serif;
}
```

(Bloco extraído de um protótipo que reproduziu os nove painéis com dados reais.)

Tipografia **Poppins** (Google Fonts, geométrica arredondada como no design; alternativas equivalentes verificadas: Outfit, Plus Jakarta Sans, Figtree). Títulos de card 14 px/600, temperatura principal 42–56 px/600 com `letter-spacing: -.02em`, corpo 13 px, rótulos 10–11 px. O design é denso; texto pequeno é característica dele.

Ícones **Meteocons** via `@bybas/weather-icons` (MIT), mapeados a partir do campo `icon` do payload.

O eixo do gráfico horário usa rótulos esparsos — sete marcas, não 24, que não cabem na largura disponível.

### Desvios deliberados do design de referência

Quatro, todos com justificativa:

1. **O painel de alertas muda de nome** (algo como "Condições previstas") e cada card indica que é derivado da previsão. Alerta meteorológico é a categoria de informação em que pessoas tomam decisão de segurança, e uma derivação nossa não é aviso oficial.
2. **O card de alerta muda de conteúdo.** O design mostra uma temperatura grande com máxima e mínima ao lado do aviso — dados que nada dizem sobre vento ou tempestade. No lugar: categoria, data e o valor da métrica que disparou.
3. **O mapa ilustrado de regiões vira tabela de cidades próximas** com distância. O mapa pressupõe um país fixo, o que é incompatível com buscar qualquer cidade do mundo. A tabela já existe no design, no canto inferior direito; perde-se a ilustração.
4. **Um rodapé fino de atribuição** que o design não tem, exigido pelas licenças CC-BY 4.0.

O toggle sol/lua do cabeçalho permanece **decorativo** (ver Fora de Escopo).

## Testing Decisions

Um bom teste aqui verifica **comportamento externo observável** — o que sai dos endpoints, o que a seleção devolve — e não como o resultado foi produzido. Nenhum teste deve conhecer a estrutura interna do cliente HTTP, a forma do dicionário de cache ou a ordem das chamadas.

Não há código nem testes existentes: o repositório é novo, então não há arte prévia a seguir. As duas costuras abaixo foram escolhidas para serem as mais altas possíveis e as menos numerosas.

### Costura 1: os endpoints HTTP

`TestClient` do FastAPI com a API externa mockada por **respx** (integra com httpx). Atravessa roteamento, cliente, cache, tabela WMO, derivação de alertas e serialização de uma vez. É a costura preferida: quase tudo que merece teste passa por ela.

Casos, priorizados por **erros que de fato ocorreram** durante a investigação, não por cobertura teórica: ([ticket 12](issues/12-testes.md))

- **Cidade não encontrada** → resposta de "não encontrada", não exceção. Fixture com a chave `results` ausente, que é como a API externa responde. *Armadilha real da API.*
- **Ambiguidade** → múltiplas candidatas com estado, país e população.
- **Painel completo** → as nove chaves presentes, `hourly` com 24 pontos, `daily` com 7, `units` preenchido, `attribution` não vazio.
- **Fuso preservado** → cidade com offset não-zero; os horários sobrevivem ao trajeto sem deslocamento. *Armadilha real da API.*
- **Alertas, Wellington** → **um** card de vento, não cinco. *Regressão da regra sem dedup, que estava errada.*
- **Alertas, Cairo e Singapura** → lista vazia; o estado vazio é caminho normal, não exceção.
- **Alertas, Miami** → dois cards distintos (chuva e tempestade).
- **Fronteiras de limiar** → 59,9 contra 60,0 km/h; 19,9 contra 20,0 mm.
- **Cache** → duas requisições iguais produzem uma só chamada externa; após o TTL, duas. Relógio injetado, sem `sleep`.
- **API externa fora do ar** → erro tratado, com mensagem compreensível.
- **Parâmetros inválidos em `/api/cities`** → `q` e `lat`/`lon` juntos, ou nenhum, devolvem `400`.
- **Coordenada distante** → acima de 50 km, nenhuma sugestão.

As fixtures reaproveitam respostas reais já gravadas durante a investigação, que cobrem seis cidades de perfis climáticos contrastantes.

### Costura 2: seleção de cidades vizinhas

Função pura sobre o dataset real, sem HTTP. Merece costura própria porque os casos que importam exigem as 34 mil linhas, e amarrá-los a requisições os tornaria lentos e indiretos.

- **Berlim** → vizinhas reais (Potsdam, Oranienburg), não subúrbios do próprio município.
- **Basileia** → mistura três países sem tratamento especial.
- **Honolulu** → **não** devolve megalópole chinesa. *Regressão do critério de raio fixo, que falhava assim.*
- **Reykjavik e Papeete** → degradam para anéis largos em vez de devolver lista vazia.
- **Carga do dataset** → mais de 30 mil cidades após o filtro. *Regressão do índice de coluna errado, que devolvia zero em silêncio.*
- **Reverse geocoding** → coordenada urbana acerta abaixo de 5 km; coordenada remota devolve vazio.

### Rede real: um teste de contrato, fora da suíte padrão

Um único teste marcado como `contract` e excluído da execução padrão bate na API real e verifica apenas que os campos usados continuam presentes — nunca valores, que mudam a cada hora. Roda sob demanda.

A justificativa: a Open-Meteo é dependência externa sem versionamento; quando o formato mudar, o erro precisa ser legível. Mas fazer a suíte inteira depender da rede a tornaria intermitente e lenta.

### Frontend: sem testes unitários

O TypeScript, com os tipos espelhando o payload, já cobre a classe de erro que mais importa: referenciar campo inexistente ou de tipo errado. Componentes de apresentação sem lógica própria não rendem testes úteis — o critério deles é fidelidade visual, julgada olhando.

Uma exceção, se a implementação revelar dor: a formatação de datas e horas a partir dos timestamps sem offset é a única lógica que o compilador não protege.

## Out of Scope

- **Modo escuro.** O toggle sol/lua do cabeçalho permanece decorativo. Dobraria o trabalho de estilo dos nove painéis, e o design de referência só apresenta o tema claro.
- **Alertas meteorológicos oficiais.** Exigiriam um segundo provedor com chave de API (NWS/NOAA, Meteoalarm, Weatherbit), contra a restrição de não usar chave.
- **Calor e frio extremos** entre as condições derivadas. Precisam de normais climatológicas ou percentil histórico.
- **Responsividade abaixo de ~1100 px.** O design é desktop, e cada uma das três faixas precisaria de decisão própria de empilhamento.
- **Persistência.** Última cidade buscada, favoritos, histórico. O design mostra uma busca única.
- **Atualização automática** enquanto a página está aberta.
- **Testes ponta a ponta, de carga e de regressão visual.** Uma página com dois endpoints não os justifica.
- **Deploy, Docker e CI.** Nada nas decisões acima impede contêinerizar depois.
- **Navegação.** A barra lateral tem sete ícones no design, mas existe uma página só; permanecem decorativos.

## Further Notes

**Cota da API externa**: 600 requisições por minuto, 10.000 por dia, sem chave. Requisições com mais de 10 variáveis ou período acima de duas semanas contam fracionadas. O uso previsto (duas chamadas por consulta, com cache de 10 minutos) fica ordens de grandeza abaixo.

**Licenciamento**: Open-Meteo e GeoNames exigem atribuição CC-BY 4.0. Daí o rodapé, e o campo `attribution` no payload em vez de texto fixo no frontend.

**`git init` faz parte do trabalho** — o diretório ainda não é um repositório, o que impede revisão de código por diff. O `.gitignore` precisa cobrir `__pycache__/`, `.venv/`, `node_modules/`, `dist/` e `.env`.

**Glossário**: o repositório ainda não tem `CONTEXT.md` nem ADRs. Termos que a implementação vai firmar e que merecem registro assim que estabilizarem: *cidade candidata* (resultado de geocodificação ainda não escolhido), *condição prevista* (o aviso derivado, distinto de *alerta*, que é oficial e não existe aqui), *cidade vizinha* (selecionada por anéis, com distância obrigatória).

**Protótipo visual** com os nove painéis e dados reais: https://claude.ai/code/artifact/3d192376-1674-4398-b95d-86459a4713fc — útil para conferir os tokens, sem ser código a aproveitar. Amostras de dados reais estão em `probe-alertas.json` (seis cidades, para fixtures de alertas) e `payload-exemplo.json` (payload completo de Berlim).
