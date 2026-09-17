/**
 * O seletor de atividade, no topo da pagina Calendario.
 *
 * Governa a **pagina inteira** — as sete celulas do horizonte curto se repintam
 * por ele —, e por isso fica no topo e fora de qualquer cartao, exatamente como
 * o `FiltroDeJanela` da Tendencia, que governa a pagina dele do mesmo jeito.
 *
 * ## As cinco opcoes, e por que "Nenhuma" e uma delas
 *
 * Sao quatro atividades **mais** o estado sem atividade escolhida, e ele e um
 * botao como os outros em vez de um "x" para limpar. Duas razoes:
 *
 * 1. **E o estado inicial, e nao a limpeza de um estado.** A pagina abre sem
 *    pintura — e como a fatia 04 a deixou — e voltar para la e uma escolha tao
 *    legitima quanto escolher plantio. Um "x" o trataria como desfazer.
 * 2. **Num `radiogroup` de teclado, sair da escolha exige um alvo.** Com quatro
 *    botoes e um "x" a parte, quem navega por setas nao teria como alcancar o
 *    estado sem pintura sem sair do grupo.
 *
 * ## Os rotulos vem do backend
 *
 * "Lavar roupa", "Esporte ao ar livre" — as frases sao as de
 * `JulgamentoDeAptidao.rotulo`, extraidas do primeiro dia do horizonte curto, e
 * **nao** um mapa de `Atividade` para texto escrito aqui. Escrevê-lo faria o
 * segundo lugar que precisa concordar com o backend na hora de renomear uma
 * atividade, que e o que o campo `rotulo` existe para evitar.
 *
 * A consequencia e que o seletor **so aparece quando ha aptidao**: sem os
 * rotulos nao ha o que desenhar. E o comportamento certo — um seletor que nao
 * pinta nada nao serve para nada.
 */

import type { Atividade, JulgamentoDeAptidao } from "../../api/types";
import { GrupoDeRadio } from "../GrupoDeRadio";

type Props = {
  /** Os julgamentos de um dia do horizonte curto, so pelos rotulos. */
  rotulos: JulgamentoDeAptidao[];
  escolhida: Atividade | null;
  onEscolher: (atividade: Atividade | null) => void;
};

export function SeletorDeAtividade({ rotulos, escolhida, onEscolher }: Props) {
  if (rotulos.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-3">
        {/* As cinco sao uma escolha unica, nao cinco acoes soltas — o mesmo
            papel que o `FiltroDeJanela` usa, e agora o mesmo componente.

            "Nenhuma" entra como a primeira opcao, com `null` por valor: e o
            estado inicial da pagina, e num grupo de radio navegavel por setas
            ele precisa ser um alvo alcancavel como os outros. */}
        <GrupoDeRadio<Atividade | null>
          rotulo="Atividade para julgar os dias"
          opcoes={[
            { valor: null, rotulo: "Nenhuma" },
            ...rotulos.map((julgamento) => ({
              valor: julgamento.atividade,
              rotulo: julgamento.rotulo,
            })),
          ]}
          escolhida={escolhida}
          onEscolher={onEscolher}
        />
      </div>

      {/*
        O rotulo de que a aptidao e **nossa**, e nao conselho de autoridade.

        Mesma obrigacao que o ADR 0001 impos a cada card de condicao prevista, e
        pelo mesmo motivo: sem ela, "esporte: ruim" lido solto se confunde com
        aviso oficial. O card de condicao prevista imprime "Derivado da
        previsao"; aqui a frase diz tambem **de quem** e o criterio, porque uma
        aptidao e mais opinativa que uma condicao — o limiar de "bom para lavar
        roupa" e uma escolha nossa de um jeito que "rajada de 86 km/h" nao e.

        Fica junto do seletor e nao dentro de cada celula: sao sete celulas
        pequenas, e repetir a ressalva em todas a tornaria ruido que ninguem le.
        Aqui ela aparece uma vez, exatamente onde a escolha e feita.
      */}
      <p className="text-[11px] text-ink-3">
        A aptidao e derivada da previsao por criterios nossos, e nao e
        recomendacao de autoridade meteorologica.
      </p>
    </div>
  );
}
