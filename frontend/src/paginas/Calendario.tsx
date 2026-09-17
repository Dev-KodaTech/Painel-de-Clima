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
 * ## A pagina e mista, e e a primeira do app
 *
 * A grade e a aptidao sao funcao da **cidade** e viajam na URL: qualquer pessoa
 * que abra o link ve o mesmo. A faixa de planos e funcao da **conta**, e so o
 * dono a ve. Nenhuma outra pagina mistura as duas — Locais salvos, que seria a
 * primeira por conta, e inteira da conta (verbete *Pagina* do `CONTEXT.md`).
 *
 * Duas regras saem disso, e as duas moram neste arquivo:
 *
 * 1. **A pagina nao exige conta para nada alem dos planos.** Sem conta, a
 *    requisicao do horizonte acontece igual, a grade se pinta igual, e so a
 *    faixa vira convite.
 * 2. **Trocar de cidade nao mexe nos planos — mas mexe na aptidao ao lado
 *    deles.** Os planos sao da conta; o julgamento e da cidade. Ver
 *    `cruzarPlanos`, onde a consequencia esta registrada por extenso, e o
 *    efeito no `useEffect` que **nao** depende da cidade.
 */

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import {
  apagarPlano,
  buscarHorizonte,
  buscarPlanos,
  criarPlano,
  mensagemDeErro,
} from "../api/client";
import type { Atividade, DiaDoHorizonte, Plano } from "../api/types";
import { atividadeDosParametros, comAtividade } from "../atividadeNaUrl";
import { cidadeDosParametros } from "../cidadeNaUrl";
import { julgamentoDe } from "../components/calendario/aptidao";
import { CriarPlano } from "../components/calendario/CriarPlano";
import { DetalheDoDia } from "../components/calendario/DetalheDoDia";
import { FaixaDePlanos } from "../components/calendario/FaixaDePlanos";
import { Grade } from "../components/calendario/Grade";
import { cruzarPlanos, diasComPlano } from "../components/calendario/planos";
import { SeletorDeAtividade } from "../components/calendario/SeletorDeAtividade";
import { Painel } from "../components/Painel";
import { useConta } from "../estadoDaConta";
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
  const { conta } = useConta();
  const [parametros, setParametros] = useSearchParams();
  const [resultado, setResultado] = useState<Resultado | null>(null);
  /**
   * Os planos da conta, ou `null` enquanto nao se sabe.
   *
   * `null` **nao** e lista vazia, e a faixa diz coisas diferentes nos dois:
   * um e "carregando", o outro e "crie o seu primeiro". Colapsa-los mostraria
   * a mensagem de conta nova a quem tem doze planos e uma conexao lenta.
   */
  const [planos, setPlanos] = useState<Plano[] | null>(null);
  const [erroDosPlanos, setErroDosPlanos] = useState<string | null>(null);
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

  const temConta = conta.tipo === "entrada";
  /**
   * **Quem** e o dono, e nao so se ha um.
   *
   * E a dependencia do efeito dos planos, e um booleano nao serviria: trocar de
   * conta sem passar por "sem conta" no meio deixaria `temConta` valendo
   * `true` nos dois lados, o efeito nao reexecutaria e a faixa mostraria os
   * planos da conta anterior. Hoje isso nao acontece — entrar passa pela pagina
   * `/entrada` e esta desmonta —, mas a lista e de outra pessoa, e a correcao
   * nao pode depender de por onde a navegacao passou.
   */
  const dono = conta.tipo === "entrada" ? conta.conta.email : null;

  /**
   * A lista de planos — **independente da cidade, de proposito**.
   *
   * As dependencias sao a conta e nada mais. E a consequencia menos obvia de a
   * pagina ser mista, e ela e visivel exatamente aqui: trocar de cidade
   * **nao** recarrega os planos, porque eles nao sao da cidade. O que muda ao
   * trocar e a aptidao exibida ao lado deles, e essa sai do horizonte novo
   * pelo `cruzarPlanos` mais abaixo — sem tocar nesta lista.
   *
   * Por `chave` nas dependencias seria o erro natural, e ele custaria uma
   * requisicao por troca de cidade para receber de volta exatamente a mesma
   * lista.
   */
  useEffect(() => {
    if (dono === null) return;

    const controller = new AbortController();

    buscarPlanos(controller.signal)
      .then((lista) => {
        setPlanos(lista);
        setErroDosPlanos(null);
      })
      .catch((falha: unknown) => {
        if (controller.signal.aborted) return;
        setErroDosPlanos(
          mensagemDeErro(falha, "Nao foi possivel carregar seus planos."),
        );
      });

    return () => controller.abort();
  }, [dono]);

  /**
   * Apaga o plano e tira-o da lista.
   *
   * A lista local e corrigida a partir do `id`, e nao rebuscada: o backend
   * respondeu `204` e nao tem mais nada a dizer, e uma segunda requisicao
   * traria a mesma lista menos uma linha. O `404` de plano que nao existe mais
   * cai no mesmo caminho de erro — e nele a lista **nao** e alterada, porque
   * nao se sabe o que aconteceu do outro lado.
   */
  const aoApagar = useCallback(async (plano: Plano) => {
    try {
      await apagarPlano(plano.id);
      setPlanos((atuais) =>
        atuais === null ? atuais : atuais.filter((p) => p.id !== plano.id),
      );
      setErroDosPlanos(null);
    } catch (falha: unknown) {
      setErroDosPlanos(
        mensagemDeErro(falha, "Nao foi possivel apagar o plano."),
      );
    }
  }, []);

  /**
   * Cria o plano e o poe na lista, **na posicao certa**.
   *
   * Reordenar aqui repete a regra do backend (`ORDER BY dia, id`), e e a
   * escolha menos ruim entre as tres: rebuscar a lista custa uma requisicao
   * para saber algo que ja se sabe; empilhar no fim deixaria o plano recem
   * criado fora de ordem ate a proxima visita, e quem acabou de cria-lo e
   * exatamente quem vai procura-lo.
   *
   * O criterio e o mesmo do repositorio — dia, e `id` para desempatar — e foi
   * escrito olhando para ele: o `RepositorioEmMemoria` tambem ordena por
   * `(dia, id)` explicito, pela mesma razao de nao depender da ordem de
   * insercao.
   */
  const aoCriar = useCallback(
    async (titulo: string, dia: string, atividade: Atividade) => {
      const criado = await criarPlano(titulo, dia, atividade);
      setPlanos((atuais) =>
        [...(atuais ?? []), criado].sort(
          (um, outro) =>
            um.dia.localeCompare(outro.dia) || um.id - outro.id,
        ),
      );
      return criado;
    },
    [],
  );

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

  /**
   * Hoje **na cidade consultada**: o primeiro dia da grade.
   *
   * `null` enquanto a grade nao chegou, e nao `new Date()`. E o que decide
   * quais planos ja passaram (ADR 0012), e lido do relogio do browser quem
   * esta em Sao Paulo consultando Toquio agruparia um plano pelo fuso errado.
   * Sem grade, nenhum plano e classificado como passado — que e o estado certo:
   * sem saber que dia e la, agrupar seria chutar.
   */
  const hoje = dias[0]?.date ?? null;

  /**
   * A lista que a faixa de fato usa — vazia para quem nao tem conta.
   *
   * Derivada no render, e nao zerada por um efeito ao sair. Sem conta nao ha
   * planos a mostrar, e essa e uma funcao do estado da conta, nao um estado a
   * manter em sincronia: quem sai ve o convite no mesmo render, sem um quadro
   * intermediario em que a lista antiga ainda esta na tela.
   *
   * E o que impede o vazamento entre contas: sair e entrar com outra conta nao
   * tem como exibir os planos da primeira, porque a lista guardada so e lida
   * enquanto `temConta` vale.
   */
  const daConta = temConta ? planos : null;

  /**
   * Os planos cruzados com a grade corrente.
   *
   * Derivado a cada render, e nao guardado em estado: as duas metades ja moram
   * em `planos` e `dias`, e uma terceira copia teria de ser invalidada nas duas
   * ocasioes em que qualquer uma muda — trocar de cidade e criar ou apagar um
   * plano. E o cruzamento e um `find` sobre dezesseis itens.
   */
  const cruzados = daConta === null ? null : cruzarPlanos(daConta, dias, hoje);

  const marcados = diasComPlano(daConta ?? []);

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

          {/*
            A grade e a faixa, lado a lado — e empilhadas em tela estreita.

            `lg:` e nao `sm:`: a grade tem sete colunas de conteudo real (data,
            ceu, maxima, minima, palavra da aptidao), e espreme-la numa metade
            de tablet quebraria a celula antes de a faixa ganhar largura util.
            Ate la as duas ocupam a linha inteira, uma sob a outra — a grade
            primeiro, porque e o que a pagina promete a quem chega, e porque e
            a metade que funciona sem conta.

            A faixa tem largura fixa na coluna da direita (`lg:w-80`) e a grade
            fica com o resto: sao dezesseis celulas que ganham em ter espaco, e
            uma lista de titulos curtos que nao ganha nada em passar de ~320 px.
          */}
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start">
            <Painel titulo="Proximos dezesseis dias" className="min-w-0 flex-1">
              <Grade
                dias={resultado.dias}
                units={units}
                atividade={atividade}
                diasComPlano={marcados}
                onAbrirDia={(dia) => setDiaAberto(dia.date)}
              />
            </Painel>

            <div className="lg:w-80 lg:shrink-0">
              <FaixaDePlanos
                cruzados={cruzados}
                consultandoConta={conta.tipo === "consultando"}
                temConta={temConta}
                erro={erroDosPlanos}
                rotulos={rotulos}
                onApagar={aoApagar}
              />
            </div>
          </div>

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
        >
          {/*
            O formulario so existe com conta — e o detalhe do dia continua
            abrindo inteiro sem ela, com a previsao e as quatro aptidoes. E a
            regra da pagina mista: conta so para os planos.

            `rotulos.length > 0` porque o formulario precisa das quatro
            atividades, que vem do backend junto da aptidao. Num dia do
            horizonte longo os rotulos vem da grade (qualquer dia curto serve),
            entao criar plano para dezembro continua possivel — planejar longe e
            legitimo, julgar longe e que nao.
          */}
          {temConta && rotulos.length > 0 && (
            <CriarPlano
              dia={aberto.date}
              rotulos={rotulos}
              atividadeInicial={atividade}
              onCriar={aoCriar}
              onCriado={() => setDiaAberto(null)}
            />
          )}
        </DetalheDoDia>
      )}
    </section>
  );
}
