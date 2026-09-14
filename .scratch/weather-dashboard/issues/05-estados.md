# Estados fora do print

Type: grilling
Status: resolved

## Question

O print mostra só o estado feliz. Quais estados extra entram no destino: loading, cidade não encontrada, erro de API, ambiguidade de cidade, dark mode?

## Answer

**Entram**: loading, cidade não encontrada, erro de API/offline, e **desambiguação por dropdown de candidatas** — o geocoding devolve várias (Springfield MO/IL/MA...) com `admin1`, `admin2` e `population` para distingui-las; escolher a primeira silenciosamente daria a cidade errada. A ausência da chave `results` é o caso de "não encontrada".

**Fora de escopo**: dark mode. O toggle sol/lua do header fica decorativo. Dobraria o trabalho de estilo dos nove painéis e o print só mostra o tema claro.
