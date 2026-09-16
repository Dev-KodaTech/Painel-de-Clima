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

**Status:** resolved

- [x] Existe tela de cadastro e tela de entrada, alcançáveis de qualquer página
- [x] Dá para ir de uma para a outra
- [x] Cadastrar pela tela entra direto, sem pedir a senha de novo
- [x] Quem está entrado vê que está, e com qual conta
- [x] Dá para sair, e sair volta ao estado de visitante
- [x] O envio em curso é visível, e o botão não dispara duas vezes
- [x] Erro de credenciais mostra mensagem clara, sem revelar se o e-mail existe
- [x] Erro de rede é distinguível de erro de credenciais
- [x] Os requisitos de senha aparecem antes do envio, não só no erro
- [x] O estado da conta é consultado uma vez, na rota de layout, e distribuído às páginas
- [x] O cliente de API envia credenciais; nenhum componente toca em cookie
- [x] As telas seguem os tokens e primitivas existentes, sem biblioteca de formulário nova
- [x] As telas respeitam o tema escuro
- [x] As telas são navegáveis por teclado
- [x] As demais páginas continuam funcionando sem conta
