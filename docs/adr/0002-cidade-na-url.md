# A cidade escolhida mora na URL, não no estado do componente

Com seis páginas, quatro delas lendo o mesmo `WeatherResponse`, era preciso
decidir onde a cidade escolhida vive. Ela vive nos parâmetros de busca da URL
(`?lat=&lon=&name=&cc=&country=&admin1=`), lidos com `useSearchParams` na rota
de layout, que faz a requisição e distribui o resultado às páginas.

O caminho óbvio seria um `useState` no componente de layout. Foi rejeitado por
um motivo específico: com ele, recarregar a página mantém *qual* página está
aberta e perde *qual cidade* — a URL parece carregar o estado e carrega só
metade dele. É pior que não ter rota nenhuma, porque cria uma expectativa que
não se cumpre.

A terceira opção — cada página buscando o seu ao montar — foi rejeitada por
refazer a requisição a cada troca de página. O cache de 10 minutos do backend
absorveria o custo; a requisição continuaria redundante.

## Consequences

A URL fica longa e feia. `/vizinhas?lat=52.52&lon=13.40&name=Berlin&cc=DE&country=Germany&admin1=Land+Berlin`
é o preço de ela ser completa: `/api/weather` exige `country_code`, e `country`
e `admin1` alimentam o `location` exibido. Carregar menos que isso devolve 422
ou um cabeçalho sem procedência.

Em troca, todo link é um link de verdade: compartilhar a barra de endereços
abre a mesma cidade na mesma página, e o botão Voltar do browser desfaz tanto a
troca de página quanto a troca de cidade.

Reverter custa tocar as seis páginas, porque todas leem a cidade da mesma
fonte. É o que torna esta decisão registrável em vez de óbvia.

Uma consequência menos visível: a cidade passa a ser **estado público**. Alguém
que hoje acrescente um campo ao objeto da cidade precisa decidir se ele viaja
na URL — e se viajar, ele fica exposto. Nada do que existe hoje é sensível
(nome, país, coordenada de cidade), mas a pergunta passa a existir.
