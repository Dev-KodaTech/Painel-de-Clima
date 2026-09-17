/**
 * Um grupo de escolha unica: a moldura `radiogroup` e as suas pilulas.
 *
 * Duas paginas escolhem assim, e **a aparencia e o papel sao os mesmos nas
 * duas**: o `FiltroDeJanela` da Tendencia escolhe a janela temporal, o
 * `SeletorDeAtividade` do Calendario escolhe a atividade. Os dois ficam no topo
 * da pagina, fora de cartao, porque governam tudo abaixo deles.
 *
 * Extraido pela mesma regra que fez `DIAS_CURTOS` sair para o `formato.ts`: uma
 * copia local seria um lugar a mais para discordar na primeira vez que alguem
 * mexesse no `hover`, no foco — ou no teclado. Aqui a razao pesa mais que la,
 * porque estas classes carregam o **estado selecionado**, e duas copias
 * divergindo fariam a escolha ativa parecer diferente em duas paginas que fazem
 * a mesma coisa.
 *
 * ## Por que o grupo tambem mora aqui, e nao so a pilula
 *
 * `role="radiogroup"` **promete navegacao por setas e uma unica parada de
 * tabulacao**, e essa promessa nao se cumpre numa pilula isolada: quem
 * implementa setas precisa conhecer os irmaos. Com so a pilula compartilhada,
 * cada pagina montava a sua moldura e nenhuma das duas cumpria o contrato que
 * o papel anuncia — as cinco opcoes eram cinco paradas de `Tab` e as setas nao
 * faziam nada.
 *
 * O padrao implementado e o do WAI-ARIA para `radiogroup`: **tabindex
 * rotativo** (so a opcao ativa recebe `0`; as demais, `-1`), setas andam e
 * dao a volta, `Home`/`End` vao as pontas, e mover a selecao ja **escolhe** —
 * num grupo de radio a seta seleciona, e nao so move o foco.
 */

import { useRef } from "react";

/** Uma opcao do grupo. `valor` e a chave por onde quem usa a reconhece. */
export type OpcaoDoGrupo<T> = {
  valor: T;
  rotulo: string;
};

type Props<T> = {
  /** O que o grupo significa. Cada pagina descreve o seu. */
  rotulo: string;
  opcoes: OpcaoDoGrupo<T>[];
  escolhida: T;
  onEscolher: (valor: T) => void;
};

export function GrupoDeRadio<T>({
  rotulo,
  opcoes,
  escolhida,
  onEscolher,
}: Props<T>) {
  const grupo = useRef<HTMLDivElement>(null);

  function aoTeclar(evento: React.KeyboardEvent, indice: number) {
    // `Home`/`End` primeiro: sao absolutos e nao dependem do indice atual.
    const destino =
      evento.key === "Home"
        ? 0
        : evento.key === "End"
          ? opcoes.length - 1
          : evento.key === "ArrowRight" || evento.key === "ArrowDown"
            ? // A volta no fim: um grupo de radio e circular, e parar na ultima
              // obrigaria a voltar por cinco setas para alcancar a primeira.
              (indice + 1) % opcoes.length
            : evento.key === "ArrowLeft" || evento.key === "ArrowUp"
              ? (indice - 1 + opcoes.length) % opcoes.length
              : -1;

    if (destino === -1) return;

    // `preventDefault`: as setas rolariam a pagina por baixo da escolha.
    evento.preventDefault();
    onEscolher(opcoes[destino].valor);

    // O foco acompanha a selecao. Sem isto a proxima seta partiria do botao
    // antigo, que acabou de perder o `tabindex`, e a navegacao travaria.
    const botoes = grupo.current?.querySelectorAll("button");
    botoes?.[destino]?.focus();
  }

  return (
    <div
      ref={grupo}
      role="radiogroup"
      aria-label={rotulo}
      className="flex flex-wrap gap-1 rounded-inner bg-card p-1 shadow-card"
    >
      {opcoes.map((opcao, indice) => {
        const ativa = opcao.valor === escolhida;
        return (
          <button
            key={String(opcao.valor)}
            type="button"
            role="radio"
            aria-checked={ativa}
            // O tabindex rotativo: o grupo inteiro e **uma** parada de `Tab`, e
            // e a opcao ativa que a recebe. Sem isto, tabular por uma pagina
            // com cinco atividades custaria cinco paradas para atravessar um
            // controle so.
            tabIndex={ativa ? 0 : -1}
            onClick={() => onEscolher(opcao.valor)}
            onKeyDown={(evento) => aoTeclar(evento, indice)}
            className={`rounded-lg px-3 py-1.5 text-[12px] font-medium outline-none transition-colors focus-visible:ring-2 focus-visible:ring-brand/50 ${
              ativa
                ? "bg-brand text-white"
                : "text-ink-2 hover:bg-brand-soft hover:text-brand-text"
            }`}
          >
            {opcao.rotulo}
          </button>
        );
      })}
    </div>
  );
}
