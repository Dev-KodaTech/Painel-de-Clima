# Regra de derivação dos pseudo-alertas

Type: prototype
Status: resolved
Blocked by: 02

## Question

Quais limiares exatos disparam um pseudo-alerta, e como o painel os apresenta?

## Answer

Testado contra forecast real de 6 cidades de perfis opostos (Wellington, Reykjavik, Innsbruck, Singapura, Cairo, Miami), numa única chamada multi-coordenada. Dados brutos em `../probe-alertas.json`.

### Regra escolhida: limiar fixo + dedup por categoria

Três categorias, **no máximo um card por categoria**, representando o pior dia:

| Categoria | Gatilho | Card mostra |
|---|---|---|
| Tempestade | `weather_code` ∈ {95, 96, 99} | primeiro dia + "(+N)" se houver mais |
| Vento | `wind_gusts_10m_max` ≥ 60 km/h | pior dia, valor, + "(+N dias)" |
| Chuva | `precipitation_sum` ≥ 20 mm | pior dia, valor, + "(+N)" |

Resultado nas 6 cidades: **0 a 2 cards cada** — cabe no espaço do print sem truncar.

```
Wellington  1 card: vento 86km/h d2 (+4 dias)
Reykjavik   2 cards: vento 86km/h d2 | chuva 27.9mm d2
Innsbruck   1 card: tempestade d2
Singapura   VAZIO
Cairo       VAZIO
Miami       2 cards: chuva 104.4mm d0 | tempestade d5
```

### Duas abordagens testadas e rejeitadas

**Limiar fixo sem dedup** (a recomendação inicial): **Wellington dispara 5 dos 7 dias** com vento ≥ 60. Numa cidade litorânea, vento forte é o clima normal — cinco cards idênticos são ruído, não alerta. O dedup por categoria resolve sem mexer no limiar.

**Limiar relativo ao forecast da cidade** (≥1,5× a mediana da semana + piso absoluto): **falha de forma perigosa.** Em Wellington a mediana de rajada é 76 km/h, então 86 km/h é "normal" e a regra **não emite alerta de vento** numa semana com rajadas de 86. Emite chuva de 14,5 mm no lugar. É o mesmo erro do [ticket 08](08-criterio-proximidade.md) ao pontuar por população/distância: normalizar demais some com o sinal. **Perigo é absoluto, não relativo** — 86 km/h derruba galho em Wellington igual a Cairo.

### Distribuição observada (42 dias-cidade)

| Limiar de vento | % de dias | Veredito |
|---|---|---|
| ≥40 km/h | 26% | ruidoso demais |
| ≥50 km/h | 21% | ruidoso |
| **≥60 km/h** | **14%** | **escolhido** |
| ≥70 km/h | 14% | idêntico ao 60 nesta amostra |
| ≥80 km/h | 9% | perde eventos reais |

Chuva: ≥10 mm → 14% dos dias; **≥20 mm → 4%**; ≥30 mm → 2%. Tempestade: 4% dos dias, 2 de 6 cidades.

### Decisões de apresentação

- **Severidade**: um nível só. O print mostra dois cards visualmente idênticos; três limiares a calibrar em vez de um, sem ganho.
- **Quantidade e ordem**: máximo 2 no painel, ordenados por data. Com o dedup, passar de 2 é raro (nenhuma das 6 cidades passou).
- **Estado vazio**: **2 de 6 cidades ficaram vazias** — é o caso comum, não a exceção, e o print não o cobre. O painel mantém o tamanho e mostra algo positivo ("Sem condições severas nos próximos 7 dias"). Sumir ou encolher quebra o grid de nove painéis.
- **Rotulagem**: o cabeçalho **não** diz "Weather Alerts". Usar "Condições previstas" ou equivalente, com nota de que são derivadas do forecast. Desvia do print de propósito: alerta meteorológico é categoria em que as pessoas tomam decisão de segurança, e a Open-Meteo não é fonte oficial de aviso. Custa uma linha de texto.

### Fora de escopo

Calor e frio extremos ficam de fora. Precisam de limiar relativo ao clima local (30 °C é notícia em Reykjavik, terça-feira em Cuiabá), e o teste acima mostrou que o relativo ingênuo falha. Exigiria normais climatológicas ou percentil histórico — ticket próprio, se um dia.

### Confirmação lateral

Esta sessão reconfirmou o multi-coordenada do ticket 08 na prática: 6 cidades, 1 requisição, array na ordem de entrada, `location_id` a partir do segundo elemento, `timezone=auto` resolvendo por localização (Pacific/Auckland no primeiro).
