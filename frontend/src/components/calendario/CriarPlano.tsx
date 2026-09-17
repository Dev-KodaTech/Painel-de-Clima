/**
 * Criar um plano, de dentro do detalhe do dia.
 *
 * ## Por que aqui, e nao num botao proprio na faixa
 *
 * **O dia vem do dia clicado — nao se digita.** Um formulario na faixa
 * precisaria de um campo de data, e um campo de data numa pagina que ja e uma
 * grade de dezesseis dias clicaveis seria a segunda maneira de dizer a mesma
 * coisa, com a diferenca de que a segunda aceita "31 de fevereiro". Clicar na
 * quinta e escolher a quinta; nao ha o que validar.
 *
 * ## Sem campo de hora, e isto e regra de dominio
 *
 * Um plano nao tem hora, e o tipo do backend (`Date`, nao `DateTime`) e a rede
 * que o garante. **Quem for acrescentar um campo de hora aqui precisa reabrir o
 * verbete *Plano* do `CONTEXT.md` e o ADR 0010 antes** — nao e uma melhoria de
 * formulario: a aptidao e diaria e o horizonte longo nao tem dado horario, e um
 * campo de hora prometeria uma precisao que o dado nao tem. E o mesmo erro que
 * a fronteira do dia 8 existe para nao cometer.
 *
 * ## A atividade entra pre-escolhida
 *
 * Quem esta olhando a grade pintada por "lavar roupa" e clica numa quinta
 * provavelmente quer um plano de lavar roupa. A atividade da URL entra
 * selecionada, e continua trocavel — e um palpite com boa taxa de acerto, nao
 * uma decisao tomada pela pessoa.
 *
 * Sem atividade escolhida na grade, nenhuma vem marcada: eleger uma das quatro
 * ali seria inventar uma intencao que ninguem manifestou, do mesmo modo que a
 * pagina nao elege uma atividade padrao para pintar a grade.
 */

import { useState } from "react";
import { Link } from "react-router";
import { SessaoExpirada, mensagemDeErro } from "../../api/client";
import type { Atividade, JulgamentoDeAptidao, Plano } from "../../api/types";
import { CAMINHO_ENTRADA, useComCidade } from "../../navegacao";
import { GrupoDeRadio } from "../GrupoDeRadio";

/**
 * O teto do titulo. **Copia deliberada** do backend, e nao um valor proprio.
 *
 * O mesmo 200 esta na coluna (`schema.py`, `String(200)`) e na rota
 * (`routers/planos.py`, `MAXIMO_DO_TITULO`). Tres lugares com o mesmo numero e
 * exatamente o que `rotuloDaAtividade` se recusa a fazer com os nomes das
 * atividades, entao vale dizer por que ali a duplicacao e erro e aqui nao:
 *
 * **O rotulo o backend manda; este numero ele nao manda.** Nenhuma resposta da
 * API carrega o limite de caracteres — nao ha campo de onde le-lo —, e as
 * alternativas para nao escreve-lo aqui seriam inventar um endpoint de
 * configuracao ou deixar o campo sem `maxLength`. A segunda troca um aviso
 * imediato ("nao cabe mais") por um `422` depois do envio, que e pior
 * justamente no formulario em que perder o que se digitou e o risco que esta
 * fatia existe para cobrir.
 *
 * O acoplamento e real e o modo de falha e brando: com este numero **maior**
 * que o do backend, o campo aceitaria texto que a rota recusa — e a recusa ja
 * tem caminho tratado, com o titulo preservado. Diminui-lo no backend sem
 * mexer aqui nao perde dado, so mostra o erro mais tarde do que poderia.
 */
const MAXIMO_DO_TITULO = 200;

type Props = {
  /** O dia clicado. Vem da grade, e nao de um campo. */
  dia: string;
  /** Os rotulos das quatro atividades, do backend. */
  rotulos: JulgamentoDeAptidao[];
  /** A atividade da URL, que entra pre-escolhida. */
  atividadeInicial: Atividade | null;
  /**
   * Cria o plano. Rejeita com o erro do cliente, que este componente traduz.
   *
   * A pagina e quem chama a API, e nao este componente: e ela que guarda a
   * lista e precisa redesenha-la, e um `fetch` daqui deixaria os dois com
   * copias do mesmo estado.
   */
  onCriar: (titulo: string, dia: string, atividade: Atividade) => Promise<Plano>;
  /** Fecha o formulario depois de criar. */
  onCriado: () => void;
};

export function CriarPlano({
  dia,
  rotulos,
  atividadeInicial,
  onCriar,
  onCriado,
}: Props) {
  const [titulo, setTitulo] = useState("");
  const [atividade, setAtividade] = useState<Atividade | null>(atividadeInicial);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  /**
   * Se a recusa foi de sessao, e nao uma falha qualquer.
   *
   * **Guardado a parte da mensagem** porque muda o que se oferece: uma falha
   * comum pede "tente de novo", e esta pede "entre de novo" — tentar outra vez
   * com a mesma sessao morta falha igual. Ver `SessaoExpirada`.
   */
  const [sessaoMorreu, setSessaoMorreu] = useState(false);
  const comCidade = useComCidade();

  const aparado = titulo.trim();
  const podeEnviar = aparado.length > 0 && atividade !== null && !enviando;

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (!podeEnviar || atividade === null) return;

    setEnviando(true);
    setErro(null);
    setSessaoMorreu(false);

    try {
      await onCriar(aparado, dia, atividade);
      onCriado();
    } catch (falha: unknown) {
      /*
        **O que foi digitado nao e apagado em nenhum caminho de falha.**

        E o requisito da issue e o caminho novo que a spec registra como risco:
        todo o resto do app e leitura publica ou formulario de conta, e nos dois
        a recusa acontece antes de haver texto a preservar. Aqui ha — e o
        `setTitulo("")` mora **so** no caminho de sucesso, logo abaixo, por isso.

        Quem escreveu "lavar as cortinas da sala" e viu a sessao vencer entra de
        novo, volta, e a frase continua no campo.
      */
      setSessaoMorreu(falha instanceof SessaoExpirada);
      setErro(
        mensagemDeErro(falha, "Nao foi possivel criar o plano. Tente de novo."),
      );
      setEnviando(false);
      return;
    }

    // So aqui o campo se limpa: o plano existe, e o proximo que a pessoa criar
    // e outro.
    setTitulo("");
    setEnviando(false);
  }

  return (
    <form onSubmit={enviar} className="flex flex-col gap-2.5">
      <h4 className="text-[12px] font-semibold text-ink-2">
        Criar um plano para este dia
      </h4>

      <label className="flex flex-col gap-1">
        <span className="text-[11px] text-ink-2">O que voce pretende fazer</span>
        <input
          type="text"
          value={titulo}
          onChange={(evento) => setTitulo(evento.target.value)}
          maxLength={MAXIMO_DO_TITULO}
          placeholder="Lavar as cortinas"
          // `aria-invalid` so depois de uma recusa: marca-lo enquanto o campo
          // esta vazio de proposito anunciaria erro a quem ainda nao digitou.
          aria-invalid={erro !== null ? true : undefined}
          className="rounded-inner border border-line bg-card px-2.5 py-1.5 text-[13px] outline-none focus:ring-2 focus:ring-brand/40"
        />
      </label>

      {/* As quatro atividades, sem a opcao "Nenhuma" que o seletor da grade
          tem: ali ela e o estado inicial da pagina, aqui um plano **precisa**
          de atividade — e a regra do backend, e sem ela nao haveria criterio
          para julgar o dia. */}
      <div className="flex flex-col gap-1">
        <span className="text-[11px] text-ink-2">Atividade</span>
        <GrupoDeRadio<Atividade | null>
          rotulo="Atividade do plano"
          opcoes={rotulos.map((julgamento) => ({
            valor: julgamento.atividade,
            rotulo: julgamento.rotulo,
          }))}
          escolhida={atividade}
          onEscolher={setAtividade}
        />
      </div>

      {erro && (
        <div role="alert" className="flex flex-col gap-1">
          <p className="text-[11px] text-ink-2">{erro}</p>
          {sessaoMorreu && (
            <p className="text-[11px] text-ink-2">
              {/* A frase promete o que o codigo cumpre: o titulo continua no
                  campo. Sem ela, quem ve "Entre para continuar" fecha a pagina
                  supondo que perdeu o que escreveu. */}
              O que voce escreveu continua aqui.{" "}
              <Link
                to={comCidade(CAMINHO_ENTRADA)}
                className="font-medium text-brand underline underline-offset-2 outline-none focus-visible:ring-2 focus-visible:ring-brand/40"
              >
                Entrar de novo
              </Link>
            </p>
          )}
        </div>
      )}

      <button
        type="submit"
        disabled={!podeEnviar}
        className="self-start rounded-full bg-brand px-3.5 py-1.5 text-[12px] font-medium text-white outline-none transition-opacity hover:opacity-90 focus-visible:ring-2 focus-visible:ring-brand/40 disabled:opacity-40"
      >
        {enviando ? "Criando…" : "Criar plano"}
      </button>
    </form>
  );
}
