/**
 * O filtro temporal: 7 dias, 30 dias ou 6 meses.
 *
 * Governa a **pagina inteira** — todo grafico e toda metrica abaixo reagem a
 * ele —, e por isso fica no topo e nao dentro de um cartao.
 *
 * O intervalo de datas aparece ao lado, e nao dentro do botao: ele diz que "30
 * dias" termina hoje, o que nao se deduz do rotulo. As datas vem prontas do
 * payload; a interface nao recalcula janela.
 */

import type { Janela, Periodo } from "../../api/types";
import { intervalo } from "../../formato";
import { JANELAS } from "../../janelaNaUrl";

type Props = {
  janela: Janela;
  /** `null` enquanto o historico nao chegou: so entao ha datas a exibir. */
  periodo: Periodo | null;
  carregando: boolean;
  onEscolher: (janela: Janela) => void;
};

export function FiltroDeJanela({
  janela,
  periodo,
  carregando,
  onEscolher,
}: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* `radiogroup`: as tres sao uma escolha unica, nao tres acoes soltas. */}
      <div
        role="radiogroup"
        aria-label="Janela temporal"
        className="flex gap-1 rounded-inner bg-card p-1 shadow-card"
      >
        {JANELAS.map(({ valor, rotulo }) => {
          const ativa = valor === janela;
          return (
            <button
              key={valor}
              type="button"
              role="radio"
              aria-checked={ativa}
              onClick={() => onEscolher(valor)}
              className={`rounded-lg px-3 py-1.5 text-[12px] font-medium transition-colors ${
                ativa
                  ? "bg-brand text-white"
                  : "text-ink-2 hover:bg-brand-soft hover:text-brand-text"
              }`}
            >
              {rotulo}
            </button>
          );
        })}
      </div>

      {/* O intervalo **permanece** enquanto a janela nova carrega, em vez de
          ser substituido pelo aviso. Trocar a janela a cada clique fazia a
          unica coisa que data a tela piscar para fora; as duas informacoes nao
          competem — uma diz o que se esta vendo, a outra que vem coisa nova. */}
      {periodo && (
        <p className="text-[12px] text-ink-2">
          {intervalo(periodo.inicio, periodo.fim)}
        </p>
      )}

      {/* A pessoa que clicou precisa ver que o clique foi registrado; sem
          isto, trocar de janela nao muda nada visivel por ate um segundo. */}
      {carregando && (
        <p role="status" className="text-[12px] text-ink-3">
          Carregando o historico…
        </p>
      )}
    </div>
  );
}
