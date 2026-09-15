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
_Avoid_: cidade próxima, região, redondeza

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
