# Mapa regional vs. busca livre

Type: grilling
Status: resolved

## Question

O painel "Temperature in various regions" mostra um mapa da Austrália com 4 regiões fixas. Isso pressupõe país fixo, contra o requisito de digitar qualquer cidade. Como resolver?

## Answer

**Tabela de cidades próximas.** O backend devolve 4–5 localidades relevantes com suas temperaturas, exibidas na tabela "Locations / Temperature" que já existe no canto inferior direito do print. A ilustração do mapa sai.

Descartadas: fixar na Austrália (painel estático, ignora a busca), mapa SVG dinâmico por país (caro, exige um asset por país).

Mantém o painel coerente com a busca livre; perde-se a ilustração. **O critério de "próxima" ficou em aberto** — o geocoding não tem busca por proximidade. Virou o ticket [Critério de cidades próximas](08-criterio-proximidade.md).
