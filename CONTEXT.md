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
forte ou chuva intensa. Nunca é chamada de alerta: alerta é a categoria de
informação em que pessoas tomam decisão de segurança, e esta não vem de fonte
oficial.
_Avoid_: alerta, aviso oficial, warning

**API externa**:
O serviço público de onde vêm os dados de clima e geocodificação. Só o backend
fala com ela; o frontend nunca.
_Avoid_: provedor, upstream, fonte

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
Uma das seis visões alcançáveis pela barra lateral: Visão geral, Tendência,
Cidades vizinhas, Condições previstas, Sete dias e Ajustes. Uma página ocupa a
área de conteúdo inteira e tem URL própria.

Distinta de painel: um painel mora *dentro* de uma página, e a mesma informação
pode aparecer resumida num painel da Visão geral e por inteiro na sua página.
_Avoid_: aba, tela, rota, seção

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
