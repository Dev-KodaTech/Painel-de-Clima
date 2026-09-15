# 34: Página Tendência — histórico climatológico e filtro temporal

**What to build:** a primeira fatia visível. `/tendencia` deixa de ser uma página
vazia: a pessoa escolhe entre 7 dias, 30 dias e 6 meses, e vê a temperatura do
período sobreposta à do mesmo período do ano anterior, com os números do resumo
ao lado. Passar o mouse sobre o gráfico mostra os valores dos dois anos naquela
data.

A janela escolhida entra na URL, então "Berlim, últimos 6 meses" é um link.

**Blocked by:** 33

**Status:** done

Origem: [spec da página Tendência](30-pagina-tendencia.md).

## Contexto

A página busca o histórico **sozinha**, e não pela rota de layout. É a exceção
deliberada ao [ADR 0002](../../../docs/adr/0002-cidade-na-url.md), e o motivo é
o inverso do que o ADR usou para rejeitar a terceira opção: o `Shell` buscando o
histórico faria as **seis** páginas pagarem por dado que só uma lê.

A consequência a aceitar: sair da Tendência e voltar refaz a requisição. O cache
do backend absorve.

Entra o **Recharts** como dependência do frontend (~100 KB gzip, contra zero
hoje). Os dois gráficos existentes — `TendenciaTemperatura` e `Precipitacao` —
continuam SVG desenhado à mão, e o projeto passa a ter dois vocabulários de
gráfico. A troca é consciente: a página de análise precisa de tooltip, eixo duplo
e legenda, que seriam trabalho manual considerável.

As métricas de chuva, umidade, vento e UV chegam no ticket 35.

- [ ] A rota `/tendencia` deixa de renderizar a página vazia
- [ ] Filtro de três janelas — 7 dias, 30 dias, 6 meses — governando a página
      inteira, e não cada gráfico separadamente
- [ ] A janela mora na URL, pela mesma razão que a cidade mora: compartilhar a
      barra de endereços abre o mesmo período, e recarregar o mantém
- [ ] Trocar de cidade preserva a janela escolhida, para comparar duas cidades no
      mesmo período sem reconfigurar nada
- [ ] O intervalo de datas é exibido em texto, para que "30 dias" não deixe
      dúvida sobre onde termina
- [ ] Gráfico com as duas séries de temperatura sobrepostas, visualmente
      distinguíveis, com tooltip mostrando os dois anos na mesma data
- [ ] A diferença média entre os dois períodos exibida como número, para dar a
      conclusão sem exigir interpretação do gráfico
- [ ] Ano anterior indisponível é dito em texto, não uma série que some sem
      explicação
- [ ] **Nenhum timestamp passa por `new Date()`.** A regra de `formato.ts` vale
      igual aqui: os timestamps são horário de parede da cidade, e o eixo do
      Recharts recebe texto já formatado por nós, nunca um `Date`
- [ ] Cores por variável CSS, como nos gráficos existentes. Cor literal
      quebraria o tema escuro nesta página e só nela
- [ ] Os gráficos continuam legíveis em tela estreita, dentro da coluna de
      conteúdo que já é `min-w-0` no `Shell`
- [ ] Cada gráfico tem resumo em texto para leitor de tela: uma série de 180
      pontos não se lê ponto a ponto
- [ ] Estados tratados **na página**, sem interferir nos estados do painel que
      vêm do `Shell`: sem cidade escolhida instrui a buscar uma; carregando é
      visível ao trocar de janela; erro do histórico não derruba o resto
- [ ] Tipos do frontend espelhando o payload, para que um campo errado quebre na
      compilação


## Comments

Entregue junto das demais fatias, numa implementação só da spec [30](30-pagina-tendencia.md) — ver os comentários de lá, inclusive os achados da revisão.
