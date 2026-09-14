# 22: Gráfico horário e previsão de sete dias

**What to build:** a pessoa vê como a temperatura varia ao longo do dia num gráfico com a hora atual marcada, a previsão dos próximos sete dias com ícone e máxima/mínima de cada um, e os horários de nascer e pôr do sol — todos no fuso da cidade consultada.

**Blocked by:** 21

**Status:** resolved

Referência: [spec](../spec.md), "Contrato da API" e a armadilha nº 3 de "Armadilhas de formato da API externa".

- [x] Payload ganha os blocos `hourly` (24 pontos), `daily` (7 dias) e `sun`
- [x] `hourly` traz as **24 horas do dia corrente** (00:00–23:00), não uma janela rolante a partir de agora
- [x] Timestamps viajam **sem sufixo de fuso**, como a API os devolve, acompanhados de `timezone` e `utc_offset_seconds`
- [x] O frontend trata os timestamps como horário de parede da cidade, **nunca** via conversão UTC
- [x] Gráfico de tendência com a hora atual marcada e rótulos esparsos no eixo (~7 marcas, não 24)
- [x] Painel de previsão da semana com o dia de hoje destacado
- [x] Painel de nascer/pôr do sol
- [x] Teste na costura HTTP: cidade com offset não-zero preserva os horários sem deslocamento
- [x] Teste: `hourly` tem 24 pontos e `daily` tem 7
