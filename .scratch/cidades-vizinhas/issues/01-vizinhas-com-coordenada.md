# 01: Cidades vizinhas chegam com coordenada

**What to build:** hoje cada cidade vizinha chega ao frontend com o nome, o país,
a distância em quilômetros e o clima — mas sem a coordenada. Nenhuma tela
precisava dela até agora, e o backend a descarta ao montar a resposta, embora a
tenha em mãos: a seleção por anéis trabalha justamente sobre coordenadas.

Este ticket faz a coordenada de cada cidade vizinha sobreviver até o payload.
Nada muda na tela; é o prefactor que torna o mapa possível, feito antes e à parte
para que a entrega do mapa seja só o mapa.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] Cada cidade vizinha no payload de `/api/weather` traz latitude e longitude
- [x] Os valores são os mesmos que a seleção usou para calcular a distância, sem
      arredondamento adicional
- [x] O tipo do frontend acompanha o do backend, como já acompanha nos demais campos
- [x] Os testes HTTP existentes de vizinhas verificam a presença e o valor das coordenadas
- [x] O teste que prova o casamento posicional entre a seleção e as temperaturas
      continua válido: uma troca de ordem tem de continuar aparecendo como erro
- [x] Nenhuma mudança visível na Visão geral
