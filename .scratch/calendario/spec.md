# Página Calendário: dezesseis dias, aptidão e planos

Status: ready-for-agent

Origem: sessão de grilling + domain-modeling. Decisões registradas em
[ADR 0010](../../docs/adr/0010-dezesseis-dias-e-a-fronteira-do-dia-oito.md) e
[ADR 0011](../../docs/adr/0011-aptidao-e-absoluta-pelo-motivo-oposto.md).

## Problem Statement

A barra lateral oferece "Sete dias" em `/semana` e a página não existe — o
`PaginaVazia` renderiza a promessa: *"A previsao dos sete dias expandida, com
mais que icone, maxima e minima. Ainda nao construida."*

A promessa é pequena demais para valer uma página. A Visão geral **já mostra os
sete dias** em `PrevisaoSemana.tsx`, com ícone, máxima e mínima. Uma página
inteira para os mesmos sete dias com duas variáveis a mais repetiria o erro que o
[ADR 0006](../../docs/adr/0006-vizinhas-e-comparacao-nao-lista-longa.md) já
corrigiu uma vez: uma página que existe para destravar um limite que não existe.

E há um erro de nome por baixo. O ícone da barra é um calendário, a URL é
`/semana` e o título é "Sete dias" — três nomes para a mesma entrada, e nenhum
deles é o que a página vai ser.

O que falta não é a semana expandida. É **o tempo que ainda não chegou**, longe o
bastante para se planejar em cima dele, e uma resposta à pergunta que a previsão
sozinha não responde: *este dia serve para o que eu preciso fazer?*

## Solution

**A página Calendário**, em `/calendario`, com três camadas:

**Dezesseis dias numa grade**, com uma fronteira visível no dia 8. Do dia 1 ao 7
— o *horizonte curto* — cada dia traz ícone, máxima, mínima e aptidão. Do 8 ao
16 — o *horizonte longo* — a fonte já é outro modelo, e a célula mostra menos:
sem ícone de céu, com probabilidade de chuva no lugar do número seco. Trinta dias
não existem honestamente, e o ADR 0010 mede por quê.

**Aptidão por atividade**, no horizonte curto. Um seletor no topo escolhe a
atividade — lavar roupa, esporte, viagem, plantio — e a grade inteira se pinta
para ela, respondendo "qual dia serve para isto?" numa olhada, em vez de exigir
sete cliques. As regras são limiares absolutos, e o ADR 0011 registra por que a
razão não é a mesma do `condicoes.py`.

**Planos**, para quem tem conta. Um plano é título, dia e atividade — sem hora,
porque a aptidão é diária. A faixa lateral lista os planos e, ao lado de cada um,
a aptidão daquele dia para aquela atividade: o plano diz o que você quer fazer, a
previsão diz se o tempo colabora.

### O que esta página deliberadamente não é

O pedido original descrevia reuniões com link de videochamada e convidados por
e-mail, tarefas com prioridade, e lembretes com aviso automático. Nada disso
entra, e a razão é uma só: **é um segundo produto**, não uma feature de clima.

- **Reunião com convidados** exigiria envio de e-mail. O app não envia e-mail
  nenhum — nem para recuperação de senha, que o
  [ADR 0004](../../docs/adr/0004-locais-salvos-exigem-conta.md) cortou do escopo
  pelo mesmo motivo. Uma lista de convidados que ninguém recebe é um campo que
  mente.
- **Avisos automáticos baseados no clima** ("me avise se quinta virar chuva")
  exigiriam um worker agendado verificando previsões — infraestrutura que não
  existe, o backend só responde requisição — e, sem push nem e-mail, só
  notificariam com o app aberto. Um lembrete que avisa quem já está olhando.
- **Reunião, tarefa e lembrete são três nomes para "coisa num dia"**, que se
  distinguem por campos que o clima não lê: link, prioridade, hora do alerta.
  Um conceito — *plano* — cobre o que a página sabe fazer com o tempo.

Se um dia o app ganhar envio de e-mail e um agendador, esta seção é o que precisa
ser reaberto.

## User Stories

### A grade e os dezesseis dias

1. Como visitante, quero abrir a página Calendário pela barra lateral, para ver o tempo dos próximos dias da cidade escolhida.
2. Como visitante, quero ver dezesseis dias, para planejar além da semana que a Visão geral já mostra.
3. Como visitante, quero ver os dias numa grade de calendário, para reconhecer as semanas e achar "a próxima quinta" sem contar.
4. Como visitante, quero ver ícone, máxima e mínima nos sete primeiros dias, para ter no Calendário o que já tenho na Visão geral.
5. Como visitante, quero perceber que os dias distantes são menos confiáveis, para não tratar o dia 14 como o dia 2.
6. Como visitante, quero ver a probabilidade de chuva nos dias distantes, para ter alguma informação onde o ícone não cabe.
7. Como visitante, quero entender por que os dias mudam de aparência no meio da grade, para não achar que é falha de carregamento.
8. Como visitante, quero que o dia de hoje seja distinguível, para me situar na grade.

### Aptidão

9. Como visitante, quero escolher uma atividade no topo da página, para saber quais dias servem para ela.
10. Como visitante, quero ver a grade inteira pintada pela aptidão da atividade escolhida, para achar o dia bom numa olhada.
11. Como visitante, quero ver a aptidão como texto além da cor, para entendê-la sem depender de enxergar cor.
12. Como visitante, quero saber **por que** um dia é ruim para a atividade, para julgar se o motivo me importa.
13. Como visitante, quero que a aptidão apareça só nos sete primeiros dias, para não receber conselho sobre dado que não sustenta conselho.
14. Como visitante, quero entender por que os dias distantes não têm aptidão, para não achar que faltou carregar.
15. Como visitante numa semana ruim, quero ver que nenhum dia serve, para decidir adiar — e não achar que a página quebrou.
16. Como visitante, quero ver que a aptidão é derivada da previsão e nossa, para não confundir com recomendação de autoridade.

### Planos

17. Como visitante com conta, quero criar um plano num dia, para registrar o que pretendo fazer.
18. Como visitante com conta, quero dar um título ao plano, para distinguir "lavar as cortinas" de "lavar o tapete".
19. Como visitante com conta, quero escolher a atividade do plano, para que o tempo seja julgado pelo critério certo.
20. Como visitante com conta, quero ver meus planos numa faixa ao lado da grade, para ler todos sem clicar dia a dia.
21. Como visitante com conta, quero ver a aptidão do dia ao lado de cada plano, para saber se o tempo colabora.
22. Como visitante com conta, quero apagar um plano, para tirar da lista o que já fiz ou desisti.
23. Como visitante com conta, quero ver os dias que têm plano marcados na grade, para achar meus compromissos no mês.
24. Como visitante sem conta, quero ver a previsão e a aptidão normalmente, para que a página sirva sem eu me cadastrar.
25. Como visitante sem conta, quero um convite para entrar no lugar da faixa de planos, para saber o que ganho ao criar conta.
26. Como visitante com conta e sem planos, quero uma mensagem que me diga como criar o primeiro, para não ver uma faixa vazia.
27. Como visitante com conta, quero que meus planos sigam comigo em outro navegador, para não perdê-los ao trocar de máquina.
28. Como visitante com conta, quero que um plano de um dia que já passou não suma sem aviso, para saber o que planejei.

### Transversais

29. Como visitante sem cidade escolhida, quero uma instrução para buscar uma, em vez de uma página vazia ou quebrada.
30. Como visitante, quero ver o estado de carregamento, para saber que algo está acontecendo.
31. Como visitante, quero que a falha da previsão seja declarada, para não confundir com ausência de dado.
32. Como visitante, quero ver o crédito das fontes da página, para saber de onde vem o que estou lendo.
33. Como visitante no tema escuro, quero que a página acompanhe o tema, inclusive as cores de aptidão.
34. Como visitante de teclado, quero navegar a grade e criar um plano sem mouse.
35. Como visitante com leitor de tela, quero que cada dia seja anunciado com data, previsão e aptidão, e não como uma célula muda.
36. Como visitante, quero que trocar de cidade recarregue a grade, para não ler a previsão da cidade anterior.

## Implementation Decisions

**Dezesseis dias, não trinta.** ADR 0010. `forecast_days` teto em 16; o ensemble
de 35 dias não tem `weather_code` e cai para ~50 km, e o σ de 4,5 °C no dia 30
torna o número único desonesto.

**A fronteira do dia 8 é troca de modelo, não estética.** ICON até o 7, ECMWF do
8 ao 15, com 4,7 °C de desacordo medido na costura. Uma curva contínua exibiria
um degrau que não é meteorologia.

**A previsão longa é buscada na página.** Endpoint novo, buscado no componente,
pela regra do [ADR 0003](../../docs/adr/0003-historico-e-buscado-na-pagina.md):
só uma página lê os dias 8–16, então vai nela. A chamada de 7 dias do painel
**não muda** — cinco páginas dependem dela e não leem o dia 12.

**A aptidão mora no backend.** Módulo próprio ao lado de `condicoes.py`, com os
limiares como constantes documentadas, seguindo o mesmo formato. Regra de domínio
testável, não lógica dentro de componente.

**A aptidão para no dia 7.** Skill de precipitação colapsa antes da de
temperatura, e a decisão que ela informa é de 1 a 5 dias. ADR 0010.

**A aptidão é absoluta, e não pelo motivo do vizinho.** ADR 0011. Os dois
arquivos vão parecer concordar por engano; cada um aponta para o registro.

**Os limiares precisam de amostra com trópico úmido.** A calibração do
`condicoes.py` usou 42 dias-cidade montados para outro fim. Uma aptidão calibrada
só em cidade temperada reproduz o bug que o ADR 0011 diz evitar.

**Plano exige conta.** Regra do ADR 0004: função de quem está olhando vai no
banco. `localStorage` deslogado com migração ao entrar foi rejeitado lá, pelos
casos de conflito, e a rejeição continua valendo.

**A página é mista, e é a primeira.** Previsão e aptidão são função da cidade e
viajam na URL; só a faixa de planos é da conta. Nenhuma página do app fez isso
ainda — Locais salvos, que seria a primeira por conta, é inteira da conta.

**Plano não guarda clima.** Mesma regra do `LocalSalvo`: clima guardado
envelhece. Guarda título, dia e atividade; a previsão é buscada fresca e cruzada
na leitura.

**Plano não tem hora.** A aptidão é diária e o horizonte longo não tem dado
horário. Um campo de hora prometeria precisão inexistente.

**O guard de sessão sai numa fatia própria.** `conta_da_sessao()` hoje é função
de módulo chamada de um lugar só. Três rotas autenticadas a mais é onde um
`Depends` ganha o seu lugar — e a fatia 01 o entrega para esta feature **e** para
a issue 05 de `locais-salvos`, que precisa do mesmo.

**A grade é escrita à mão.** Nem FullCalendar (~200 KB, CSS próprio brigando com
os tokens, feito para agenda arrastável) nem shadcn/ui Calendar (traz Radix, CVA,
`tailwind-merge` e um `components.json` que o repo não tem — e é um *date
picker*, não uma grade com conteúdo por célula). O componente central é "célula
de dia que mostra clima e julgamento", que é código nosso em qualquer cenário.

**Sem biblioteca de data.** `Intl` e o truque de `Date.UTC` que `formato.ts` já
usa em `indiceDoDia` bastam. Atenção: esta é a primeira página do app que faz
**aritmética** de data — limites de mês, offset do dia da semana —, e a regra do
`formato.ts` (timestamps do painel são hora de parede da cidade, fatiados como
string, nunca parseados) continua valendo para a previsão.

**A frase da barra lateral muda junto.** Regra do ADR 0006. `titulo`, `caminho`
e `oQueVem` mudam na mesma fatia — a barra não pode prometer "Sete dias" numa
página de dezesseis.

## Riscos registrados

- **Os números do ADR 0010 são sondagem de setembro de 2026** — o seam de
  4,7 °C, o σ de 4,5 °C e o mapeamento ICON/ECMWF/GFS. A Open-Meteo pode trocar
  o encadeamento de modelos sem avisar, e a fronteira do dia 8 deixaria de casar
  com a troca real. Um teste de contrato marcado é o que avisa.
- **`weather_code` no horizonte longo não foi verificado dia a dia.** O endpoint
  padrão o devolve até o dia 16; o que não se mediu é o quanto ele oscila entre
  execuções. A decisão de não exibir ícone lá protege disso, mas se um dia se
  quiser exibir, isso precisa ser medido antes.
- **Os limiares de aptidão ainda não existem.** Diferente do `condicoes.py`, que
  chegou com calibração medida, aqui a calibração é trabalho da fatia 05 — e sem
  ela os números serão chutes com aparência de medida.
- **Plano de dia passado não tem política definida.** A story 28 diz que não pode
  sumir sem aviso; o que exatamente acontece (fica, esmaece, vai para um fim de
  lista) é decisão da fatia 08.
- **Primeira página com escrita autenticada.** Todo o CRUD anterior do app é
  leitura pública ou conta/sessão. Erros de sessão expirada no meio de um
  formulário são caminho novo.
