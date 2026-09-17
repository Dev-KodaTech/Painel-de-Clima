"""Julga o quanto cada dia do horizonte curto serve para cada atividade.

*Aptidao* e o quanto um dia serve para uma intencao — lavar roupa, esporte ao
ar livre, viagem, plantio. Derivada da previsao por limiares nossos, como a
condicao prevista, e **existe para todo dia do horizonte curto**, tenha alguem
planejado algo ou nao: e do mundo, nao da pessoa.

## Aptidao nao e condicao prevista, e a diferenca nao e de grau

O `condicoes.py` diz que o tempo e **perigoso**. Este modulo diz que o tempo
**serve ou nao serve** para uma intencao sua. Um dia sem condicao prevista
nenhuma pode ter aptidao pessima: 95% de umidade e sem chuva nao dispara aviso
algum, e a roupa nao seca. Confundi-los faria a pagina Calendario parecer uma
segunda pagina Condicoes, mais permissiva (verbete *Aptidao* do `CONTEXT.md`).

## Os limiares sao absolutos, e o motivo **nao** e o do vizinho

Os dois modulos tem constantes de limiar no topo com um comentario de
calibracao, e a semelhanca e superficial. **Leia o
`docs/adr/0011-aptidao-e-absoluta-pelo-motivo-oposto.md` antes de aplicar aqui
o raciocinio de la.**

O `condicoes.py` rejeita o limiar relativo porque *perigo e absoluto*: 86 km/h
derruba galho em Wellington igual a Cairo. Correto e **intransferivel** — nao
ha nada de absoluto em "bom dia para secar roupa" da forma como ha em "vento
que derruba galho". Aqui o absoluto foi escolhido por outra razao: a aptidao
relativa responde a pergunta errada (a roupa em Manaus seca mesmo mais devagar,
e isso e o fato, nao um artefato a corrigir) e obrigaria a interface a explicar
"bom comparado a que?" em cada celula.

A consequencia que o ADR manda aceitar: **cidade umida tem menos dia bom de
secar roupa, e isso e um resultado valido, nao um estado de erro.** O que nao
se aceita e zero — ver a calibracao abaixo.

## A calibracao, e o que ela mediu

Os limiares foram calibrados sobre **3.650 dias-cidade**: um ano inteiro
(setembro de 2025 a agosto de 2026) do `archive-api` para dez cidades, cinco
delas de tropico umido — Manaus, Belem, Singapura, Lagos e Bangkok. A amostra
de 42 dias-cidade que calibrou o `condicoes.py` **nao serve aqui**: foi montada
para outro fim e e temperada demais, e uma aptidao calibrada so nela reproduz
exatamente o bug que o ADR 0011 diz evitar.

O numero que justifica cada constante esta no comentario dela. O resultado
final, em dias bons por ano para lavar roupa: Cairo 97%, Sorocaba 53%,
Berlim 44%, Manaus 21%, Singapura 17%, Lagos 13%, **Belem 9%**. Belem e o piso,
e 9% sao ~33 dias por ano — poucos, e e o fato. Com um limiar de umidade em 88%
em vez de 92%, Belem caia para **zero dias bons no ano inteiro**, que e o modo
de falha que o `test_aptidao.py` guarda.

## Nunca persistida

Recalculada a cada leitura, como o `LocalSalvo` nao guarda clima: um plano
guardado carrega titulo, dia e atividade, e a previsao e buscada fresca e
cruzada na leitura (verbete *Plano* do `CONTEXT.md`).
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.models import (
    Atividade,
    JulgamentoDeAptidao,
    MotivoDaAptidao,
    NivelDeAptidao,
    VariavelDaAptidao,
)
from app.services.wmo import CODIGOS_NEVE, CODIGOS_TEMPESTADE

#: Os tres niveis, reexportados de `models` por conveniencia de quem importa
#: este modulo. **Nao sao uma segunda definicao**: um `Enum` aqui ao lado do
#: `Literal` de la faria a quarta faixa, no dia em que existisse, ter de ser
#: acrescentada em dois lugares que precisariam concordar.
BOA: NivelDeAptidao = "boa"
MEDIA: NivelDeAptidao = "media"
RUIM: NivelDeAptidao = "ruim"


@dataclass(frozen=True)
class _Faixa:
    """Um limiar de uma atividade sobre **uma** variavel do dia.

    Carrega tudo o que aquela variavel precisa para julgar: de que campo do
    bloco diario ela sai, a partir de que valor reprova, ate que valor o dia
    ainda e bom, e como se escreve o motivo. E o que permite `_reprovacao` e
    `_e_boa` serem um laco cada, em vez de duas cascatas de `if` que repetem o
    mesmo formato sete vezes e precisam concordar entre si.

    E a mesma escolha que `_Categoria` faz no `condicoes.py`: a estrutura
    carrega o comportamento (`reprova`, `dentro_do_bom`, `motivo`), e
    acrescentar uma variavel e acrescentar uma entrada — nao editar quatro
    lugares.

    **A direcao e o que mais varia.** Quase tudo reprova por excesso (chuva,
    vento, umidade, calor), o frio reprova por falta, e a chuva do plantio tem
    as duas pontas: pouca demais ja nao e boa. Dai `acima_reprova` existir em
    vez de se assumir uma direcao so.
    """

    variavel: VariavelDaAptidao
    #: O campo do bloco diario de onde o valor sai.
    campo: str
    #: A partir (ou abaixo) de que valor o dia e reprovado.
    reprova_em: float
    #: Ate (ou a partir de) que valor o dia ainda conta como bom.
    bom_ate: float
    #: Como a frase do motivo e escrita, ja com o valor.
    texto: Callable[[float], str]
    #: `True` quando o excesso reprova (chuva, vento, calor); `False` quando e
    #: a falta que reprova (frio).
    acima_reprova: bool = True
    #: O piso do que conta como dia bom, quando a variavel tem as duas pontas.
    #: So a chuva do plantio o usa: um dia seco nao reprova, mas tambem nao e
    #: bom para quem acabou de semear.
    bom_a_partir_de: float | None = None

    def valor(self, dia: dict) -> float | None:
        """O numero do dia, ou `None` quando nao ha.

        O campo pode faltar — uma resposta parcial da API externa nao traria a
        umidade — e a API devolve `null` na borda da janela. Os dois viram
        `None`, e `None` **nunca reprova**: julgar por um valor que nao chegou
        seria inventar o julgamento.
        """
        valor = dia.get(self.campo)
        return None if valor is None else float(valor)

    def reprova(self, dia: dict) -> bool:
        valor = self.valor(dia)
        if valor is None:
            return False
        if self.acima_reprova:
            return valor >= self.reprova_em
        return valor <= self.reprova_em

    def dentro_do_bom(self, dia: dict) -> bool:
        """Se a variavel nao impede o dia de ser bom.

        O valor ausente **nao** impede: a alternativa seria a borda da janela
        virar cinza por falta de uma variavel, e nao por causa do tempo.
        """
        valor = self.valor(dia)
        if valor is None:
            return True
        if self.acima_reprova and valor > self.bom_ate:
            return False
        if not self.acima_reprova and valor < self.bom_ate:
            return False
        if self.bom_a_partir_de is not None and valor < self.bom_a_partir_de:
            return False
        return True

    def motivo(self, dia: dict) -> MotivoDaAptidao:
        """A frase da reprovacao, com o valor que reprovou.

        So faz sentido depois de `reprova()` devolver `True`, e ali o valor
        nunca e `None` — o ausente nao reprova. O `0.0` e a rede de seguranca
        de quem for chamar isto fora de ordem, e nao um valor que a interface
        possa ver.
        """
        valor = self.valor(dia)
        return MotivoDaAptidao(
            variavel=self.variavel, texto=self.texto(0.0 if valor is None else valor)
        )


@dataclass(frozen=True)
class _Regra:
    """Uma atividade e o que ela pede do tempo.

    **Uma regra explicita sobre variaveis nomeadas, e nao um score generico com
    pesos.** Pesos dariam quatro numeros diferentes a partir das mesmas
    variaveis sem que ninguem soubesse dizer por que — e a story 12 pede
    exatamente o contrario: *qual* variavel reprovou e com *que* valor.

    As faixas vem **em ordem de gravidade percebida**: e ela que decide o que
    um dia de tempestade com 38 °C anuncia primeiro. Listar os dois seria um
    relatorio onde cabe uma frase.
    """

    atividade: Atividade
    rotulo: str
    faixas: tuple[_Faixa, ...]
    #: Os codigos WMO que reprovam sem limiar a comparar. Tempestade em todas;
    #: neve e granizo so na viagem, que e a unica que eles atrapalham em
    #: volume que nao chega a ser chuva forte.
    codigos: tuple[tuple[frozenset[int], VariavelDaAptidao, str], ...] = ()


def _chuva(reprova_em: float, bom_ate: float, bom_a_partir_de: float | None = None):
    return _Faixa(
        variavel="chuva",
        campo="precipitation_sum",
        reprova_em=reprova_em,
        bom_ate=bom_ate,
        bom_a_partir_de=bom_a_partir_de,
        texto=lambda v: f"{v:.1f} mm de chuva previstos".replace(".", ","),
    )


def _vento(reprova_em: float, bom_ate: float):
    return _Faixa(
        variavel="vento",
        campo="wind_gusts_10m_max",
        reprova_em=reprova_em,
        bom_ate=bom_ate,
        texto=lambda v: f"Rajadas de {v:.0f} km/h",
    )


def _umidade(reprova_em: float, bom_ate: float):
    return _Faixa(
        variavel="umidade",
        campo="relative_humidity_2m_mean",
        reprova_em=reprova_em,
        bom_ate=bom_ate,
        texto=lambda v: f"Umidade media de {v:.0f}%",
    )


def _calor(reprova_em: float, bom_ate: float):
    return _Faixa(
        variavel="calor",
        campo="temperature_2m_max",
        reprova_em=reprova_em,
        bom_ate=bom_ate,
        texto=lambda v: f"Maxima de {v:.0f} °C",
    )


def _frio(reprova_em: float, bom_a_partir: float):
    """A unica faixa em que e a **falta** que reprova, dai `acima_reprova`."""
    return _Faixa(
        variavel="frio",
        campo="temperature_2m_min",
        reprova_em=reprova_em,
        bom_ate=bom_a_partir,
        acima_reprova=False,
        texto=lambda v: f"Minima de {v:.0f} °C",
    )


#: Tempestade reprova toda atividade ao ar livre. Nao ha limiar a comparar — o
#: codigo e o gatilho —, e por isso ela e um par de codigos e nao uma `_Faixa`.
_TEMPESTADE = (CODIGOS_TEMPESTADE, "tempestade", "Tempestade com raios prevista")

#: Neve e granizo, so para viagem: fecham estrada em volume que nao chega a ser
#: chuva forte.
_NEVE = (CODIGOS_NEVE, "neve", "Neve ou granizo previstos")


#: As quatro atividades, com os limiares medidos.
#:
#: **Os numeros sao a calibracao sobre os 3.650 dias-cidade** — um ano de dez
#: cidades, cinco delas de tropico umido — e o que cada limiar marca nessa
#: amostra esta no comentario acima dele. Nenhum numero aqui foi escolhido por
#: parecer razoavel.
ATIVIDADES: tuple[_Regra, ...] = (
    # LAVAR ROUPA — chuva e umidade, que sao as duas que decidem se a roupa seca.
    #
    # Umidade: reprovar em >=92% (3,6% dos dias do ano) e chamar de bom ate
    # 78% (49%). O numero rejeitado esta medido ao lado: **>=88% marcaria 12,3%
    # dos dias, e zerava Belem no ano inteiro** — Lagos ficava com 1 dia bom —,
    # que e exatamente o modo de falha do ADR 0011. A mediana de umidade de
    # Manaus no ano e 84%, e o limiar mora acima dela de proposito: 84% nao
    # pode ser reprovacao numa cidade onde 84% e terca-feira.
    #
    # Chuva: >=3 mm reprova — 33% dos dias do ano na amostra — e ate 1,0 mm
    # ainda e bom (52%). Vento nao entra: ele **ajuda** a secar, e e a unica
    # variavel que uma atividade daqui prefere alta.
    _Regra(
        atividade="lavar_roupa",
        rotulo="Lavar roupa",
        faixas=(_chuva(reprova_em=3.0, bom_ate=1.0), _umidade(reprova_em=92.0, bom_ate=78.0)),
        codigos=(_TEMPESTADE,),
    ),
    # ESPORTE AO AR LIVRE — chuva, vento e temperatura sobre quem se esforca.
    #
    # Rajada: reprova em >=60 km/h, **o mesmo limiar de severidade do
    # `condicoes.py`**, e bom ate 40. Nao e coincidencia nem copia: acima dali
    # o vento ja e a condicao severa que a outra pagina anuncia, e seria
    # estranho o app avisar "vento forte" e a aptidao dizer que o dia serve
    # para correr. Wellington reprova 76% dos dias por este limiar — a mediana
    # de rajada la e 73 km/h —, e o ADR 0011 manda aceitar: a cidade e ventosa
    # mesmo.
    #
    # Calor >=35 °C marca 5,6% dos dias do ano e frio <=2 °C marca 3,6%: sao os
    # extremos, e nao "dia quente". Chuva >=5 mm reprova (24%); ate 1,0 mm
    # ainda e bom (52%). Dia bom exige tambem maxima <=32 °C (77%) e minima
    # >=5 °C (94%).
    _Regra(
        atividade="esporte",
        rotulo="Esporte ao ar livre",
        faixas=(
            _chuva(reprova_em=5.0, bom_ate=1.0),
            _vento(reprova_em=60.0, bom_ate=40.0),
            _calor(reprova_em=35.0, bom_ate=32.0),
            _frio(reprova_em=2.0, bom_a_partir=5.0),
        ),
        codigos=(_TEMPESTADE,),
    ),
    # VIAGEM — o que atrapalha deslocamento, que e mais tolerante que o resto.
    #
    # Chuva >=15 mm reprova (7,3% dos dias do ano): dirigir em 5 mm e
    # desconfortavel, nao impeditivo, e o limiar do esporte aqui marcaria 24%
    # dos dias como ruins para viajar — conselho inutil, porque quem viaja
    # viaja na chuva. Bom ate 2,0 mm (61%). Neve e granizo reprovam **por
    # codigo**, sem limiar de volume: 2 mm de neve fecham estrada que 2 mm de
    # chuva nao fecham.
    #
    # Rajada igual a do esporte, pelo mesmo motivo de concordar com a pagina
    # Condicoes; bom ate 45 km/h (81%). Resultado: Cairo 75% de dias bons,
    # Manaus 37%, Wellington 7%.
    _Regra(
        atividade="viagem",
        rotulo="Viagem",
        faixas=(
            _chuva(reprova_em=15.0, bom_ate=2.0),
            _vento(reprova_em=60.0, bom_ate=45.0),
        ),
        codigos=(_TEMPESTADE, _NEVE),
    ),
    # PLANTIO — **a unica em que a chuva fraca ajuda.**
    #
    # E o que torna as quatro regras genuinamente diferentes, e nao o mesmo
    # score com pesos: 5 mm reprovam lavar roupa e sao o melhor caso do
    # plantio. Bom exige entre 0,1 e 12 mm; o dia seco fica medio, nao bom.
    #
    # Geada (<=2 °C, 3,6% dos dias do ano) e calor de >=36 °C (3,7%) reprovam —
    # sao os extremos que matam muda recem-posta. Chuva >=25 mm reprova (2,6%):
    # lava semente. A faixa boa de 0,1 a 12 mm cobre 58% dos dias, e minima
    # >=8 °C 89%. Resultado: Lagos 80% de dias bons, Singapura 78%, Manaus 63%,
    # Cairo 5% — deserto nao e bom de plantar, e a regra diz isso sem que
    # ninguem a ensine sobre deserto.
    _Regra(
        atividade="plantio",
        rotulo="Plantio",
        faixas=(
            # A unica faixa com as duas pontas: chuva demais lava semente, e
            # chuva nenhuma nao ajuda quem acabou de semear.
            _chuva(reprova_em=25.0, bom_ate=12.0, bom_a_partir_de=0.1),
            _vento(reprova_em=60.0, bom_ate=45.0),
            _calor(reprova_em=36.0, bom_ate=33.0),
            _frio(reprova_em=2.0, bom_a_partir=8.0),
        ),
        codigos=(_TEMPESTADE,),
    ),
)


def _reprovacao(dia: dict, regra: _Regra) -> MotivoDaAptidao | None:
    """O primeiro motivo que reprova o dia, ou `None` se nenhum reprova.

    **A ordem importa, e e a da gravidade percebida.** Os codigos vem antes das
    faixas, e as faixas na ordem em que a regra as lista: um dia de tempestade
    com 38 °C reprova por tempestade, que e o que a pessoa precisa ouvir
    primeiro. Listar os dois seria um relatorio onde cabe uma frase.
    """
    codigo = dia.get("weather_code")
    for codigos, variavel, texto in regra.codigos:
        if codigo in codigos:
            return MotivoDaAptidao(variavel=variavel, texto=texto)

    for faixa in regra.faixas:
        if faixa.reprova(dia):
            return faixa.motivo(dia)

    return None


def _e_boa(dia: dict, regra: _Regra) -> bool:
    """Se o dia atende **todas** as faixas da atividade.

    Conjuncao e nao media: um dia de sol com rajada de 55 km/h nao e bom para
    correr, e uma media entre "otimo" e "ruim" o chamaria de mediano pelo
    motivo errado.
    """
    return all(faixa.dentro_do_bom(dia) for faixa in regra.faixas)


def _julgar(dia: dict, regra: _Regra) -> JulgamentoDeAptidao:
    motivo = _reprovacao(dia, regra)
    if motivo is not None:
        return JulgamentoDeAptidao(
            atividade=regra.atividade,
            rotulo=regra.rotulo,
            nivel=RUIM,
            motivo=motivo,
        )

    nivel = BOA if _e_boa(dia, regra) else MEDIA
    return JulgamentoDeAptidao(
        atividade=regra.atividade, rotulo=regra.rotulo, nivel=nivel, motivo=None
    )


def julgar_dia(dia: dict) -> list[JulgamentoDeAptidao]:
    """A aptidao de um dia para as quatro atividades.

    Recebe **so o dia**, e e a assinatura que faz o ADR 0011 valer: nao ha por
    onde uma cidade ou uma climatologia entrar na conta, entao a mesma entrada
    meteorologica produz a mesma aptidao em Manaus e em Wellington.

    Sempre as quatro, e sempre na mesma ordem: a grade pinta a atividade
    escolhida, e a faixa de planos le a do plano. Nenhuma das duas quer
    descobrir quais atividades vieram.
    """
    return [_julgar(dia, regra) for regra in ATIVIDADES]


def julgar_dia_do_bloco(daily: dict, indice: int) -> list[JulgamentoDeAptidao]:
    """A aptidao de um dia **do bloco diario** da Open-Meteo.

    O bloco vem como listas paralelas (`{"precipitation_sum": [...], ...}`), e
    esta funcao recorta a coluna do dia antes de julgar. Existe para que
    `julgar_dia` receba um dia como dicionario plano e continue testavel sem
    montar o formato da API externa.
    """
    return julgar_dia(
        {
            campo: valores[indice]
            for campo, valores in daily.items()
            if isinstance(valores, list) and indice < len(valores)
        }
    )
