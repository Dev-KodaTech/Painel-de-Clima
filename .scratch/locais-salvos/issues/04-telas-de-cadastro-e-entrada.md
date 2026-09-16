# 04: Telas de cadastro e entrada

**What to build:** a primeira parte visível. Até aqui a conta só existe para
quem sabe fazer requisições à mão.

Duas telas — cadastro e entrada — alcançáveis de qualquer página, com caminho de
uma para a outra, porque quem errou a porta precisa corrigir sem voltar ao
começo. Quem está entrado vê que está, e com qual conta, e tem como sair.

O estado da conta vive na rota de layout, junto do painel, e chega às páginas
pelo mesmo contexto que o painel já usa. É consultado uma vez ao abrir o app.

O cliente de API passa a enviar credenciais, e esse é o único ponto do frontend
que muda por causa da sessão: nenhum componente manipula cookie ou cabeçalho.
O tratamento de erro já existente não precisa mudar — ele já exibe a mensagem
que o backend manda.

As outras páginas continuam funcionando sem conta, exatamente como hoje. O login
não é pedágio para nada que já existe.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Existe tela de cadastro e tela de entrada, alcançáveis de qualquer página
- [ ] Dá para ir de uma para a outra
- [ ] Cadastrar pela tela entra direto, sem pedir a senha de novo
- [ ] Quem está entrado vê que está, e com qual conta
- [ ] Dá para sair, e sair volta ao estado de visitante
- [ ] O envio em curso é visível, e o botão não dispara duas vezes
- [ ] Erro de credenciais mostra mensagem clara, sem revelar se o e-mail existe
- [ ] Erro de rede é distinguível de erro de credenciais
- [ ] Os requisitos de senha aparecem antes do envio, não só no erro
- [ ] O estado da conta é consultado uma vez, na rota de layout, e distribuído às páginas
- [ ] O cliente de API envia credenciais; nenhum componente toca em cookie
- [ ] As telas seguem os tokens e primitivas existentes, sem biblioteca de formulário nova
- [ ] As telas respeitam o tema escuro
- [ ] As telas são navegáveis por teclado
- [ ] As demais páginas continuam funcionando sem conta
