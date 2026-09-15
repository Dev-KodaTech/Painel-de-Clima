# A página Cidades vizinhas é comparação e mapa, não a lista longa que fora prometida

A navegação prometia, em `frontend/src/navegacao.tsx`, que a página traria "a
lista inteira que o painel da Visao geral trunca". **Essa lista não existe.** O
backend devolve no máximo cinco vizinhas (`QUANTAS = 5` em
`backend/app/services/vizinhas.py`) e o painel da Visão geral mostra as cinco.
Não há truncamento, e a promessa era falsa antes de a página existir.

A página passa a ser outra coisa: as cinco vizinhas **mais a cidade escolhida**
numa tabela ordenável por temperatura ou distância, e um mapa mostrando onde
elas ficam. A pergunta que ela responde é "onde está mais quente agora, aqui
em volta?" — que o painel não responde, porque painel não ordena.

## Por que não apenas aumentar `QUANTAS`

Era o caminho óbvio: subir de 5 para 12 e cumprir a promessa ao pé da letra.
Foi rejeitado porque a seleção não é "as N mais próximas" — é curada. Ela varre
anéis de 100 km a 25.000 km, ordena por população dentro de cada anel, descarta
qualquer candidata a menos de 25 km de uma já escolhida e corta a cauda quando
a distância dá um salto desproporcional. Tudo isso existe para que o resultado
sejam cidades de verdade, e não bairros da mesma metrópole.

A partir da sexta, essa curadoria degrada: o que entra são cidades pequenas
demais ou distantes demais, e a lista fica mais longa piorando. Cinco vizinhas
bem escolhidas comparadas lado a lado valem mais que doze mal escolhidas
empilhadas.

## Consequences

**A frase em `navegacao.tsx` tem de mudar junto com a página**, ou a barra
lateral continua prometendo o que a página não entrega.

**A cidade escolhida aparece dentro da tabela de vizinhas**, e não é uma vizinha
— é a referência de quem todas as distâncias são medidas. A interface precisa
distingui-la visivelmente; uma linha igual às outras faria "distância 0 km"
parecer um dado, quando é uma tautologia.

**O mapa não tem camadas meteorológicas.** A Open-Meteo serve dados por
coordenada e não serve tiles; radar exigiria um segundo fornecedor, com chave e
cota próprias, quando o `CONTEXT.md` descreve "a API externa" no singular. O
mapa usa Leaflet com tiles do OpenStreetMap — sem chave, e o crédito entra na
mesma linha de rodapé que já credita Open-Meteo e GeoNames.

**A página não busca nada.** Lê `nearby` e `units` do painel que o `Shell` já
carregou, obedecendo a regra do [ADR 0003](0003-historico-e-buscado-na-pagina.md):
dado que várias páginas leem, vai no layout. Ordenar é estado local, não viaja
na URL — ao contrário da janela temporal da Tendência, porque a ordem de uma
tabela de cinco linhas não é algo que alguém compartilhe.
