/**
 * A rota de layout: barra lateral, cabecalho, busca e a requisicao do painel.
 *
 * A cidade escolhida mora nos parametros da URL, nao em `useState` — ver
 * `docs/adr/0002-cidade-na-url.md`. Duas consequencias visiveis aqui:
 *
 * - navegar entre paginas nao refaz a requisicao, porque os parametros nao
 *   mudam quando so o caminho muda;
 * - recarregar mantem a cidade, e um link colado abre a mesma cidade na mesma
 *   pagina.
 */

import { startTransition, useEffect, useRef, useState } from "react";
import { Outlet, useLocation, useSearchParams } from "react-router";
import { buscarPainel, mensagemDeErro, quemSou, sair } from "../api/client";
import type { Cidade, Conta, WeatherResponse } from "../api/types";
import { cidadeDosParametros, trocarCidade } from "../cidadeNaUrl";
import { descobrirCidadeInicial } from "../cidadeInicial";
import type { ContextoDoOutlet, EstadoDaConta } from "../estadoDaConta";
import type { Estado } from "../estadoDoPainel";
import { dataPorExtenso } from "../formato";
import { ehPaginaSemBusca, ehTelaDeConta } from "../navegacao";
import { lembrar } from "../ultimaCidade";
import { BarraLateral } from "./BarraLateral";
import { Cabecalho } from "./Cabecalho";

/**
 * Onde esta a decisao sobre a cidade inicial.
 *
 * Tres estados, e nao um booleano, por causa do meio: consultar a permissao e
 * ler a ultima cidade e instantaneo, mas **esperar a coordenada leva ate 10 s**.
 * Com um booleano so, esses 10 s seriam de tela em branco; separando
 * `detectando`, eles viram "Carregando o painel…", que e o que de fato esta
 * acontecendo.
 */
type Inicial =
  | { tipo: "decidindo" }
  | { tipo: "detectando" }
  | { tipo: "pronto" };

/**
 * O que a requisicao devolveu, carimbado com a cidade que a originou.
 *
 * A chave junto nao e redundancia: e ela que faz "carregando" ser *derivado* —
 * um resultado de outra cidade significa que esta ainda nao chegou. Sem o
 * carimbo, "carregando" seria estado a parte, e um estado a parte pode
 * discordar da URL.
 */
type Resultado =
  | { chave: string; tipo: "pronto"; painel: WeatherResponse }
  | { chave: string; tipo: "erro"; mensagem: string };

export function Shell() {
  const [parametros, setParametros] = useSearchParams();
  const { pathname } = useLocation();
  const [resultado, setResultado] = useState<Resultado | null>(null);

  /**
   * O estado da conta, consultado **uma vez** ao abrir o app.
   *
   * Mora aqui, na rota de layout, junto do painel, e chega as paginas pelo
   * contexto do outlet — a mesma mecanica que o painel ja usa. Uma consulta
   * so: navegar entre paginas nao a refaz, porque o `Shell` nao desmonta, e o
   * que a mantem em dia depois disso sao `aoEntrar` e `aoSair`, chamados por
   * quem provocou a mudanca.
   */
  const [conta, setConta] = useState<EstadoDaConta>({ tipo: "consultando" });

  useEffect(() => {
    const controller = new AbortController();

    quemSou(controller.signal)
      .then((encontrada) => {
        setConta(
          encontrada === null
            ? { tipo: "visitante" }
            : { tipo: "entrada", conta: encontrada },
        );
      })
      .catch(() => {
        if (controller.signal.aborted) return;
        // Falhar a consulta e ser visitante: e o estado em que as outras sete
        // paginas funcionam inteiras. Ver `EstadoDaConta`, que por isso nao
        // tem caso de erro.
        setConta({ tipo: "visitante" });
      });

    return () => controller.abort();
  }, []);

  /** Guarda a conta que o cadastro ou a entrada acabou de abrir. */
  function aoEntrar(aberta: Conta) {
    setConta({ tipo: "entrada", conta: aberta });
  }

  /**
   * Sai: apaga a sessao no servidor e volta ao estado de visitante.
   *
   * O estado local vira `visitante` **sem esperar** a resposta, e a falha da
   * requisicao nao o desfaz. Quem clicou em sair quer estar fora, e o pior
   * resultado possivel e a tela continuar dizendo que ha uma sessao. A linha
   * no banco e o que importa de verdade, e `/api/saida` responde `200` ate
   * quando nao ha o que apagar — a chamada que falha por rede deixa uma sessao
   * viva no servidor, que expira sozinha.
   */
  function aoSair() {
    setConta({ tipo: "visitante" });
    void sair().catch(() => {});
  }

  const cidade = cidadeDosParametros(parametros);

  // So ha o que decidir quando a URL chega sem cidade. Com cidade, ela manda —
  // um link colado nao deve ser sobrescrito pela localizacao de quem o abriu.
  const [inicial, setInicial] = useState<Inicial>(() =>
    cidade ? { tipo: "pronto" } : { tipo: "decidindo" },
  );
  const jaDecidiu = useRef(false);

  /**
   * A cidade do ultimo render, para a deteccao consultar quando terminar.
   *
   * Um ref e nao a variavel porque o `.then` la embaixo fecha sobre o render em
   * que o efeito rodou, e entre aquele render e a coordenada chegando cabem
   * ate 10 s — tempo de sobra para a URL ter mudado.
   *
   * Sincronizado em efeito, e nao durante o render, que seria escrita em ref no
   * meio da renderizacao. A deteccao so le isto depois de uma volta pela rede,
   * muito depois de qualquer efeito ter rodado.
   */
  const cidadeAgora = useRef(cidade);
  useEffect(() => {
    cidadeAgora.current = cidade;
  });

  useEffect(() => {
    if (jaDecidiu.current || inicial.tipo === "pronto") return;
    // Uma vez por carregamento: pedir a posicao do aparelho e acao, nao
    // sincronizacao, e o `StrictMode` roda todo efeito duas vezes em
    // desenvolvimento. Sem funcao de limpeza de proposito — cancelar a primeira
    // execucao deixaria a decisao pendurada para sempre, porque a segunda para
    // aqui.
    jaDecidiu.current = true;

    descobrirCidadeInicial(() => setInicial({ tipo: "detectando" })).then(
      (encontrada) => {
        // A deteccao perde para qualquer cidade que tenha chegado a URL
        // enquanto ela esperava. A busca fica viva durante os ate 10 s do GPS,
        // entao escolher uma cidade nessa janela e comum — e sem esta guarda a
        // coordenada chegava depois e desfazia a escolha, com `replace`, sem
        // nem deixar o Voltar recuperar. E a mesma regra que ja valia para um
        // link colado, so que aplicada tambem ao que chega durante a espera:
        // cidade na URL manda, venha de onde vier.
        if (!encontrada || cidadeAgora.current) {
          setInicial({ tipo: "pronto" });
          return;
        }
        // Os dois updates **precisam cair no mesmo render**, e e so por isso
        // que ha um `startTransition` aqui.
        //
        // O React Router aplica a navegacao como transicao. Um
        // `setInicial` solto seria update urgente e passaria na frente: haveria
        // um quadro com a decisao ja tomada e os parametros ainda vazios, que e
        // exatamente a combinacao que `estado` le como `vazio`. Resultado
        // observado antes desta linha existir: "Busque uma cidade" piscando
        // sobre a URL que ja tinha a cidade — o quadro que `decidindo` existe
        // para impedir. Na mesma transicao, os dois chegam juntos.
        //
        // `replace`: sem ele, entrar no app ja deixaria a pessoa a um clique de
        // Voltar de sair dele.
        startTransition(() => {
          setParametros(encontrada, { replace: true });
          setInicial({ tipo: "pronto" });
        });
      },
    );
  }, [inicial.tipo, setParametros]);

  // A dependencia do efeito e o texto dos parametros, e nao o objeto da
  // cidade: uma cidade reconstruida a cada render nunca seria igual a anterior
  // e o efeito entraria em laco. O texto tambem e o que da a propriedade que
  // interessa — trocar de pagina mantendo a cidade nao o altera, e nenhuma
  // requisicao e refeita.
  const chave = parametros.toString();

  useEffect(() => {
    const alvo = cidadeDosParametros(new URLSearchParams(chave));
    // Sem cidade na URL e o estado inicial, nao erro: ninguem buscou ainda.
    if (!alvo) return;

    const controller = new AbortController();

    buscarPainel(alvo, controller.signal)
      .then((painel) => {
        setResultado({ chave, tipo: "pronto", painel });
        // Guardada so quando o painel de fato carregou: uma cidade que falhou
        // reabriria no erro na proxima visita.
        lembrar(new URLSearchParams(chave));
      })
      .catch((falha: unknown) => {
        if (controller.signal.aborted) return;
        setResultado({
          chave,
          tipo: "erro",
          mensagem: mensagemDeErro(falha, "Nao foi possivel carregar o painel."),
        });
      });

    return () => controller.abort();
  }, [chave]);

  // "Carregando" e derivado, nunca atribuido: ha cidade na URL e o resultado
  // que temos e de outra. Quem dispara a carga nao e so o clique — o botao
  // Voltar e um link colado trocam a URL sem clique algum —, e derivar e o que
  // garante que os tres caminhos concordem.
  const estado: Estado = cidade
    ? resultado?.chave !== chave
      ? { tipo: "carregando" }
      : resultado.tipo === "pronto"
        ? { tipo: "pronto", painel: resultado.painel }
        : { tipo: "erro", mensagem: resultado.mensagem }
    : // Detectar ja e carregar: ha cidade a caminho, so nao se sabe qual.
      inicial.tipo === "detectando"
      ? { tipo: "carregando" }
      : inicial.tipo === "decidindo"
        ? { tipo: "decidindo" }
        : { tipo: "vazio" };

  /** Escolher uma cidade e trocar a URL; o efeito acima faz o resto. */
  function escolher(escolhida: Cidade) {
    // `setSearchParams` preserva o caminho: buscar em /vizinhas continua em
    // /vizinhas, com a cidade nova.
    //
    // `trocarCidade` preserva os **parametros** que nao sao da cidade, pelo
    // mesmo motivo: quem escolheu "6 meses" na Tendencia e busca outra cidade
    // quer as duas no mesmo periodo. Um conjunto novo de parametros apagaria a
    // janela junto com a cidade antiga.
    setParametros(trocarCidade(parametros, escolhida));
  }

  // A data e a de hoje **na cidade consultada**, e por isso so existe depois
  // que uma cidade carrega.
  const data =
    estado.tipo === "pronto"
      ? dataPorExtenso(estado.painel.current.observed_at)
      : null;

  return (
    <div className="min-h-screen">
      <div className="mx-auto grid max-w-[1180px] grid-cols-[64px_1fr] gap-4 px-6 py-8">
        <BarraLateral conta={conta} aoSair={aoSair} />

        {/* `min-w-0`: sem isso a coluna de conteudo cresce ate caber o seu
            maior filho — o grafico da tendencia — e estoura o container. */}
        <div className="flex min-w-0 flex-col gap-4">
          <Cabecalho
            conta={conta}
            data={data}
            // As telas de conta se juntam a Ajustes e a Noticias na lista das
            // que nao sao sobre uma cidade: buscar uma cidade de dentro do
            // formulario de cadastro trocaria a URL sob um formulario ja
            // preenchido, e na Noticias nao mudaria nada na tela.
            mostrarBusca={
              !ehPaginaSemBusca(pathname) && !ehTelaDeConta(pathname)
            }
            nomeDaCidade={
              estado.tipo === "pronto" ? estado.painel.location.name : null
            }
            onEscolher={escolher}
          />

          <main className="min-w-0">
            <Outlet
              context={
                { estado, conta, aoEntrar } satisfies ContextoDoOutlet
              }
            />
          </main>

          {estado.tipo === "pronto" && (
            <footer className="mt-2 text-[11px] text-ink-3">
              {estado.painel.attribution}
            </footer>
          )}
        </div>
      </div>
    </div>
  );
}
