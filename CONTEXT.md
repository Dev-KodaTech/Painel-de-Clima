# Painel de Clima

Uma aplicação que mostra, para uma cidade, o tempo agora e a previsão dos
próximos sete dias. O backend busca, combina e traduz os dados da API externa;
o frontend consome apenas o backend próprio.

## Language

### Cidade

**Cidade candidata**:
Um resultado de geocodificação que o usuário ainda não escolheu. A busca é
fuzzy e há homônimas legítimas, então uma candidata carrega estado, país e
população — é o que permite distinguir uma da outra.
_Avoid_: resultado, match, sugestão

**Cidade escolhida**:
A cidade que o usuário selecionou entre as candidatas, e sobre a qual as
páginas são montadas. Distinta da candidata: o que serve para *escolher*
(identificador, população) não diz mais nada depois da escolha.
_Avoid_: cidade selecionada, cidade ativa

**Cidade inicial**:
A cidade com que o app abre quando ninguém escolheu nenhuma. Tem duas origens —
a detectada e a última que o app carregou —, e quem a vê não sabe de qual veio:
para ela é só "já estava preenchido".

Distinta da escolhida porque quem escolheu foi o app, não a pessoa. Apagar essa
diferença é o que faz alguém tratar um palpite como uma decisão do usuário.
_Avoid_: cidade padrão, cidade automática, cidade sugerida

**Cidade detectada**:
A cidade que *nós* resolvemos a partir da coordenada que o navegador fornece.
Uma das duas origens da cidade inicial.

Nunca "detectada pelo navegador": o navegador entrega uma coordenada e nada
mais — não sabe o que é uma cidade. Acima de 50 km da mais próxima não há
cidade detectada nenhuma, e isso é resultado normal, não falha.
_Avoid_: cidade do navegador, geolocalização, minha cidade

**Cidade vizinha**:
Uma cidade próxima à escolhida, apresentada para comparação regional, sempre
acompanhada da distância. A distância não é opcional: numa cidade isolada as
vizinhas são distantes, e omiti-la sugeriria uma vizinhança que não existe.

O que a lista abaixo proíbe é **nomear uma cidade vizinha** com essas palavras —
"as regiões em volta" no lugar de "as cidades vizinhas". *Região* no sentido
geográfico comum continua valendo, e a própria definição acima a usa
("comparação regional"): "territórios e regiões especiais" ou "regiões densas"
não são sinônimos do verbete, são outra coisa.
_Avoid_: cidade próxima, região, redondeza — **como nome da cidade vizinha**

### Condições

**Condição prevista**:
Um aviso de tempo severo que *nós* derivamos da previsão — tempestade, vento
forte ou chuva intensa. Não é alerta, e a diferença é de origem, não de
gravidade: a condição prevista sai de um limiar que nós calibramos sobre os
números da previsão, e ninguém a assinou.

Enquanto o app não tinha fonte oficial, "alerta" era só uma palavra proibida.
Agora é o verbete ao lado, e a proibição fica mais estreita e mais séria: chamar
uma condição prevista de alerta passou a ser confundi-la com *outra coisa que
existe no app*, não mais exagerar sozinha.
_Avoid_: alerta, aviso oficial, warning

**Alerta**:
Um aviso meteorológico emitido por autoridade — no Brasil, o INMET. Traz o que
uma condição prevista não pode ter: severidade oficial, janela de validade
declarada por quem emitiu, e recomendações de segurança.

Existe para uma região, não para uma cidade: o alerta cobre um polígono, e a
cidade escolhida está dentro ou fora dele. Por isso o mesmo alerta aparece em
muitas cidades, e não é "o alerta de Sorocaba".

Só existe no Brasil, e isso não é um detalhe de cobertura que se possa omitir:
não ter alerta e não ser coberto são estados diferentes, e apresentá-los igual
diria a quem está em Wellington que não há aviso quando na verdade não há dado.
_Avoid_: aviso, condição prevista, warning

**Fonte oficial**:
Quem tem autoridade para emitir alerta. O que separa alerta de condição prevista
é isto e só isto — não a gravidade do tempo, não a qualidade do dado.
_Avoid_: fonte confiável, fonte primária

**API externa**:
Cada serviço público de onde vêm os dados. Eram um só — a Open-Meteo — e hoje
são três: a Open-Meteo (clima e geocodificação), o INMET (alertas) e os feeds
dos veículos (notícias). Só o backend fala com elas; o frontend nunca.

O que continua valendo do singular original é a restrição que importava: nenhuma
delas exige chave nem tem cota. Não era "um fornecedor", era "nada de chave" —
e foi preciso acrescentar fornecedor para descobrir qual das duas regras era a
regra.
_Avoid_: provedor, upstream, fonte (sem qualificar)

### Notícias

**Notícia**:
Uma matéria publicada por um veículo, sobre clima ou meio ambiente, trazida de
feed público. Não é dado meteorológico: ninguém a calculou, ela não descreve a
cidade escolhida e nada no app depende dela.

É o único conteúdo que **não** é sobre a cidade escolhida. Todo o resto do app
responde "e aqui?"; a notícia é nacional e continua a mesma em Sorocaba e em
Belém. Foi por isso que ganhou página própria em vez de virar uma terceira seção
da página Condições — não por tamanho, mas porque juntá-la a alertas e condições
faria a página prometer relevância local que a notícia não tem.
_Avoid_: artigo, post, feed (como sinônimo de notícia)

**Veículo**:
Quem publica a notícia — a Agência Brasil, o Observatório do Clima, a Pesquisa
FAPESP. Sempre nomeado junto da notícia: a licença exige crédito, e uma matéria
sem veículo não deixa a pessoa julgar o que está lendo.
_Avoid_: fonte, publisher, portal

### Histórico

**Histórico climatológico**:
A série de dias passados de uma cidade, vinda da reanálise, sempre apresentada
em comparação com o mesmo período do ano anterior. A comparação não é enfeite:
24 °C não diz nada sozinho, e o que responde "está fora do normal?" é o ano
passado ao lado.

Distinto de *previsão*: um é medição do passado, o outro é modelo do futuro.
Misturar os dois numa série só faria a fronteira entre medido e previsto
desaparecer no meio do gráfico.
_Avoid_: histórico, passado, dados antigos

**Janela temporal**:
A *escolha* de quanto passado a página Tendência analisa: 7 dias, 30 dias ou 6
meses. É da pessoa, governa a página inteira e viaja na URL.

Distinta dos *sete dias* da previsão, que são fixos e não se escolhem. Distinta
também do **período** que ela resolve: a janela é "6 meses", o período é "17 mar
— 15 set". Uma é a escolha, o outro é o intervalo de datas que sai dela, e o
payload traz os dois (`janela` dentro de `periodo`).

Não chame a *escolha* de período, range ou filtro — é aí que os dois se
confundem, e foi por isso que "6 meses" e "17 mar — 15 set" chegaram a ser a
mesma palavra.
_Avoid_: range, filtro, "o período" como sinônimo da escolha

### Interface

**Painel**:
Um dos cartões brancos do grid — o cartão do dia, a tendência, a precipitação.
São nove na Visão geral, e todos compartilham a mesma moldura.

A palavra chegou a significar três coisas ao mesmo tempo: o cartão, a resposta
inteira da API e a aplicação toda. Ficou sendo só o cartão. A resposta da API
não tem termo de domínio — é `WeatherResponse` no código e nada mais.
_Avoid_: card, widget, bloco, "o painel completo"

**Página**:
Uma das oito visões alcançáveis pela barra lateral: Visão geral, Tendência,
Cidades vizinhas, Locais salvos, Condições, Sete dias, Notícias e Ajustes. Uma
página ocupa a área de conteúdo inteira e tem URL própria.

Sete delas mostram a mesma coisa para qualquer pessoa que abra a URL. Locais
salvos é a exceção — a mesma URL mostra conteúdo diferente conforme a conta.

Distinta de painel: um painel mora *dentro* de uma página, e a mesma informação
pode aparecer resumida num painel da Visão geral e por inteiro na sua página.
_Avoid_: aba, tela, rota, seção

**Página Condições**:
A página que reúne, para a cidade escolhida, os alertas que a cobrem e as
condições previstas dos próximos sete dias. Duas seções, não uma lista só —
misturá-las apagaria a fronteira entre o que é oficial e o que é nosso.

Chama-se **Condições**, não "Condições previstas": o nome antigo descrevia só
metade do que a página passou a mostrar, e um título que nomeia metade do
conteúdo é pior que um genérico. Ao falar do termo, diga "condição prevista";
ao falar da página, diga "a página Condições" — é o mesmo cuidado que
*tendência* já exige.
_Avoid_: alertas (como nome da página), "condições previstas" (como nome da página)

**Tendência**:
A palavra nomeia **duas coisas**, e o registro existe para que ninguém as
confunda:

- a *página* Tendência, que é a página de análise — histórico climatológico,
  comparação com o ano anterior e as métricas avançadas de uma janela temporal;
- o *painel* de tendência da Visão geral, que é a curva horária de temperatura
  de **um** dia.

Sem este registro, "tendência" repetiria o problema que o glossário desfez com
"painel": um nome para coisas de escalas diferentes. Ao falar de qualquer uma
delas, diga qual — "a página Tendência" ou "o painel de tendência".
_Avoid_: "a tendência" sem qualificar

### Conta

**Conta**:
A identidade que possui locais salvos, criada com e-mail e senha. Existe por uma
razão só: dar dono a uma lista. Nada mais no app depende dela — as sete páginas
funcionam sem nenhuma conta, exceto a lista dos salvos.

Distinta de *pessoa*: duas contas podem ser da mesma pessoa e o app não tem como
saber, nem precisa.
_Avoid_: usuário, perfil, login (como substantivo)

**Sessão**:
A prova de que quem está pedindo é o dono da conta. Vive num cookie `HttpOnly`
e numa linha da tabela; sair apaga a linha, e é isso que faz o logout ser real.

Distinta de conta: a conta permanece, a sessão expira. Uma conta pode ter várias
sessões ao mesmo tempo — é o mesmo dono em dois navegadores.
_Avoid_: token, JWT, login (como substantivo), autenticação

**Local salvo**:
Uma cidade que a pessoa guardou na sua conta, para reabrir depois sem buscar de
novo.

É o único conceito do glossário que **persiste e tem dono**. Todas as outras
cidades são derivadas de algo — a candidata vem da busca, a escolhida vem da
candidata, a vizinha vem da escolhida, a detectada vem da coordenada. O local
salvo não é derivado de nada: é uma decisão que alguém tomou e que sobrevive ao
fechar a aba.

Por isso não se chama "cidade salva". Já há quatro termos começando em *cidade*,
e todos significam "cidade que o app calculou". Chamar esta de cidade a
colocaria na mesma prateleira de coisas que ela justamente não é.

Um local salvo **não tem distância**: distância de quê? A vizinha tem, porque
existe em relação à escolhida. O salvo existe sozinho.
_Avoid_: favorito, cidade salva, bookmark, marcador
