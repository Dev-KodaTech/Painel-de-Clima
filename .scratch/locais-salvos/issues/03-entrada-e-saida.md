# 03: Entrada e saída

**What to build:** com o cadastro de pé, falta o ciclo completo: quem já tem
conta precisa poder voltar, e quem entrou precisa poder sair.

Entrar valida as credenciais e abre uma sessão nova. Sair apaga a linha da
sessão e expira o cookie — e é apagar a linha que faz o logout ser real, em vez
de apenas esquecer um papel que continua valendo.

Duas propriedades que este ticket existe para garantir, e que são fáceis de
errar:

**A resposta a credenciais inválidas é a mesma** para e-mail que não existe e
para senha errada. Respostas diferentes deixariam qualquer um descobrir quais
e-mails têm conta, testando um por um.

**Sair de um navegador não derruba o outro.** Uma conta pode ter várias sessões
ao mesmo tempo — é a mesma pessoa no computador e no celular —, e sair do
celular não pode encerrar a sessão do computador.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Entrar com credenciais corretas abre sessão e devolve o cookie
- [ ] Entrar com senha errada é recusado
- [ ] Entrar com e-mail inexistente é recusado com a **mesma** resposta da senha errada
- [ ] Entrar não diferencia maiúsculas no e-mail
- [ ] Sair apaga a sessão e expira o cookie
- [ ] Depois de sair, o endpoint de quem sou responde que não há conta
- [ ] Sair de uma sessão não invalida as outras sessões da mesma conta
- [ ] Sair sem sessão não é erro
- [ ] Entrar duas vezes produz duas sessões independentes
- [ ] Uma sessão expirada é recusada como se não existisse
- [ ] Os testes usam a costura HTTP, com o banco em memória
