# Painel de Clima

Um painel único que mostra, para uma cidade, o tempo agora e a previsão dos
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
A cidade que o usuário selecionou entre as candidatas, e sobre a qual o painel
é montado. Distinta da candidata: o que serve para *escolher* (identificador,
população) não diz mais nada depois da escolha.
_Avoid_: cidade selecionada, cidade ativa

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
