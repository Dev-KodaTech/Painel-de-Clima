/**
 * O detalhe de um dia: a previsao completa e as **quatro** aptidoes.
 *
 * ## Por que as quatro, e nao a escolhida
 *
 * A grade pinta uma atividade por vez porque ela responde "qual dia serve para
 * isto?" — a pergunta e sobre os dias, e a atividade e fixa. **Clicar num dia
 * inverte a pergunta**: quem abriu o dia 22 quer saber sobre o dia 22, e
 * mostrar so a aptidao que por acaso estava selecionada na grade esconderia que
 * o dia e otimo para viajar e pessimo para lavar roupa. E a issue 06 e
 * explicita: quem clicou num dia quer saber sobre o dia.
 *
 * E o lugar onde o **motivo** aparece (story 12). Ele nao cabe nas celulas da
 * grade — sete frases como "Umidade media de 94%" ao mesmo tempo seriam um
 * relatorio no lugar de uma varredura —, e e exatamente por isso que existe um
 * detalhe: a grade responde *qual dia*, o detalhe responde *por que*.
 *
 * ## Um dialogo escrito a mao
 *
 * O repo nao tem precedente de modal — o `BuscaCidade` trata `Escape` no
 * proprio campo e nao abre camada nenhuma. Este e o primeiro, e por isso carrega
 * o minimo que um dialogo precisa para nao ser uma armadilha de teclado: papel
 * declarado, foco movido para dentro ao abrir, `Escape` fecha, o foco volta para
 * a celula que o abriu, e o clique no fundo tambem fecha.
 *
 * Nao e `<dialog>` nativo com `showModal()`, apesar de ele dar o `Escape` e o
 * `inert` de graca: o elemento nativo renderiza no *top layer*, fora do
 * `:root[data-tema]` para efeito de alguns estilos de agente, e o repo inteiro
 * depende de tokens herdados. Um dialogo de tres paragrafos nao vale essa
 * investigacao — e o comportamento que ele daria de graca esta escrito aqui e
 * cabe numa tela.
 */

import { useEffect, useRef } from "react";
import type { DiaDoHorizonte, Units } from "../../api/types";
import {
  dataPorExtenso,
  precipitacao,
  probabilidade,
  temperatura,
} from "../../formato";
import { WeatherIcon } from "../WeatherIcon";
import { ANUNCIO, COR_DO_NIVEL, PALAVRA } from "./aptidao";

/**
 * So as duas unidades que o detalhe escreve.
 *
 * `Pick` e nao `Units` inteiro, pela mesma razao de `UnidadesDaGrade`: o
 * detalhe nao mostra vento nem distancia, e pedir os quatro campos obrigaria a
 * pagina a inventar dois valores enquanto o painel ainda carrega — que e
 * exatamente o estado em que ela pode estar quando alguem clica num dia.
 */
export type UnidadesDoDetalhe = Pick<Units, "temperature" | "precipitation">;

type Props = {
  dia: DiaDoHorizonte;
  units: UnidadesDoDetalhe;
  onFechar: () => void;
};

export function DetalheDoDia({ dia, units, onFechar }: Props) {
  const fechar = useRef<HTMLButtonElement>(null);

  // O foco entra no dialogo ao abrir e **volta para a celula ao fechar**. Sem a
  // ida, o foco continua na celula atras da camada e `Tab` anda pela grade que
  // o dialogo esta cobrindo; sem a volta, fechar joga o foco para o inicio do
  // documento e quem navega por teclado perde o lugar na grade — teria de
  // percorrer a pagina de novo para chegar ao dia seguinte.
  //
  // O elemento e guardado no momento da abertura, e nao procurado na hora de
  // fechar: ao fechar o dialogo, quem tinha o foco e o botao "Fechar" que esta
  // prestes a sair do DOM.
  useEffect(() => {
    const abriu = document.activeElement;
    fechar.current?.focus();

    return () => {
      // `isConnected`: trocar de cidade com o detalhe aberto remonta a grade, e
      // a celula guardada pode ja nao estar no documento. Focar um elemento
      // solto nao lanca, mas tambem nao move o foco para lugar nenhum — o
      // `if` deixa claro que o caso foi considerado.
      if (abriu instanceof HTMLElement && abriu.isConnected) abriu.focus();
    };
  }, []);

  // `Escape` em qualquer lugar do dialogo, e nao so no botao: quem chegou ao
  // conteudo com `Tab` fecha de onde estiver.
  useEffect(() => {
    function aoTeclar(evento: KeyboardEvent) {
      if (evento.key === "Escape") onFechar();
    }
    document.addEventListener("keydown", aoTeclar);
    return () => document.removeEventListener("keydown", aoTeclar);
  }, [onFechar]);

  return (
    // O fundo escurecido, que tambem fecha ao clique. `aria-hidden` nao entra
    // aqui: o dialogo e filho dele.
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-ink/40 p-4 sm:items-center"
      onClick={onFechar}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Previsao e aptidoes de ${dataPorExtenso(dia.date)}`}
        // O clique dentro nao fecha: sem isto, selecionar o texto do motivo
        // fecharia o dialogo no meio da leitura.
        onClick={(evento) => evento.stopPropagation()}
        className="flex max-h-[80vh] w-full max-w-sm flex-col gap-3 overflow-y-auto rounded-card bg-card p-4 shadow-card"
      >
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-[15px] font-semibold">
            {dataPorExtenso(dia.date)}
          </h3>
          <button
            ref={fechar}
            type="button"
            onClick={onFechar}
            aria-label="Fechar o detalhe do dia"
            className="shrink-0 rounded-lg px-2 py-1 text-[12px] font-medium text-ink-2 outline-none transition-colors hover:bg-brand-soft hover:text-brand-text focus:ring-2 focus:ring-brand/40"
          >
            Fechar
          </button>
        </div>

        <Previsao dia={dia} units={units} />

        {dia.aptidoes.length > 0 ? (
          <Aptidoes dia={dia} />
        ) : (
          /* O horizonte longo, dito no lugar onde a ausencia seria notada.
             A nota da fronteira, abaixo da grade, explica a metade distante
             como um todo; quem abriu **este** dia precisa da razao aqui, ou a
             lista de aptidoes sumida parece falha. */
          <p className="text-[12px] text-ink-2">
            Este dia esta longe demais para julgar aptidao: a essa distancia a
            previsao ja nao sustenta conselho sobre lavar roupa ou plantar.
          </p>
        )}
      </div>
    </div>
  );
}

function Previsao({
  dia,
  units,
}: {
  dia: DiaDoHorizonte;
  units: UnidadesDoDetalhe;
}) {
  return (
    <div className="flex items-center gap-3 rounded-inner bg-brand-soft p-3">
      {dia.icon && dia.description && (
        <WeatherIcon icon={dia.icon} description={dia.description} className="size-9" decorativo />
      )}
      <div className="flex flex-col gap-0.5">
        {dia.description && (
          <p className="text-[13px] font-medium">{dia.description}</p>
        )}
        <p className="text-[12px] text-ink-2">
          {dia.high !== null && dia.low !== null
            ? `Maxima de ${temperatura(dia.high, units.temperature)}, minima de ${temperatura(dia.low, units.temperature)}`
            : "Sem previsao de temperatura para este dia"}
        </p>
        {dia.precipitation_mm !== null && (
          <p className="text-[12px] text-ink-2">
            {precipitacao(dia.precipitation_mm, units.precipitation)} de chuva
          </p>
        )}
        {dia.precipitation_probability_max !== null && (
          <p className="text-[12px] text-ink-2">
            {probabilidade(dia.precipitation_probability_max)} de chance de
            chuva
          </p>
        )}
      </div>
    </div>
  );
}

/**
 * As quatro aptidoes, cada uma com o seu motivo.
 *
 * O nivel e **palavra colorida**, e nao faixa preenchida: quatro faixas de cor
 * empilhadas fariam um arco-iris onde o que importa e ler quatro julgamentos.
 * A cor reforca, a palavra informa — a mesma regra da celula da grade.
 */
function Aptidoes({ dia }: { dia: DiaDoHorizonte }) {
  return (
    <div className="flex flex-col gap-2">
      <h4 className="text-[12px] font-semibold text-ink-2">
        O quanto o dia serve para cada atividade
      </h4>
      <ul className="flex flex-col gap-2">
        {dia.aptidoes.map((julgamento) => (
          <li
            key={julgamento.atividade}
            className="flex flex-col gap-0.5 rounded-inner border border-line p-2.5"
          >
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-[13px]">{julgamento.rotulo}</span>
              <span
                className={`text-[12px] font-semibold ${COR_DO_NIVEL[julgamento.nivel]}`}
              >
                {/* A palavra e visivel; o leitor de tela ouve a frase inteira,
                    porque "boa" solto depois de "Viagem" nao diz boa para que. */}
                <span aria-hidden="true">{PALAVRA[julgamento.nivel]}</span>
                <span className="sr-only">
                  {ANUNCIO[julgamento.nivel]} {julgamento.rotulo.toLowerCase()}
                </span>
              </span>
            </div>
            {/* So o nivel `ruim` tem motivo — um dia bom nao tem motivo a dar,
                e "nada atrapalha" nao e informacao. */}
            {julgamento.motivo && (
              <p className="text-[11px] text-ink-2">
                {julgamento.motivo.texto}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
