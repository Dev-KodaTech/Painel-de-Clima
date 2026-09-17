# A aptidão usa limiares absolutos, e o motivo é o oposto do que o `condicoes.py` diz

Os limiares de aptidão — quanto um dia serve para lavar roupa, esporte, viagem
ou plantio — são **absolutos**, fixos, iguais em Manaus e em Wellington. É a
mesma escolha que `backend/app/services/condicoes.py` fez para as condições
previstas, e por isso este registro existe: **as razões não são as mesmas**, e
quem ler os dois arquivos vai supor que alguém copiou o padrão do vizinho sem
pensar.

## O que o vizinho diz, e por que o argumento dele não serve aqui

O `condicoes.py` documenta a rejeição do relativo em termos de perigo:

> Perigo é absoluto — 86 km/h derruba galho em Wellington igual a Cairo.

Correto, e intransferível. Perigo é uma propriedade do mundo físico; aptidão é
uma propriedade da relação entre o tempo e uma intenção humana. Não há nada de
absoluto em "bom dia para secar roupa" da forma como há em "vento que derruba
galho".

E o caso que testa isso é real. Manaus tem umidade relativa média em torno de
80% o ano inteiro. Um limiar fixo em "70% ou menos para lavar roupa" faria a
página dizer, para a cidade inteira, **todos os dias do ano**, que não é dia de
lavar roupa. Isso é exatamente o modo de falha que o `condicoes.py` descreve na
direção contrária — o limiar relativo que faz Wellington nunca avisar sobre
vento.

## O relativo foi considerado, e o app até tem com que fazê-lo

A alternativa séria era calibrar por cidade contra a climatologia local: "úmido
*para Manaus*", não "úmido". O app tem a infraestrutura — `services/historico.py`
já busca `relative_humidity_2m_mean` do `archive-api`, e o cache já tem a família
de 24 h para dado do passado, que não muda.

Foi rejeitada por duas razões.

**A primeira é que ela responde a pergunta errada.** A roupa em Manaus seca
mesmo mais devagar. Isso não é um artefato do limiar absoluto a ser corrigido —
é o fato que o limiar absoluto relata corretamente. Um sistema que diz "hoje é
ótimo para secar roupa" num dia de 78% de umidade porque *para Manaus* 78% é
seco está informando sobre estatística climática quando a pessoa perguntou sobre
a roupa dela.

**A segunda é que a interface teria de responder "bom comparado a quê?"**. Uma
aptidão relativa é um percentil disfarçado de conselho, e ou ela explica a
referência em cada célula — e a grade vira um gráfico — ou ela esconde que o
mesmo rótulo significa coisas diferentes em cidades diferentes.

## O que substitui o relativo: tolerância, não referência

O risco real do absoluto não é errar o clima tropical — é ser rígido demais e
marcar tudo como ruim. A resposta é **calibrar os limiares para serem
tolerantes**, aceitando explicitamente que Manaus terá menos dias bons de secar
roupa que Sorocaba, porque isso é verdade.

Concretamente, os limiares precisam ser calibrados sobre uma amostra de
dias-cidade que **inclua trópico úmido**, e não só cidades temperadas — a
amostra de 42 dias-cidade que calibrou o `condicoes.py` foi montada para outro
fim. Uma aptidão calibrada só em Sorocaba e Berlim reproduz o bug que este
registro diz evitar.

## Consequences

**Os dois arquivos vão parecer concordar por engano.** `condicoes.py` e o módulo
de aptidão terão ambos constantes de limiar no topo com um comentário de
calibração, e a semelhança é superficial. Cada um deve apontar para este
registro; sem isso, a próxima pessoa a mexer num deles aplica o raciocínio do
outro.

**A aptidão de uma cidade pode ser sempre ruim para uma atividade, e isso é um
resultado válido** — não um estado de erro a ser suprimido. A interface não pode
tratar "nenhum dia bom para lavar roupa nesta semana" como falha, do mesmo modo
que o `status_dos_alertas` distingue "sem alerta" de "sem resposta".

**Se um dia a aptidão virar relativa, este registro é o que precisa ser
revogado**, e a condição é nomeável: se surgirem reclamações de que a página é
inútil em cidades tropicais *apesar* de limiares tolerantes, a tolerância não
resolveu e a referência climatológica passa a ser a resposta.

**Reverter é barato.** São constantes num módulo, e a página não guarda aptidão
— ela é recalculada a cada leitura, porque plano guardado não carrega clima
(ver `LocalSalvo` e o verbete *Plano* no `CONTEXT.md`). Trocar a regra muda o que
a próxima requisição responde, e nada mais. É por isso que este registro é curto:
ele existe pela confusão que evita, não pelo custo que trava.
