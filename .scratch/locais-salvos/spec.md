# Locais salvos, com conta e sessão

Status: ready-for-agent

Origem: sessão de grilling + domain-modeling. Decisões registradas em
[ADR 0004](../../docs/adr/0004-locais-salvos-exigem-conta.md) e
[ADR 0005](../../docs/adr/0005-sessao-em-cookie-nao-jwt.md).

## Problem Statement

Quem acompanha o clima de mais de um lugar — onde mora, onde a família mora,
para onde vai viajar — hoje precisa buscar cada cidade de novo, toda vez. O app
lembra da última cidade carregada e só dela, e essa memória vive no navegador:
troca de máquina e ela some.

Não há como dizer "estes são os lugares que me interessam" e voltar a eles.

## Solution

Uma conta, e uma lista que pertence a ela.

Quem se cadastra com e-mail e senha ganha uma estrela no cabeçalho que salva a
cidade que está vendo, e uma página **Locais salvos** com um cartão por local —
nome, país, e um resumo do clima de agora — de onde dá para abrir a cidade ou
removê-la.

Os locais salvos vivem no banco, ligados à conta, e por isso acompanham a pessoa
entre navegadores e máquinas. Entrar em outro computador mostra a mesma lista.

Quem não tem conta continua usando o app inteiro como sempre: as outras páginas
não mudam, não exigem login e não mostram a estrela.

## User Stories

### Cadastro e entrada

1. Como visitante sem conta, quero me cadastrar com e-mail e senha, para ter uma lista de locais que me acompanha.
2. Como visitante me cadastrando, quero saber os requisitos da senha antes de enviar, para não descobrir por erro.
3. Como visitante me cadastrando com um e-mail já usado, quero uma mensagem clara, para saber que devo entrar em vez de cadastrar.
4. Como visitante me cadastrando, quero ser levado direto para dentro, para não ter de entrar logo após criar a conta.
5. Como pessoa com conta, quero entrar com e-mail e senha, para reencontrar meus locais salvos.
6. Como pessoa entrando com dados errados, quero uma mensagem que não revele se o e-mail existe, para que minha conta não seja descoberta por tentativa.
7. Como pessoa entrando, quero continuar entrada ao voltar depois, para não digitar a senha toda visita.
8. Como pessoa entrada, quero sair, para que a sessão termine de verdade neste navegador.
9. Como pessoa entrada em dois navegadores, quero que sair de um não derrube o outro, para não perder a sessão do trabalho ao sair do celular.
10. Como pessoa entrada, quero ver que estou entrada e com qual conta, para não confundir com estar deslogada.
11. Como visitante, quero alcançar cadastro e entrada de qualquer página, para não caçar o caminho.
12. Como visitante, quero ir de cadastro para entrada e vice-versa, para corrigir o rumo se errei a porta.
13. Como pessoa entrando ou cadastrando, quero ver que o envio está em curso, para não clicar duas vezes.
14. Como pessoa entrando, quero que o erro de rede seja distinto do erro de senha, para saber se tento de novo ou corrijo os dados.

### Salvar e gerenciar

15. Como pessoa entrada vendo uma cidade, quero salvá-la pela estrela do cabeçalho, para guardá-la no momento em que me interessa.
16. Como pessoa entrada, quero que a estrela mostre se a cidade atual já está salva, para não salvar duas vezes.
17. Como pessoa entrada, quero remover um local pela mesma estrela, para desfazer sem ir a outra página.
18. Como pessoa entrada, quero ver a página Locais salvos com um cartão por local, para ver todos de uma vez.
19. Como pessoa entrada, quero ver o clima atual de cada local salvo no cartão, para saber como estão sem abrir um por um.
20. Como pessoa entrada, quero ver o ícone e a descrição do tempo em cada cartão, para comparar as condições num relance.
21. Como pessoa entrada, quero clicar num local salvo e abrir a Visão geral dele, para ver o painel completo daquela cidade.
22. Como pessoa entrada, quero remover um local pelo cartão, para limpar a lista de onde a estou olhando.
23. Como pessoa entrada removendo um local, quero que a remoção seja evidente e imediata, para não duvidar se funcionou.
24. Como pessoa entrada, quero ver o país de cada local salvo, para distinguir cidades homônimas.
25. Como pessoa entrada sem nenhum local, quero uma mensagem explicando como salvar o primeiro, para não ver uma página vazia sem saída.
26. Como pessoa entrada, quero que salvar a mesma cidade duas vezes não crie duas entradas, para a lista não encher de repetições.
27. Como pessoa entrada, quero que meus locais apareçam em ordem previsível, para reencontrá-los onde deixei.
28. Como pessoa entrada em outra máquina, quero ver a mesma lista, para ela valer a pena existir.

### Acesso e estados

29. Como visitante sem conta, quero não ver a estrela, para não ser oferecido algo que não posso usar.
30. Como visitante sem conta abrindo Locais salvos, quero um convite para entrar, para saber o que a página faz e como usá-la.
31. Como pessoa cuja sessão expirou, quero saber disso ao tentar salvar, para entrar de novo em vez de achar que quebrou.
32. Como pessoa entrada, quero ver o carregamento da lista, para saber que está vindo.
33. Como pessoa entrada, quero uma mensagem clara se a lista falhar ao carregar, para saber que o problema não é meu.
34. Como pessoa entrada, quero que a falha em buscar o clima dos cartões não apague a lista, para ainda ver e gerenciar meus locais.
35. Como visitante, quero que as outras páginas funcionem sem conta como sempre funcionaram, para o login não virar pedágio.
36. Como pessoa de teclado, quero alcançar e acionar a estrela e os controles dos cartões, para usar sem mouse.
37. Como pessoa com leitor de tela, quero que a estrela anuncie se salva ou não, para saber o estado sem ver.
38. Como pessoa no tema escuro, quero que as telas de cadastro e entrada sigam o tema, para a experiência ser contínua.

## Implementation Decisions

### Banco e infraestrutura

**PostgreSQL**, em container, subido por um arquivo de composição. **Só o banco
é containerizado** — backend e frontend continuam a rodar como o README manda,
porque o recarregamento automático de ambos é o que torna o desenvolvimento
tolerável e dentro de container ele exige montagem de volumes que quebra com
frequência. Containerizar a aplicação inteira é decisão separada, para deploy.

**Migrações com Alembic**, sobre SQLAlchemy. Três tabelas numa migração inicial.

**Três tabelas e nada mais: contas, sessões e locais salvos.** O cache da API
externa continua em memória — cache que some no restart é cache funcionando, e
movê-lo para o banco trocaria um dicionário por ida à rede. O conjunto de
cidades do GeoNames continua sendo o arquivo lido no boot: é dado que nunca
muda, já coberto por testes de funções puras, e movê-lo para tabelas
geoespaciais traria extensão e migração sem ganho que alguém perceba.

**A configuração do banco vem de variável de ambiente**, como a de CORS já vem.
Um arquivo de exemplo documenta as variáveis; o arquivo real não entra no git.

### Contas e senhas

**E-mail e senha, e mais nada.** Sem recuperação de senha, sem verificação de
e-mail, sem OAuth — cada um é um subsistema e nenhum demonstra o que os três
primeiros já demonstram. Ver ADR 0004.

**Senha guardada como hash com Argon2 ou bcrypt.** Nunca em texto, nunca em log,
nunca em resposta de erro. O e-mail é único e comparado sem diferenciar
maiúsculas.

**A resposta a credenciais inválidas é a mesma** para e-mail inexistente e senha
errada, para que a existência de uma conta não seja descoberta por tentativa.

### Sessão

**Cookie `HttpOnly`, `SameSite=Lax`, `Secure` em produção, com linha na tabela
de sessões.** Sem JWT: um token no armazenamento do navegador é legível por
qualquer script da página, e não há como revogá-lo antes de expirar. Sair apaga
a linha, e é isso que faz o logout ser real. Ver ADR 0005.

**Sessões expiram** e uma sessão expirada é recusada. Linhas vencidas se
acumulam enquanto não houver limpeza periódica; é o custo aceito.

**O CORS muda.** Credenciais exigem origem explícita — curinga deixa de ser
permitido — e os métodos deixam de ser apenas leitura, porque cadastro, entrada
e salvar escrevem, e remover apaga. Em desenvolvimento o proxy do Vite esconde
isso: o problema nasce inteiro no primeiro deploy que separar as origens.

### API

Endpoints novos, todos sob o mesmo prefixo dos existentes:

- **cadastro** — recebe e-mail e senha, cria a conta, abre sessão e devolve o cookie
- **entrada** — valida credenciais, abre sessão, devolve o cookie
- **saída** — apaga a sessão e expira o cookie
- **quem sou** — devolve a conta da sessão, ou o estado de não autenticado
- **listar locais salvos** — os locais da conta da sessão
- **salvar local** — acrescenta um local à conta; salvar um já salvo não duplica
- **remover local** — apaga um local da conta

E um endpoint independente de conta:

- **clima atual de várias coordenadas** — expõe a busca em lote que já existe
  dentro do painel, hoje enterrada e sem endpoint próprio. Recebe uma lista de
  coordenadas e devolve temperatura, código e descrição de cada uma, **numa só
  chamada à API externa**. É o que pinta os cartões: uma requisição para a lista
  inteira, não uma por cartão. O caminho alternativo — chamar o painel completo
  por local salvo — foi rejeitado por trazer previsão de sete dias, condições
  previstas e cidades vizinhas que o cartão descarta.

**O local salvo guarda os seis parâmetros que descrevem a cidade** — os mesmos
que já viajam na URL — e nada de clima. Clima guardado envelhece, e alguém veria
a temperatura de ontem sem saber que é de ontem. O clima dos cartões é sempre
buscado na hora.

**A identidade de um local, para efeito de não duplicar, é a coordenada
arredondada mais o código do país.** Comparar pelo nome falharia com grafias
diferentes da mesma cidade.

### Frontend

**Uma sétima página**, entrando pelo mesmo registro de páginas construídas que a
Tendência usou. A barra lateral ganha o item.

**O estado da conta vive na rota de layout**, junto do painel, e chega às
páginas pelo contexto do outlet — mesma mecânica já estabelecida. É consultado
uma vez ao abrir o app.

**O cliente de API ganha envio de credenciais** e é o único ponto que muda:
nenhum componente manipula cookie, cabeçalho ou token.

**A estrela some quando não há conta.** Salvar deslogado no navegador e migrar
ao entrar foi rejeitado: fundir lista anônima com lista da conta tem conflitos —
a mesma cidade dos dois lados, ordem, duplicatas — que custam mais código que a
funcionalidade. Um botão visível e desabilitado também foi rejeitado, por
oferecer o que não funciona. A regra é: **um local salvo pertence a uma conta.**

**Clicar num local salvo abre a Visão geral daquela cidade**, trocando a cidade
escolhida pelos parâmetros da URL. Reusa a mesma travessia que a busca já faz, e
o botão Voltar do navegador desfaz — coerente com o ADR 0002.

**A lista e o clima são dois carregamentos distintos.** A lista vem do banco, o
clima da API externa; o cartão mostra nome e país assim que a lista chega, e o
resumo do clima quando ele chega. Falhar em buscar o clima não pode apagar a
lista.

**As telas de cadastro e entrada reusam os tokens e primitivas existentes.** Não
há biblioteca de formulário no projeto e esta entrega não introduz uma.

**O armazenamento local do navegador continua com tema e última cidade.** A
política escrita no módulo da janela temporal diz que o armazenamento está
restrito a esses dois; a frase precisa ser reescrita para registrar que os
locais salvos vivem no banco, e não que a restrição foi abandonada.

## Testing Decisions

**Um bom teste aqui exercita a costura HTTP**: dada uma requisição, o que volta —
status, corpo, cookie. Não inspeciona o conteúdo da tabela nem chama função
interna. O prior art é a suíte existente, que testa os endpoints por cliente HTTP
com a rede externa simulada, e que verifica o cache contando requisições em vez
de espiar suas entradas.

**A costura principal é uma só: o cliente HTTP sobre a aplicação.** Todos os
endpoints novos são testados por ela.

**O banco entra por injeção, como o relógio e o cache já entram.** A suíte padrão
roda contra um repositório em memória que implementa a mesma interface do de
verdade, preservando a propriedade mais valiosa da suíte atual: roda em cerca de
um segundo, sem infraestrutura. Testar contra um banco diferente do de produção
foi rejeitado — testaria outra coisa.

**Um conjunto menor de testes marcados roda contra o Postgres real**, sob
demanda, exatamente como o teste de contrato já faz com a API externa: fora da
execução padrão, acionado por marcador. É o que prova que o SQL e as migrações
funcionam de verdade. Sem eles, o repositório em memória esconderia erros de
schema.

**Funções puras testadas diretamente**: o hash e a verificação de senha, e a
leitura do parâmetro de coordenadas do endpoint em lote — incluindo entrada
malformada, lista vazia e coordenada fora de faixa.

**Casos que a suíte precisa cobrir**, porque são onde isto quebra:

- cadastro com e-mail repetido, e com diferença apenas de maiúsculas
- entrada com senha errada e com e-mail inexistente devolvendo a mesma resposta
- cada endpoint protegido recusando quem não tem sessão
- sessão expirada recusada
- sair invalidando a sessão, e não derrubando outra sessão da mesma conta
- salvar o mesmo local duas vezes não duplicando
- remover local de outra conta não funcionando
- listar devolvendo apenas os locais da conta da sessão
- o endpoint em lote fazendo **uma** chamada externa para várias coordenadas
- o endpoint em lote com lista vazia
- senha nunca aparecendo em resposta alguma

**Nenhum teste de frontend**, mantendo a decisão do projeto.

**Verificação manual obrigatória**: cadastrar, salvar de duas máquinas ou dois
navegadores e confirmar que a lista é a mesma; e confirmar que sair de um
navegador não derruba o outro.

## Out of Scope

- **Recuperação e troca de senha** — subsistema próprio, exige envio de e-mail.
- **Verificação de e-mail** — idem.
- **Entrada por provedor externo** — não demonstra nada que e-mail e senha não demonstrem.
- **Perfil, nome, foto, preferências de conta** — a conta existe para dar dono a uma lista.
- **Apagar a conta** — reconhecidamente uma lacuna; ver notas.
- **Migrar locais salvos de visitante para conta** — rejeitado no ADR 0004.
- **Reordenar, apelidar ou agrupar locais salvos.**
- **Containerizar backend e frontend** — só o banco entra; deploy é decisão separada.
- **Limite de quantos locais uma conta pode salvar.**
- **Limitação de tentativas de entrada** — ver notas.
- **Limpeza automática de sessões expiradas** — ver notas.
- **Testes automatizados de frontend** — decisão do projeto.

## Further Notes

**Esta entrega é majoritariamente infraestrutura.** A funcionalidade visível —
salvar cidades e vê-las em cartões — é a menor parte; banco, container,
migrações, hash, sessão, cadastro, entrada e rotas protegidas são a maior. O
ADR 0004 registra por que a proporção é essa de propósito, e vale lê-lo antes de
concluir que alguém exagerou.

**Guardar senhas de outras pessoas é uma responsabilidade que não vai embora.**
É a consequência que não aparece no dia do commit.

**Três lacunas conhecidas, deixadas fora de propósito e registradas para não
serem esquecidas**: não há como apagar a conta; não há limitação de tentativas
de entrada, o que deixa a porta aberta a força bruta; e sessões expiradas se
acumulam sem limpeza. Nenhuma impede a entrega, todas são dívida consciente.

**Duas filosofias de estado passam a conviver** no mesmo app: seis páginas cujo
conteúdo é função da URL e compartilhável por link, e uma cuja mesma URL mostra
listas diferentes conforme quem olha. A regra que separa as duas está no
ADR 0004 e existe para a oitava página não ter de adivinhar.

**Sugestão de ordem**: banco e migrações, depois conta e sessão com os testes da
costura HTTP, depois o endpoint em lote, e só então as telas. A página de
Cidades vizinhas é independente desta entrega inteira e pode sair antes.
