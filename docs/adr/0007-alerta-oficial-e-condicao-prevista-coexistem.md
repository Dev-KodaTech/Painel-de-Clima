# Alerta oficial e condição prevista coexistem, e o campo `alerts` é renomeado

Supersede o [ADR 0001](0001-condicao-prevista-nao-e-alerta.md).

O ADR 0001 encerrava com a sua própria condição de revogação:

> Se um dia o painel passar a exibir alertas de fonte oficial, os dois conceitos
> vão coexistir e o nome `alerts` deixa de ser aceitável: aí a renomeação vira
> pré-requisito, não preferência.

O app passa a exibir alertas do INMET. A condição foi acionada, e este registro
faz o que ela manda.

## O que muda

**`alerts` vira `condicoes` no payload de `/api/weather`**, e o tipo `Alerta`
vira `CondicaoPrevista`. O ADR 0001 tinha mantido o nome inglês por um motivo
honesto — renomear quebraria o contrato por um ganho que o usuário não vê. Esse
motivo caducou: o ganho deixou de ser vocabulário e virou desambiguação. Com
alerta de verdade no app, um campo chamado `alerts` que não contém alertas não é
mais uma imprecisão tolerável, é uma armadilha para quem ler o payload.

**Alerta entra no glossário** como termo pleno, ao lado de condição prevista. O
`CONTEXT.md` registra os dois e o que os separa — origem, não gravidade.

## O que não muda

**O rótulo de proveniência por card continua obrigatório.** O ADR 0001 dizia que
o que protege o usuário não é o nome do campo, e sim o "derivado da previsão" em
cada card. Isso continua verdade e continua não-removível por conveniência de
layout. A novidade é que agora ele tem um par: o card de alerta declara a fonte
oficial com a mesma insistência, pelo mesmo motivo — um card lido sozinho, fora
da sua seção, precisa carregar de onde veio.

## Por que duas seções e não uma lista cronológica

Uma lista única ordenada por data foi considerada. É o que "feed" sugere, e
pareceria mais moderna.

Foi rejeitada porque põe o rótulo de proveniência para trabalhar sozinho dentro
de um arranjo que convida à comparação direta: dois cards adjacentes, mesma
largura, mesma tipografia, datas próximas, e a única diferença sendo uma linha
pequena de origem. É exatamente a situação em que a distinção que o ADR 0001
defendeu se apaga.

Duas seções rotuladas fazem a fronteira ser estrutural em vez de tipográfica.
Custa a ordenação cronológica global, e esse custo é aceito.

**Alerta oficial não suprime a condição prevista do mesmo dia.** Também foi
considerado — evitaria dizer "chuva" duas vezes para a mesma quinta-feira. Foi
rejeitado porque os dois não são redundantes: um é um aviso assinado por
autoridade, o outro é o nosso número contra o nosso limiar. E a supressão seria
invisível: quem lesse a página não saberia que havia uma segunda leitura.

## Consequences

A renomeação toca o contrato da API, o painel da Visão geral, os tipos do
frontend e a suíte de testes de alertas. É a quebra de contrato que o ADR 0001
recusou a pagar, paga agora porque a condição que a justificava se realizou.

**O painel da Visão geral passa a poder mostrar alerta oficial**, e alerta tem
precedência sobre condição prevista nos dois slots. Um app que sabe de um aviso
oficial e escolhe não mostrá-lo na página inicial não é defensável — e é o custo
disso que o painel continue limitado a dois cards por altura fixa.

**A distinção fica mais difícil de manter, não mais fácil.** Enquanto "alerta"
era palavra proibida, bastava não escrevê-la. Agora ela é um termo correto para
outra coisa, e o erro mudou de forma: não é mais exagerar, é trocar um pelo
outro. Quem revisar texto de interface precisa saber qual dos dois está olhando.
