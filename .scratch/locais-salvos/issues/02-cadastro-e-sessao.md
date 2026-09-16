# 02: Cadastro e sessão

**What to build:** a primeira fatia vertical de verdade. Alguém cria uma conta
com e-mail e senha, e o backend passa a saber quem está pedindo.

Cadastrar abre a sessão na hora e devolve o cookie — quem acabou de criar a
conta não deveria ter de entrar em seguida. Um endpoint responde "quem sou",
dizendo a conta da sessão ou que não há nenhuma, e é ele que o frontend vai
consultar depois.

A sessão é um cookie `HttpOnly`, `SameSite=Lax`, `Secure` em produção, com linha
na tabela. Sem token no armazenamento do navegador: seria legível por qualquer
script da página, e não haveria como revogá-lo antes de expirar. Ver ADR 0005.

A senha é guardada como hash com Argon2 ou bcrypt. Nunca em texto, nunca em log,
nunca em resposta — nem de erro.

Aqui também entra a mudança de CORS que a sessão exige: credenciais pedem origem
explícita, curinga deixa de ser aceito, e os métodos deixam de ser apenas
leitura. Em desenvolvimento nada disso aparece, porque o proxy do Vite faz o
browser ver uma origem só; o problema nasceria inteiro no primeiro deploy que
separasse as origens, longe daqui.

Demoável por linha de comando: cadastrar, guardar o cookie, perguntar quem sou.

**Blocked by:** 01

**Status:** resolved

- [x] Cadastrar com e-mail e senha cria a conta e devolve o cookie de sessão
- [x] O endpoint de quem sou identifica a conta quando há sessão válida
- [x] O endpoint de quem sou responde que não há conta quando não há sessão, sem erro
- [x] Cadastrar com e-mail já usado é recusado com mensagem clara
- [x] Dois e-mails que diferem só por maiúsculas são o mesmo e-mail
- [x] A senha é guardada como hash, e o hash nunca é igual entre duas contas de mesma senha
- [x] Nenhuma resposta da API contém a senha ou o hash, nem em erro
- [x] Senha abaixo do mínimo exigido é recusada com mensagem que diz o requisito
- [x] E-mail malformado é recusado
- [x] O cookie é `HttpOnly` e `SameSite=Lax`, e `Secure` fora de desenvolvimento
- [x] Uma sessão expirada é recusada pelo endpoint de quem sou
- [x] O CORS permite credenciais e os métodos de escrita, com origem explícita
- [x] Os testes usam a costura HTTP, com o banco em memória
