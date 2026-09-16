# Notícias vêm de RSS público, porque nenhuma API de notícias é utilizável

A página Notícias agrega três feeds RSS no backend: Agência Brasil
(meio-ambiente), Observatório do Clima e Revista Pesquisa FAPESP. A decisão
partiu de uma API de notícias e mudou diante dos termos de uso.

## O que foi verificado

Cinco APIs foram avaliadas. **Nenhum dos níveis gratuitos é utilizável neste
app:**

| API | Grátis | Produção? |
| --- | --- | --- |
| NewsAPI.org | 100 req/dia | proibido — dev/localhost apenas |
| GNews.io | 100 req/dia | proibido — "cannot be used for commercial projects" |
| Mediastack | 100 req/**mês** | proibido — "Non-Commercial Use" |
| Currents | 250 req/dia | "not suitable for production" |
| NewsData.io | 200 créditos/dia | permitido, mas sem filtro regional |

A NewsAPI é explícita: o plano Developer *"cannot be used in a staging or
production environment (including internally)"*, e o CORS é liberado só para
localhost. Produção começa em US$ 449/mês.

A NewsData.io é a única que permite uso comercial no grátis, e cai por outro
motivo: o parâmetro `region` é exclusivo de plano corporativo, e `state`/`city`
não existem. O filtro regional — que era o ponto de "impactos do tempo na região
do usuário" — não está disponível. Some-se que a permissão comercial aparece no
blog de marketing deles e não num documento vinculante verificável.

Restavam pagar US$ 449/mês ou construir sobre uma permissão que não se pode ler.

## O que o RSS entrega

Os três feeds respondem, sem chave, sem cota, sem restrição comercial e **sem o
atraso artificial de 12 a 24 horas** que os níveis gratuitos impõem. A Agência
Brasil é EBC, setor público, licença CC.

A troca não é um consolo: em frescor e em condições de uso, o RSS é melhor que
qualquer nível gratuito avaliado. O que se perde é volume e diversidade
editorial — três veículos brasileiros em vez de um agregador global.

## Sem filtro regional

Nenhum feed oferece recorte por estado. Seria possível por keyword-match do nome
do estado no título, e isso foi rejeitado: com dez itens por feed, o filtro
esvazia a lista quase sempre, e faria a mesma matéria aparecer para uma cidade e
sumir para outra por acaso de redação de título. Notícia de clima brasileira é
nacional; simular personalização prometeria uma relevância que o dado não
sustenta.

## Sem astronomia

O pedido original incluía astronomia. Não há fonte viável em português
brasileiro: a NASA "ciencia" é em espanhol, o AstroPT está parado desde abril de
2024, o Space Today responde HTTP 500 com corpo malformado, e o ESO Portugal é
português europeu e de baixo volume. Misturar feeds em inglês numa interface
inteiramente em português foi rejeitado, e traduzir exigiria um fornecedor a mais
— com chave — por conteúdo tangencial.

Dados de céu derivados da coordenada (nascer e pôr do sol, fase da lua) seguem
como possibilidade, e são outra coisa: cálculo, não notícia, e específicos da
cidade.

## Consequences

**O backend passa a fazer parsing de XML de terceiros.** Feeds quebram, mudam de
formato e saem do ar sem aviso. Um feed indisponível não pode derrubar a página:
a agregação ignora o que falhou e mostra o resto.

**A página depende de três veículos com dez itens cada.** É uma página pequena, e
fica menor se um feed parar. Acrescentar veículos é barato, e é a saída se isso
incomodar.

**Cada notícia nomeia o veículo.** A licença pede crédito, e sem ele a pessoa não
consegue julgar o que está lendo — numa lista que mistura agência pública, ONG e
revista científica, quem publicou é parte da informação.

**Notícias não entram na página Condições.** Não são sobre a cidade escolhida,
enquanto o resto do app inteiro é. Juntá-las a alertas e condições faria uma
página nomear duas naturezas — o estrago que o `CONTEXT.md` já documenta em
*painel* e em *tendência*.
