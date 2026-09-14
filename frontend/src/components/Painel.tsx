/**
 * A moldura comum dos paineis: cartao branco, cantos arredondados, sombra e
 * titulo.
 *
 * Existe porque o grid tem nove paineis que compartilham exatamente esta
 * casca — o padding de 18 px e o raio de 20 px sao tokens do design, nao
 * escolha de cada card. Centralizando-a, mudar o espacamento do design e uma
 * edicao, nao nove.
 *
 * O titulo e obrigatorio: todo painel do design tem um, e um cartao sem
 * cabecalho seria um estado que o layout nao preve.
 */

import type { ReactNode } from "react";

type Props = {
  titulo: string;
  children: ReactNode;
  /** Classes extras do container, para o painel que precisa de altura propria. */
  className?: string;
};

export function Painel({ titulo, children, className = "" }: Props) {
  return (
    <section className={`rounded-card bg-card p-[18px] shadow-card ${className}`}>
      <h2 className="mb-3.5 text-sm font-semibold">{titulo}</h2>
      {children}
    </section>
  );
}
