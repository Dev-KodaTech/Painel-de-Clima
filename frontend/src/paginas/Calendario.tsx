/**
 * A pagina Calendario: dezesseis dias numa grade, com a fronteira do dia 8.
 *
 * E a pagina que olha **mais longe** que qualquer outra. As demais paginas de
 * cidade respondem sobre agora e sobre os proximos sete dias; esta vai ate o
 * dia 16 — e a metade distante vem com menos precisao declarada, que e o
 * assunto da `Grade`.
 *
 * Dezesseis e o teto do endpoint da Open-Meteo, e nao uma escolha de produto
 * sobre trinta: o ADR 0010 mede por que trinta dias nao existem honestamente.
 *
 * ## Por que a requisicao mora aqui, e nao no `Shell`
 *
 * Regra do `docs/adr/0003-historico-e-buscado-na-pagina.md`, a mesma que a
 * Tendencia e a Condicoes seguem: **dado que so uma pagina le vai nela.** So
 * esta le `/api/horizonte` — as outras cinco nunca leem o dia 12, e engordar a
 * chamada do painel faria todas pagarem por ele.
 *
 * A chamada do painel **nao muda** por causa desta pagina, e o custo aceito e
 * que abrir a Visao geral e depois esta custa duas requisicoes externas. E o
 * correto: a alternativa era a grade receber sete dias.
 *
 * ## O que esta fatia ainda nao traz
 *
 * Aptidao (a grade pintada pela atividade escolhida) e planos (a faixa lateral
 * de quem tem conta) sao as fatias seguintes. A pagina e util sozinha assim —
 * e a razao de ela ter sido cortada aqui.
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import { buscarHorizonte, mensagemDeErro } from "../api/client";
import type { DiaDoHorizonte } from "../api/types";
import { cidadeDosParametros } from "../cidadeNaUrl";
import { Grade } from "../components/calendario/Grade";
import { Painel } from "../components/Painel";
import { usePainel } from "../estadoDoPainel";

/**
 * O que a requisicao devolveu, carimbado com a coordenada que a originou.
 *
 * O mesmo padrao da Tendencia e da Condicoes, e pelo mesmo motivo: com a chave
 * junto, "carregando" e **derivado** — um resultado de outra cidade significa
 * que o desta ainda nao chegou. Sem o carimbo, trocar de cidade deixaria a
 * grade anterior na tela sem sinal nenhum de que e a anterior.
 */
type Resultado =
  | {
      chave: string;
      tipo: "pronto";
      dias: DiaDoHorizonte[];
      attribution: string;
    }
  | { chave: string; tipo: "erro"; mensagem: string };

export function Calendario() {
  const { estado } = usePainel();
  const [parametros] = useSearchParams();
  const [resultado, setResultado] = useState<Resultado | null>(null);

  const cidade = cidadeDosParametros(parametros);
  const latitude = cidade?.latitude;
  const longitude = cidade?.longitude;
  // So a coordenada: mudar `name` ou `admin1` sem mudar a coordenada e a mesma
  // consulta. E e ela que muda quando se troca de cidade, que e o que precisa
  // recarregar a grade.
  const chave = latitude === undefined ? null : `${latitude},${longitude}`;

  useEffect(() => {
    if (chave === null || latitude === undefined || longitude === undefined) {
      return;
    }

    const controller = new AbortController();

    buscarHorizonte({ latitude, longitude }, controller.signal)
      .then((resposta) =>
        setResultado({
          chave,
          tipo: "pronto",
          dias: resposta.dias,
          attribution: resposta.attribution,
        }),
      )
      .catch((falha: unknown) => {
        if (controller.signal.aborted) return;
        setResultado({
          chave,
          tipo: "erro",
          mensagem: mensagemDeErro(
            falha,
            "Nao foi possivel carregar a previsao dos proximos dias.",
          ),
        });
      });

    return () => controller.abort();
  }, [chave, latitude, longitude]);

  // Nada, de proposito: o app ainda decide se abre com uma cidade, e a
  // instrucao de buscar uma seria errada por um instante.
  if (estado.tipo === "decidindo") return null;

  if (!cidade) {
    return (
      <p className="py-6 text-[13px] text-ink-2">
        Busque uma cidade para ver os proximos dezesseis dias.
      </p>
    );
  }

  const pronto = resultado?.chave === chave && resultado.tipo === "pronto";
  const erro =
    resultado?.chave === chave && resultado.tipo === "erro"
      ? resultado.mensagem
      : null;

  // As unidades vem do painel, como nas outras paginas de cidade: o
  // `/api/horizonte` nao as repete. Enquanto o painel carrega, o grau
  // arredondado ainda e o que se exibe — e o `°C` e o padrao do backend.
  const units =
    estado.tipo === "pronto" ? estado.painel.units : { temperature: "°C" };

  return (
    <section className="flex flex-col gap-4 py-2">
      <h2 className="text-lg font-semibold">Calendario</h2>

      {!pronto && !erro && (
        <p role="status" className="py-6 text-[13px] text-ink-2">
          Carregando os proximos dias…
        </p>
      )}

      {/* Declarado, e nao uma grade vazia: dezesseis celulas em branco se leem
          como "nao vai fazer tempo nenhum", que e o defeito que o ADR 0001
          combate do outro lado. */}
      {erro && (
        <p role="alert" className="py-6 text-[13px] text-ink-2">
          {erro}
        </p>
      )}

      {pronto && (
        <>
          <Painel titulo="Proximos dezesseis dias">
            <Grade dias={resultado.dias} units={units} />
          </Painel>

          {/*
            A atribuicao da grade, omitida so quando o rodape do `Shell` ja
            esta dizendo **exatamente a mesma frase**.

            A comparacao e por valor, e nao por estado do painel. As duas
            chamadas creditam as mesmas fontes hoje, e renderizar as duas
            deixava a linha repetida uma embaixo da outra — foi o que a pagina
            rodando mostrou. Mas `atribuicao()` no backend ja tem um ramo que
            muda o texto (`com_inmet`), e no dia em que o horizonte creditar
            algo que o painel nao credita, comparar estado esconderia a
            diferenca: a pagina mostraria o credito do painel no lugar do seu.
            Comparar o texto nao tem como errar isso — se as frases divergirem,
            as duas aparecem.

            O painel tambem pode falhar enquanto a grade carrega — sao
            requisicoes independentes —, e ai o `Shell` nao desenha rodape
            nenhum e este entra sozinho. Em nenhum caminho o credito que a
            licenca pede sai da tela.
          */}
          {(estado.tipo !== "pronto" ||
            estado.painel.attribution !== resultado.attribution) && (
            <footer className="text-[11px] text-ink-3">
              {resultado.attribution}
            </footer>
          )}
        </>
      )}
    </section>
  );
}
