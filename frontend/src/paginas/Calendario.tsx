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
 * ## A atividade governa a pagina, e por isso mora na URL
 *
 * O seletor no topo pinta as sete celulas do horizonte curto pela aptidao da
 * atividade escolhida. A escolha viaja nos parametros (`atividadeNaUrl.ts`,
 * que registra a decisao e o precedente dividido que ela resolve): governa a
 * pagina inteira como a janela da Tendencia, e "manda o link do calendario
 * mostrando quando da para lavar roupa" e um compartilhamento que alguem faz.
 *
 * O estado **sem** atividade escolhida e o inicial, e nao a ausencia de um
 * padrao: a pagina abre mostrando so previsao, como a fatia 04 a deixou.
 *
 * ## O que esta fatia ainda nao traz
 *
 * Planos — a faixa lateral de quem tem conta — sao as fatias 07 e 08.
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import { buscarHorizonte, mensagemDeErro } from "../api/client";
import type { DiaDoHorizonte } from "../api/types";
import { atividadeDosParametros, comAtividade } from "../atividadeNaUrl";
import { cidadeDosParametros } from "../cidadeNaUrl";
import { julgamentoDe } from "../components/calendario/aptidao";
import { DetalheDoDia } from "../components/calendario/DetalheDoDia";
import { Grade } from "../components/calendario/Grade";
import { SeletorDeAtividade } from "../components/calendario/SeletorDeAtividade";
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
  const [parametros, setParametros] = useSearchParams();
  const [resultado, setResultado] = useState<Resultado | null>(null);
  /**
   * O dia aberto no detalhe, ou `null`.
   *
   * Guarda a **data** e nao o dia inteiro: a grade recarrega ao trocar de
   * cidade, e um objeto guardado aqui continuaria exibindo a previsao da cidade
   * anterior por tras de uma camada que se sobrepoe a grade nova. Com a data, o
   * dia e reencontrado no resultado corrente — e some sozinho se a cidade nova
   * nao o tiver.
   */
  const [diaAberto, setDiaAberto] = useState<string | null>(null);

  const atividade = atividadeDosParametros(parametros);

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
  // arredondado ainda e o que se exibe — e o `°C` e o `mm` sao os padroes do
  // backend.
  const units =
    estado.tipo === "pronto"
      ? estado.painel.units
      : { temperature: "°C", precipitation: "mm" };

  const dias = resultado?.chave === chave && pronto ? resultado.dias : [];

  /**
   * Os rotulos das atividades, tirados do primeiro dia que tem aptidao.
   *
   * O horizonte curto vem sempre com as quatro, e sempre na mesma ordem, entao
   * qualquer dia serve. O `find` existe para o caso de uma resposta encurtada
   * comecar no horizonte longo, e nao porque os dias divirjam entre si.
   */
  const rotulos = dias.find((dia) => dia.aptidoes.length > 0)?.aptidoes ?? [];

  /**
   * O julgamento escolhido em cada dia do horizonte curto.
   *
   * So para saber se **algum** dia serve — a pintura em si e da celula, que
   * procura o seu. Aqui interessa a semana inteira.
   */
  const julgamentos = dias
    .map((dia) => julgamentoDe(dia, atividade))
    .filter((j) => j !== null);

  /**
   * Se **nenhum** dos sete dias e bom para a atividade escolhida.
   *
   * A condicao e "nenhum `boa`", e nao "todos `ruim`". A story 15 fala de uma
   * semana em que **nenhum dia serve**, e uma semana inteira de `media` e
   * exatamente isso: nao ha dia bom para lavar roupa, e a pessoa precisa saber
   * para decidir adiar. Com "todos ruim" um unico `media` no meio de seis
   * `ruim` calaria a mensagem — e essa e a semana tipica de uma cidade que o
   * ADR 0011 manda aceitar como sempre-ruim, nao a excecao.
   *
   * **Nao e erro, e o ADR 0011 e explicito**: a aptidao de uma cidade pode ser
   * sempre ruim para uma atividade, e isso e um resultado valido a ser
   * mostrado. E a mesma distincao que `status_dos_alertas` faz entre "sem
   * alerta" e "sem resposta" — a lista vazia seria a falha, e esta e uma lista
   * cheia de julgamentos que simplesmente nao tem um bom.
   */
  const nenhumDiaBom =
    julgamentos.length > 0 && !julgamentos.some((j) => j.nivel === "boa");

  const aberto = dias.find((dia) => dia.date === diaAberto) ?? null;

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
          <SeletorDeAtividade
            rotulos={rotulos}
            escolhida={atividade}
            onEscolher={(proxima) =>
              // `replace`: trocar de atividade nao e navegar. Sem ele, escolher
              // as quatro em sequencia empilharia quatro entradas no historico
              // e o botao "voltar" andaria uma atividade por clique em vez de
              // sair da pagina.
              setParametros(comAtividade(parametros, proxima), {
                replace: true,
              })
            }
          />

          {/*
            A semana em que nenhum dia serve.

            **Mensagem, e nao estado de erro** — ADR 0011: a aptidao de uma
            cidade pode ser sempre ruim para uma atividade, e isso e um
            resultado valido a ser mostrado, nao uma falha a ser suprimida. Dai
            nao ter `role="alert"` e nao substituir a grade: os sete dias
            continuam ali, pintados de ruim, e o motivo de cada um esta a um
            clique. A frase so diz o que a grade ja mostra, para que ninguem
            conclua que a pagina quebrou.
          */}
          {nenhumDiaBom && (
            <p className="rounded-inner border border-line p-3 text-[12px] text-ink-2">
              Nenhum dos proximos sete dias e bom para esta atividade — o tempo
              nao colabora nesta semana. Abra um dia para ver o que pesou.
            </p>
          )}

          <Painel titulo="Proximos dezesseis dias">
            <Grade
              dias={resultado.dias}
              units={units}
              atividade={atividade}
              onAbrirDia={(dia) => setDiaAberto(dia.date)}
            />
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

      {aberto && (
        <DetalheDoDia
          dia={aberto}
          units={units}
          onFechar={() => setDiaAberto(null)}
        />
      )}
    </section>
  );
}
