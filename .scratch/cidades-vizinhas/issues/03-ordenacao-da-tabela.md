# 03: A tabela ordena por temperatura e por distância

**What to build:** com a tabela na tela, a pergunta que ela ainda não responde é
"onde está mais quente agora?". Seis linhas em ordem de distância obrigam a
comparar seis números de cabeça.

Este ticket torna a tabela ordenável pelos dois critérios que fazem sentido:
temperatura e distância. Ordenar por temperatura começa pela mais quente, porque
é essa a pergunta que motiva ordenar por temperatura. Ordenar por distância
volta à ordem geográfica, que é a que o backend já entrega.

A cidade escolhida participa da ordenação por temperatura — ela é o termo de
comparação, e saber que ela é a mais fria das seis é exatamente o resultado
interessante. Na ordenação por distância ela fica em primeiro, por ser a origem.

A ordem é estado local da página e não viaja na URL: a ordenação de uma tabela
de seis linhas não é algo que alguém compartilhe, e o que importa no link — a
cidade escolhida — já viaja, conforme o ADR 0002.

**Blocked by:** 02 (a tabela precisa existir para ordenar)

**Status:** ready-for-agent

- [ ] A tabela pode ser ordenada por temperatura e por distância
- [ ] Ordenar por temperatura mostra a mais quente primeiro
- [ ] Ordenar por distância mostra a mais próxima primeiro, com a cidade escolhida à frente
- [ ] O critério ativo é visível
- [ ] A ordenação é função pura e exportada, recebendo a cidade escolhida, as
      vizinhas e o critério, e devolvendo as linhas na ordem de exibição
- [ ] Empate de temperatura tem desempate estável: a mesma entrada produz sempre a mesma ordem
- [ ] Os controles são alcançáveis e acionáveis por teclado
- [ ] Um leitor de tela anuncia por qual critério a tabela está ordenada
- [ ] Trocar a cidade escolhida não deixa a tabela ordenada por um critério invisível
- [ ] A ordem não é persistida e não aparece na URL
