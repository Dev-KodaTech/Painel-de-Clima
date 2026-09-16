# 08: A página Locais salvos

**What to build:** a sétima página, e o lugar onde a lista finalmente se vê
inteira: um cartão por local salvo, com nome, país e o resumo do clima de agora,
de onde dá para abrir a cidade ou removê-la.

Clicar num local abre a **Visão geral** daquela cidade — um local salvo é um
atalho para "abrir esta cidade", e a Visão geral é onde uma cidade se abre.
Reusa a mesma travessia que a busca já faz, e o botão Voltar do navegador
desfaz, coerente com o ADR 0002.

**A lista e o clima são dois carregamentos distintos**, e isso é a decisão que
governa a página: a lista vem do banco, o clima vem da API externa. O cartão
mostra nome e país assim que a lista chega, e o resumo do clima quando ele chega.
Falhar em buscar o clima **não pode apagar a lista** — quem perdeu a conexão com
a API externa ainda precisa poder ver e gerenciar seus locais.

O clima de todos os cartões vem numa requisição só, a do ticket 06.

Esta é a única página cujo conteúdo depende de quem está olhando: a mesma URL
mostra listas diferentes para contas diferentes. Quem não tem conta encontra um
convite para entrar, não uma página vazia.

**Blocked by:** 05, 06 e 07

**Status:** ready-for-agent

- [ ] A página aparece na barra lateral e tem URL própria
- [ ] Um cartão por local salvo, com nome e país
- [ ] Cada cartão mostra a temperatura, o ícone e a descrição do tempo de agora
- [ ] O clima de todos os cartões vem numa requisição só
- [ ] Clicar num cartão abre a Visão geral daquela cidade
- [ ] O botão Voltar do navegador desfaz a abertura
- [ ] Dá para remover um local pelo cartão, e a remoção é imediata e evidente
- [ ] Conta sem locais vê uma mensagem explicando como salvar o primeiro
- [ ] Quem não tem conta vê um convite para entrar, com o que a página faz
- [ ] O carregamento da lista é visível
- [ ] Falha ao carregar a lista mostra mensagem clara
- [ ] Falha ao buscar o clima **não** apaga a lista: os cartões seguem visíveis e removíveis
- [ ] Sessão expirada avisa que é preciso entrar de novo
- [ ] A página respeita o tema escuro
- [ ] Os cartões são navegáveis por teclado, com abrir e remover distinguíveis
- [ ] Reusa o componente de painel, o de ícone e os formatadores existentes
- [ ] As unidades vêm do payload
- [ ] A política de armazenamento escrita no módulo da janela temporal é reescrita para
      registrar que os locais salvos vivem no banco
