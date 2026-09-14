# Weather Alerts sem API de alertas

Type: grilling
Status: resolved
Blocked by: 01

## Question

O print mostra um painel Weather Alerts com dois avisos reais. A Open-Meteo não tem alertas. O que ocupa esse painel?

## Answer

**Derivar pseudo-alertas do próprio forecast.** Regras nossas sobre dados que já temos (rajada acima de um limiar → aviso de vento; `weather_code` 95/96/99 → aviso de tempestade), renderizadas no layout do print.

Descartadas: painel substituto por outra métrica (perde o print), segundo provedor (exige API key), mock com dados fixos (desonesto).

Preserva o layout exatamente, não acrescenta dependência nem key, e os números exibidos são reais. **Os limiares exatos não foram decididos aqui** — viraram névoa e depois o ticket [Regra de derivação dos pseudo-alertas](07-regra-alertas.md), incluindo como rotulá-los para não passarem por avisos oficiais.
