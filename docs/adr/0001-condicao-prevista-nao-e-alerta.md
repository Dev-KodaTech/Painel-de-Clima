# Condição prevista não é alerta, mas o campo do payload se chama `alerts`

> **Superseded pelo [ADR 0007](0007-alerta-oficial-e-condicao-prevista-coexistem.md).**
> A condição de revogação prevista na última seção deste registro se realizou: o
> app passou a exibir alertas do INMET, e o campo foi renomeado. O que este
> registro estabeleceu sobre o rótulo de proveniência por card continua valendo.

A fonte externa não tem alertas meteorológicos, então os avisos de tempo severo
são derivados por nós da própria previsão. A distinção importa porque alerta é a
categoria de informação em que pessoas tomam decisão de segurança: no domínio e
na interface o termo é **condição prevista**, e o painel deliberadamente não se
chama "alertas". No código, porém, o tipo é `Alerta` e o campo do payload é
`alerts` — decidimos manter assim.

## Consequences

O glossário e o código discordam no nome, e é intencional. Quem ler `alerts` no
payload pode supor que são alertas oficiais; não são, e nada no dado diz isso.

O que de fato protege o usuário não é o nome do campo, e sim o rótulo "derivado
da previsão" que a interface põe em **cada card** — essa parte é obrigatória e
não pode ser removida por conveniência de layout. Renomear o campo alinharia o
vocabulário, mas quebraria o contrato da API por um ganho que o usuário não vê.

Se um dia o painel passar a exibir alertas de fonte oficial, os dois conceitos
vão coexistir e o nome `alerts` deixa de ser aceitável: aí a renomeação vira
pré-requisito, não preferência.
