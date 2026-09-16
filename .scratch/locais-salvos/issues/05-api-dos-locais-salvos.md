# 05: Salvar, listar e remover locais salvos

**What to build:** a conta existe e sabe quem é; falta o que ela possui.

Três operações, todas escopadas à sessão: listar os locais salvos da conta,
acrescentar um, remover um. É a única parte do app onde a mesma requisição
devolve coisas diferentes conforme quem pergunta.

**O local salvo guarda os seis parâmetros que descrevem a cidade** — os mesmos
que já viajam na URL — e nada de clima. Clima guardado envelhece, e alguém veria
a temperatura de ontem sem saber que é de ontem. O clima dos cartões é sempre
buscado na hora, e isso é ticket 06.

**Salvar a mesma cidade duas vezes não duplica.** A identidade de um local, para
esse efeito, é a coordenada arredondada mais o código do país — comparar pelo
nome falharia com grafias diferentes da mesma cidade.

Testável inteiro pela costura HTTP, sem nenhuma tela: por isso este ticket não
espera o 04.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Listar devolve os locais salvos da conta da sessão
- [ ] Listar devolve lista vazia para conta sem locais, e isso não é erro
- [ ] Salvar acrescenta o local à conta da sessão
- [ ] Salvar guarda os seis parâmetros da cidade, e nenhum dado de clima
- [ ] Salvar a mesma cidade duas vezes não cria duas entradas
- [ ] Duas cidades homônimas em países diferentes são locais distintos
- [ ] Remover apaga o local da conta da sessão
- [ ] Remover um local de outra conta não funciona, e não revela que ele existe
- [ ] Remover um local inexistente não derruba a requisição
- [ ] Listar, salvar e remover são recusados sem sessão
- [ ] Listar, salvar e remover são recusados com sessão expirada
- [ ] Uma conta nunca vê os locais de outra
- [ ] A ordem da lista é previsível e estável entre requisições
- [ ] Coordenada fora de faixa ou parâmetro faltando é recusado
- [ ] Os testes usam a costura HTTP, com o banco em memória
