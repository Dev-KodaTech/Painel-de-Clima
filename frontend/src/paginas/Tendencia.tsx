/**
 * A pagina Tendencia: a pagina de analise do painel.
 *
 * E o unico lugar do app que **olha para tras**. As outras cinco paginas
 * respondem "como esta o tempo agora e nos proximos sete dias"; esta responde
 * "este periodo esta fora do normal?", comparando a janela escolhida com o
 * mesmo periodo do ano anterior.
 *
 * ## Por que a requisicao mora aqui, e nao no `Shell`
 *
 * E a excecao deliberada a regra do `docs/adr/0002-cidade-na-url.md`, e o
 * motivo e o mesmo que o ADR usou para rejeitar a terceira opcao — so
 * invertido. La, o que se queria evitar era uma requisicao que toda troca de
 * pagina refaz; aqui, o `Shell` buscando o historico faria **as seis paginas**
 * pagarem por ele.
 *
 * A regra, para quem acrescentar a setima pagina e encontrar dois precedentes:
 * **dado que varias paginas leem vai no `Shell`; dado que so uma pagina le vai
 * nela.**
 *
 * A consequencia a aceitar e que sair da Tendencia e voltar refaz a requisicao.
 * O cache do backend absorve — e por isso que a volta e instantanea, e nao por
 * estado guardado aqui.
 *
 * ## Os estados sao **dela**
 *
 * O carregamento e o erro do historico nao tocam nos estados do painel que vem
 * do `Shell`: o cabecalho e a atribuicao continuam pintados enquanto o arquivo
 * carrega, e um arquivo que falha nao apaga a pagina inteira.
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import { buscarHistorico, mensagemDeErro } from "../api/client";
import type { Janela, TrendsResponse } from "../api/types";
import { cidadeDosParametros } from "../cidadeNaUrl";
import { Chuva } from "../components/tendencia/Chuva";
import { FiltroDeJanela } from "../components/tendencia/FiltroDeJanela";
import { HistoricoClimatologico } from "../components/tendencia/HistoricoClimatologico";
import { IndiceUv } from "../components/tendencia/IndiceUv";
import { Umidade } from "../components/tendencia/Umidade";
import { Vento } from "../components/tendencia/Vento";
import { usePainel } from "../estadoDoPainel";
import { ano } from "../formato";
import { comJanela, janelaDosParametros } from "../janelaNaUrl";

/**
 * O que a requisicao devolveu, carimbado com a consulta que a originou.
 *
 * O mesmo padrao do `Shell`, e pelo mesmo motivo: com a chave junto,
 * "carregando" e **derivado** — um resultado de outra janela significa que esta
 * ainda nao chegou. Sem o carimbo, trocar de janela deixaria os graficos
 * antigos na tela sem sinal nenhum de que sao os antigos.
 */
type Resultado =
  | { chave: string; tipo: "pronto"; historico: TrendsResponse }
  | { chave: string; tipo: "erro"; mensagem: string };

export function Tendencia() {
  const { estado } = usePainel();
  const [parametros, setParametros] = useSearchParams();
  const [resultado, setResultado] = useState<Resultado | null>(null);

  const janela = janelaDosParametros(parametros);
  const cidade = cidadeDosParametros(parametros);

  // A coordenada e a janela, e nao a URL inteira: mudar `name` ou `admin1` sem
  // mudar a coordenada e a mesma consulta ao arquivo.
  //
  // A chave e **so** a identidade da consulta, para o efeito comparar. Os
  // valores que a requisicao usa sao lidos das variaveis, nao desmontados da
  // chave de volta: reconstrui-los exigiria um `as Janela` sobre um pedaco de
  // texto, que e justamente o furo que a uniao fechada existe para impedir.
  const latitude = cidade?.latitude;
  const longitude = cidade?.longitude;
  const chave =
    latitude === undefined ? null : `${latitude},${longitude},${janela}`;

  useEffect(() => {
    if (chave === null || latitude === undefined || longitude === undefined) {
      return;
    }

    const controller = new AbortController();

    buscarHistorico({ latitude, longitude }, janela, controller.signal)
      .then((historico) => setResultado({ chave, tipo: "pronto", historico }))
      .catch((falha: unknown) => {
        if (controller.signal.aborted) return;
        setResultado({
          chave,
          tipo: "erro",
          mensagem: mensagemDeErro(
            falha,
            "Nao foi possivel carregar o historico.",
          ),
        });
      });

    return () => controller.abort();
    // `chave` entra junto porque e o que carimba o resultado; os tres valores
    // que a requisicao usa mudam exatamente quando ela muda.
  }, [chave, latitude, longitude, janela]);

  /** Trocar de janela e trocar a URL; o efeito acima faz o resto. */
  function escolherJanela(escolhida: Janela) {
    // `setSearchParams` preserva os parametros da cidade: a janela entra ao
    // lado deles, e trocar de cidade depois nao a perde.
    setParametros(comJanela(parametros, escolhida), { replace: true });
  }

  // Nada, de proposito: o app ainda decide se abre com uma cidade, e a
  // instrucao de buscar uma seria errada por um instante.
  if (estado.tipo === "decidindo") return null;

  // Sem cidade, a pagina e a mesma instrucao das outras — e o filtro nem
  // aparece: nao ha o que filtrar.
  if (!cidade) {
    return (
      <p className="py-6 text-[13px] text-ink-2">
        Busque uma cidade para ver o historico climatologico.
      </p>
    );
  }

  const pronto = resultado?.chave === chave && resultado.tipo === "pronto";
  const historico = pronto ? resultado.historico : null;
  const erro =
    resultado?.chave === chave && resultado.tipo === "erro"
      ? resultado.mensagem
      : null;

  return (
    <section className="flex flex-col gap-4 py-2">
      <FiltroDeJanela
        janela={janela}
        periodo={historico?.periodo ?? null}
        carregando={!historico && !erro}
        onEscolher={escolherJanela}
      />

      {erro && (
        <p role="alert" className="py-4 text-[13px] text-ink-2">
          {erro}
        </p>
      )}

      {historico && <Conteudo historico={historico} />}
    </section>
  );
}

/**
 * Os paineis, uma vez que o historico chegou.
 *
 * Separado para que o corpo acima trate so estado: com os dois juntos, cada
 * `historico.` teria de ser lido atraves de um opcional que aqui ja se sabe
 * preenchido.
 */
function Conteudo({ historico }: { historico: TrendsResponse }) {
  const { serie, comparacao, resumo, uv, units } = historico;
  const anoAnterior = comparacao.length > 0 ? ano(comparacao[0].date) : null;

  return (
    <div className="flex flex-col gap-4">
      <HistoricoClimatologico
        serie={serie}
        comparacao={comparacao}
        diferencaMedia={resumo.diferenca_media}
        units={units}
      />

      {/* Duas colunas no desktop, empilhadas no estreito: os graficos ficam
          legiveis nos dois, e a pagina nao e exclusiva de tela grande. */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Chuva
          serie={serie}
          resumo={resumo}
          anoAnterior={anoAnterior}
          units={units}
        />
        <Umidade serie={serie} resumo={resumo} units={units} />
        <Vento serie={serie} resumo={resumo} units={units} />
        <IndiceUv uv={uv} units={units} />
      </div>
    </div>
  );
}
