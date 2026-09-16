/**
 * A pagina Noticias: materias de clima e meio ambiente dos tres veiculos.
 *
 * **A unica pagina que nao depende da cidade escolhida.** Todas as outras
 * respondem "e aqui?"; esta e nacional e continua a mesma em Sorocaba e em
 * Belem (ADR 0009, e o verbete *Noticia* do `CONTEXT.md`). Tres consequencias
 * saem disso, e nenhuma e detalhe de estilo:
 *
 * - a requisicao **nao** entra em `useEffect` com chave de coordenada, como na
 *   Tendencia e na Condicoes — nao ha coordenada, e o efeito roda uma vez;
 * - a pagina nunca mostra "Busque uma cidade", e o cabecalho nem oferece a
 *   busca (`semCidade` em `navegacao.tsx`): pedir uma cidade para depois
 *   exibir uma lista que nao a usa seria pedir trabalho a toa;
 * - o veiculo aparece em **toda** linha. A licenca pede credito, e numa lista
 *   que mistura agencia publica, ONG e revista cientifica quem publicou e
 *   parte da informacao — nao e assinatura de rodape.
 *
 * ## Por que a requisicao mora aqui
 *
 * Regra do `docs/adr/0003-historico-e-buscado-na-pagina.md`: dado que so uma
 * pagina le, vai nela. So a Noticias le `/api/noticias`, e o custo dos tres
 * feeds nao deve recair sobre quem abriu a Visao geral. O cache do backend
 * absorve a ida e volta: meia hora de TTL, proprio desta consulta e nao o de
 * dez minutos da previsao, porque noticia muda em escala de horas.
 *
 * ## Quatro estados, nao tres
 *
 * Carregando, erro e pronto, como nas outras — mais a **degradacao parcial**,
 * que e propria daqui: `status: "ok"` com `veiculos_fora_do_ar` nao vazio e
 * uma pagina que funciona e esta incompleta, e diz as duas coisas. Colapsa-la
 * em "pronto" apresentaria uma lista curta como se fosse a lista inteira.
 */

import { useEffect, useState } from "react";
import { buscarNoticias, mensagemDeErro } from "../api/client";
import type { Noticia, StatusDasNoticias } from "../api/types";
import { Painel } from "../components/Painel";
import { publicadaEm } from "../formato";

type Resultado =
  | {
      tipo: "pronto";
      noticias: Noticia[];
      status: StatusDasNoticias;
      veiculosForaDoAr: string[];
      attribution: string;
    }
  | { tipo: "erro"; mensagem: string };

export function Noticias() {
  const [resultado, setResultado] = useState<Resultado | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    buscarNoticias(controller.signal)
      .then((resposta) =>
        setResultado({
          tipo: "pronto",
          noticias: resposta.noticias,
          status: resposta.status,
          veiculosForaDoAr: resposta.veiculos_fora_do_ar,
          attribution: resposta.attribution,
        }),
      )
      .catch((falha: unknown) => {
        if (controller.signal.aborted) return;
        setResultado({
          tipo: "erro",
          mensagem: mensagemDeErro(falha, "Nao foi possivel carregar as noticias."),
        });
      });

    return () => controller.abort();
    // Sem dependencias: nao ha cidade, janela nem parametro algum que possa
    // mudar — o efeito roda uma vez por montagem. E o que distingue esta
    // pagina de todas as outras.
  }, []);

  return (
    <section className="flex flex-col gap-4 py-2">
      <div>
        <h2 className="text-lg font-semibold">Noticias</h2>
        {/* Dito na pagina, e nao so no glossario: quem chega aqui vindo das
            outras paginas — todas sobre a sua cidade — precisa saber, antes de
            ler a primeira linha, que esta lista nao mudou de assunto por
            engano. */}
        <p className="mt-1 text-[12px] text-ink-3">
          Clima e meio ambiente no Brasil. Nao dependem da cidade escolhida.
        </p>
      </div>

      {resultado === null && (
        <p role="status" className="py-6 text-[13px] text-ink-2">
          Carregando as noticias…
        </p>
      )}

      {resultado?.tipo === "erro" && (
        <p role="alert" className="py-6 text-[13px] text-ink-2">
          {resultado.mensagem}
        </p>
      )}

      {resultado?.tipo === "pronto" && (
        <>
          {/*
            Antes da lista, nao depois: quem olha uma lista curta precisa saber
            que ela esta curta **enquanto** a le, e nao ao chegar ao fim.

            So com `status: "ok"`. Com tudo fora do ar a faixa repetiria, em
            tom de rodape, o que o estado vazio ja diz por inteiro logo abaixo.
          */}
          {resultado.status === "ok" && (
            <VeiculosForaDoAr veiculos={resultado.veiculosForaDoAr} />
          )}
          <ListaDeNoticias
            noticias={resultado.noticias}
            status={resultado.status}
          />

          {/*
            A atribuicao mora **na pagina**, e nao no rodape do `Shell`.

            Duas razoes, e as duas sao desta pagina. O rodape do `Shell` so
            aparece com o painel pronto — ou seja, com uma cidade escolhida —, e
            esta e a pagina que nao exige nenhuma: sem cidade, o credito que a
            licenca pede simplesmente nao seria exibido. E o que ele mostra e a
            atribuicao do *painel*, que cita Open-Meteo e GeoNames; esta pagina
            nao le nenhum dos dois.

            Vazia quando nenhum veiculo respondeu — nao ha procedencia a
            creditar —, e ai o `&&` nao renderiza rodape algum.
          */}
          {resultado.attribution && (
            <footer className="text-[11px] text-ink-3">
              {resultado.attribution}
            </footer>
          )}
        </>
      )}
    </section>
  );
}

/**
 * "A", "A e B", "A, B e C" — a enumeracao como se escreve em portugues.
 *
 * `join(" e ")` daria "A e B e C", que se le como erro de programa e nao como
 * frase. Mora aqui, e nao em `formato.ts`, porque e a unica lista de palavras
 * que o app enumera; se uma segunda aparecer, muda de casa.
 */
function enumerar(itens: string[]): string {
  // Lista vazia devolve string vazia, e nao uma frase pela metade. O unico
  // chamador ja a barra antes de chegar aqui, mas uma funcao cujo contrato so
  // vale porque quem chama lembra de checar e uma armadilha para o segundo
  // chamador.
  if (itens.length === 0) return "";
  if (itens.length === 1) return itens[0];
  return `${itens.slice(0, -1).join(", ")} e ${itens[itens.length - 1]}`;
}

/**
 * O aviso de que a lista esta incompleta.
 *
 * **So aparece com `status: "ok"`**, e a condicao e do chamador. Quando todos
 * os feeds caem, quem fala e o estado vazio da lista — que explica o caso com
 * as palavras certas ("nao conseguimos buscar", e nao "nao ha") —, e os dois
 * juntos diriam a mesma coisa duas vezes em dois tons diferentes.
 *
 * Nomeia os veiculos em vez de conta-los: "o Observatorio do Clima nao
 * respondeu" diz a quem le o que esta faltando, e "1 veiculo indisponivel" nao
 * diz nada acionavel.
 */
function VeiculosForaDoAr({ veiculos }: { veiculos: string[] }) {
  if (veiculos.length === 0) return null;

  const verbo = veiculos.length === 1 ? "nao respondeu" : "nao responderam";
  const posse = veiculos.length === 1 ? "dele" : "deles";

  return (
    <p
      role="status"
      className="rounded-inner bg-brand-soft px-3 py-2 text-[12px] text-ink-2"
    >
      {`${enumerar(veiculos)} ${verbo}; as materias ${posse} nao estao nesta lista.`}
    </p>
  );
}

function ListaDeNoticias({
  noticias,
  status,
}: {
  noticias: Noticia[];
  status: StatusDasNoticias;
}) {
  if (noticias.length === 0) {
    return (
      <Painel titulo="Ultimas noticias">
        <div className="flex flex-col items-center justify-center gap-1 py-6 text-center">
          {/*
            Os dois estados vazios dizem coisas **opostas**, e e por isso que
            `status` existe (ADR 0009): um afirma que consultamos e nao ha
            materia nova, o outro que nao conseguimos falar com veiculo nenhum
            — e ali a lista vazia nao afirma nada sobre o mundo. Uma frase so
            para os dois casos mentiria em um deles.
          */}
          {status === "indisponivel" ? (
            <>
              <p className="text-[13px] font-medium">
                Nao foi possivel consultar os veiculos
              </p>
              {/* "veiculos", e nao "feeds": o `CONTEXT.md` proibe *feed* como
                  sinonimo de noticia, e o titulo logo acima ja diz veiculos —
                  duas palavras para a mesma coisa em duas linhas seguidas e o
                  comeco da confusao que o glossario desfaz. */}
              <p className="max-w-prose text-[11px] text-ink-3">
                Nenhum dos tres veiculos respondeu. Isto nao significa que nao
                ha noticias — significa que nao conseguimos busca-las agora.
              </p>
            </>
          ) : (
            <>
              <p className="text-[13px] font-medium">Sem noticias novas</p>
              <p className="text-[11px] text-ink-3">
                Os veiculos responderam, e nao ha materia recente.
              </p>
            </>
          )}
        </div>
      </Painel>
    );
  }

  return (
    <Painel titulo="Ultimas noticias">
      <ul className="flex flex-col">
        {noticias.map((noticia, indice) => (
          <li
            // O indice, e nao o link: a lista nunca e reordenada nem filtrada
            // depois de montada — chega pronta do backend e so se substitui
            // inteira —, entao a posicao e identidade estavel aqui. O link
            // sozinho nao serviria: dois veiculos podem republicar a mesma URL.
            key={indice}
            className="border-b border-line last:border-b-0"
          >
            <a
              href={noticia.link}
              // Abre no site do veiculo, em aba nova: a pessoa estava lendo uma
              // lista e volta para ela. `noreferrer` acompanha `noopener` por
              // higiene, e nao por exigencia do veiculo.
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded-inner px-1 py-3 outline-none transition-colors hover:bg-brand-soft/60 focus-visible:ring-2 focus-visible:ring-brand/40"
            >
              {/* Veiculo e data acima do titulo, nao abaixo: numa lista que
                  mistura tres procedencias, saber quem publicou antes de ler a
                  manchete e o que permite julga-la. */}
              <p className="flex items-center gap-1.5 text-[11px] text-ink-3">
                {/* `brand-text`, e nao `brand`: e texto pequeno sobre cartao,
                    que e exatamente a distincao que o token existe para fazer
                    no tema escuro. */}
                <span className="font-semibold text-brand-text">
                  {noticia.veiculo}
                </span>
                <span aria-hidden="true">·</span>
                <time dateTime={noticia.publicada_em}>
                  {publicadaEm(noticia.publicada_em)}
                </time>
              </p>
              <p className="mt-0.5 text-[13px] font-semibold leading-snug">
                {noticia.titulo}
              </p>
              {noticia.resumo && (
                <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-ink-2">
                  {noticia.resumo}
                </p>
              )}
            </a>
          </li>
        ))}
      </ul>
    </Painel>
  );
}
