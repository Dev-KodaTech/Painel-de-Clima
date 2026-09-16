# 07: A estrela no cabeçalho

**What to build:** o momento em que alguém quer guardar uma cidade é enquanto
está olhando para ela, não depois de navegar até uma página de gerência. Por isso
o gesto de salvar mora no cabeçalho, ao lado da busca, junto da identidade da
cidade escolhida.

Uma estrela salva a cidade que está na tela e a remove pelo mesmo clique,
mostrando a qualquer momento se aquela cidade já está salva. Funciona de qualquer
página, porque o cabeçalho está em todas.

**Quem não tem conta não vê a estrela.** Salvar deslogado no navegador e migrar
ao entrar foi rejeitado: fundir uma lista anônima com a da conta tem conflitos —
a mesma cidade dos dois lados, ordem, duplicatas — que custam mais código que a
funcionalidade inteira. Um botão visível e desabilitado também foi rejeitado, por
oferecer o que não funciona. A regra é: um local salvo pertence a uma conta.

**Blocked by:** 04 e 05

**Status:** ready-for-agent

- [ ] A estrela aparece no cabeçalho para quem tem conta, em todas as páginas
- [ ] A estrela não aparece para quem não tem conta
- [ ] A estrela mostra se a cidade escolhida já está salva
- [ ] Clicar salva a cidade escolhida
- [ ] Clicar de novo remove
- [ ] Trocar de cidade atualiza o estado da estrela
- [ ] Sem cidade escolhida, a estrela não oferece uma ação impossível
- [ ] A ação em curso é visível e não dispara duas vezes
- [ ] Falhar ao salvar mostra mensagem e não deixa a estrela mentindo sobre o estado
- [ ] Sessão expirada ao salvar avisa que é preciso entrar de novo
- [ ] A estrela é alcançável e acionável por teclado
- [ ] Um leitor de tela anuncia se a cidade está salva ou não, e o que o clique faz
