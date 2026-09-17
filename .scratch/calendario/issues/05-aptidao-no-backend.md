# 05: Aptidão no backend

Status: done

**What to build:** as regras que julgam, para cada dia do horizonte curto, o
quanto ele serve para cada uma das quatro atividades.

Decisões em
[ADR 0011](../../../docs/adr/0011-aptidao-e-absoluta-pelo-motivo-oposto.md). O
verbete *Aptidão* está no `CONTEXT.md`.

**Blocked by:** 03

## Antes de escrever a regra

- [x] Ler `backend/app/services/condicoes.py` inteiro. É o módulo-modelo: limiares
      como constantes no topo, cada uma com o comentário da calibração que a
      produziu, e a estrutura de categoria como dataclass
- [x] Ler o ADR 0011 antes de copiar o raciocínio dele. **As duas decisões
      coincidem no resultado e divergem no motivo**, e o módulo precisa dizer isso
      na docstring, apontando para o registro. Sem isso, a próxima pessoa aplica o
      argumento de um no outro

## As variáveis

- [x] Verificar o que a chamada de 16 dias já traz e o que falta. `weather_code`,
      `temperature_2m_max/min`, `precipitation_sum`, `wind_gusts_10m_max` e
      `precipitation_probability_max` já vêm da fatia 03
- [x] Umidade **não** vem da previsão hoje — `relative_humidity_2m_mean` só é
      pedida ao `archive-api` em `historico.py`. Lavar roupa depende dela.
      Decidir: pedir a variável diária na chamada de 16 dias, ou julgar roupa sem
      umidade. Registrar a escolha
      — **Decidido: pedir a variável.** Verificado contra o serviço real antes de
      decidir: o endpoint de previsão serve `relative_humidity_2m_mean` como
      variável **diária** nos dezesseis dias, sem nulos. Julgar roupa sem
      umidade era a alternativa, e ela esvazia a regra — sobraria só a chuva, e
      um dia de 95% de umidade sem chuva nenhuma passaria como ótimo para
      estender no varal, que é exatamente o caso que separa aptidão de condição
      prevista. Custo: uma variável a mais numa chamada que já existe, zero
      requisições novas. Registrado em `open_meteo.py` (constante
      `VARIAVEIS_DO_HORIZONTE`) e protegido pelo teste de contrato, que agora
      exige a umidade preenchida no horizonte curto inteiro
- [x] Toda variável nova entra na chamada da fatia 03, **não** na
      `buscar_previsao()` de 7 dias

## As quatro atividades

- [x] Lavar roupa, esporte ao ar livre, viagem, plantio
- [x] Cada uma é uma regra explícita sobre variáveis nomeadas — não um score
      genérico com pesos. Uma atividade sem regra própria seria um rótulo que não
      julga nada (verbete *Atividade*)
- [x] Cada julgamento carrega **o motivo**: qual variável reprovou e com que
      valor. A story 12 depende disso, e é o que separa conselho de palpite
- [x] Níveis de aptidão poucos e nomeáveis em texto — não um número de 0 a 100,
      que sugere precisão que a regra não tem

## Calibração — o trabalho de verdade desta fatia

- [x] Amostra de dias-cidade que **inclua trópico úmido**. A amostra de 42 do
      `condicoes.py` foi montada para outro fim e é temperada demais. Manaus é o
      caso que quebra limiar ingênuo de umidade
- [x] Medir quantos dias cada limiar marca, como `condicoes.py` fez ("≥40 marca
      26% dos dias, ≥80 perde eventos reais"). Números medidos, não escolhidos
- [x] Cada constante leva no comentário a medida que a justificou
- [x] Aceitar explicitamente que cidade úmida tem menos dia bom de secar roupa —
      é o fato, não o bug (ADR 0011)

## Endpoint

- [x] Servir junto com a previsão de 16 dias ou em rota própria — decidir e
      registrar. A previsão já está no cache de 10 minutos, então o custo é o
      mesmo; o critério é se alguém quer uma sem a outra
      — **Decidido: junto, como campo `aptidoes` de cada `DiaDoHorizonte`.**
      Pelo critério que a própria issue dá: ninguém quer uma sem a outra. A
      grade pinta a célula do dia pela aptidão daquele dia — são a mesma célula,
      e uma rota própria faria a página cruzar duas respostas por data para
      redesenhar o que já vinha junto. A aptidão é uma propriedade do dia, como
      o ícone: mora onde o dia mora
- [x] Aptidão só nos sete primeiros dias. Os dias 8–16 **não** trazem o campo —
      ausência, não um valor "desconhecido" que a interface teria de filtrar
- [x] Nunca persistida: recalculada a cada leitura

## Testes

- [x] Cada atividade tem caso que aprova e caso que reprova, com o motivo correto
- [x] Um dia sem condição prevista nenhuma pode ter aptidão péssima — o teste que
      prova que os dois conceitos são independentes
- [x] Um dia com condição prevista de tempestade reprova nas atividades ao ar livre
- [x] Os dias 8 a 16 não trazem aptidão
- [x] Cidade tropical úmida não reprova em **todos** os dias do ano para lavar
      roupa — o teste que guarda o modo de falha do ADR 0011
- [x] Os limiares são absolutos: a mesma entrada meteorológica produz a mesma
      aptidão em duas cidades diferentes

## Comments

### A calibração, que era o trabalho de verdade desta fatia

**3.650 dias-cidade**: um ano inteiro (2025-09-01 a 2026-08-31) do `archive-api`
para dez cidades, cinco delas de trópico úmido — Manaus, Belém, Singapura,
Lagos e Bangkok. A amostra de 42 do `condicoes.py` não foi reaproveitada, pelo
motivo que a issue dá: foi montada para outro fim e é temperada demais.

O número que importa está medido nos dois sentidos, e é o que o ADR 0011 manda
guardar:

| limiar de umidade | Belém | Lagos | Manaus |
|---|---|---|---|
| **≥92% (escolhido)** | 9% dos dias bons | 13% | 21% |
| ≥88% (rejeitado) | **0 dias no ano** | 1 dia no ano | 15% |

Belém zerava. É exatamente a falha que o ADR descreve — "a página diz que nunca
é dia de lavar roupa" —, e ela não aparece em nenhum teste de dia único.

**Wellington é o caso espelhado, e foi aceito como fato.** A mediana de rajada
lá é 73 km/h, acima do limiar de severidade do próprio `condicoes.py`, então a
cidade reprova 76% dos dias para esporte. Não é bug: a cidade é ventosa mesmo, e
"aceitar que cidade úmida tem menos dia bom" vale igual para a ventosa.

### O que a revisão (`/code-review`) mudou

Os dois eixos convergiram no mesmo achado principal, e ele era real:

- **Metade dos comentários de calibração citava a amostra errada.** Diziam
  "12% da amostra de 16 dias" — uma janela de previsão de uma cidade, que não
  sustenta percentual nenhum — enquanto o módulo alegava 3.650 dias-cidade duas
  linhas acima. Todos foram refeitos contra a amostra do ano, e os `*_bom`, que
  não tinham medida nenhuma, ganharam a sua
- **O teste do trópico não guardava o que dizia guardar.** Ele afirmava sobre
  quatro dias secos escolhidos a dedo, e passaria mesmo se Manaus tivesse
  exatamente aqueles quatro dias bons no ano — o próprio bug. Virou uma
  afirmação sobre **taxa**, contra uma amostra determinística de um ano real
  (um dia a cada sete, sem escolha a dedo). Verificado por mutação: apertando o
  limiar para os 88% rejeitados, Belém vai a zero e o teste falha nomeando o
  ADR 0011
- **`condicoes.py` não apontava de volta para o ADR 0011.** O registro exige o
  ponteiro nos **dois** módulos, e só o novo o tinha. Sem isso, quem mexer no
  antigo aplica nele o raciocínio do novo, que é o erro que o ADR existe para
  evitar
- **`CODIGOS_TEMPESTADE` estava duplicado** entre os dois módulos, com um
  comentário que se contradizia (dizia não acoplar e logo admitia que os dois
  precisam concordar). Foi para `wmo.py`, junto de `CODIGOS_NEVE`: quais códigos
  significam trovoada é **fato externo da tabela WMO**, ao contrário dos
  limiares de vento e chuva, que cada módulo calibra para o que julga
- **`_Regra` tinha doze campos opcionais e duas cascatas de `if` que precisavam
  concordar.** Virou uma tupla de `_Faixa`, que carrega o próprio campo, a
  direção da comparação e a frase do motivo — a mesma forma que `_Categoria`
  usa no `condicoes.py`. As duas cascatas viraram um laço cada, e acrescentar
  uma variável passou a ser acrescentar uma entrada
- **`Nivel` (Enum) e `NivelDeAptidao` (Literal)** eram duas definições dos
  mesmos três valores. Ficou só o `Literal` dos modelos, que é a convenção da
  casa. `MotivoDaAptidao.variavel` era `str` livre com a lista fechada escrita
  na descrição; virou `VariavelDaAptidao`

### Pendência que **não** é desta fatia

Duas falhas pré-existentes, nenhuma tocada aqui:

- `test_trends.py::TestUv::test_o_uv_usa_o_dia_da_cidade_e_nao_a_ponta_da_janela`
  — dependente de data, já registrada na fatia 04
- `test_contract.py::test_inmet_ainda_traz_os_campos_usados` — o serviço do
  INMET não respondeu. Falha igual em árvore limpa; é rede, não código
