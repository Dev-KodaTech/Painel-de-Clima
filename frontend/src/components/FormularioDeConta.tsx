/**
 * O formulario das duas telas de conta: cadastro e entrada.
 *
 * Um componente para os dois porque a diferenca entre eles cabe em props — o
 * titulo, o rotulo do botao, os requisitos da senha e qual funcao do cliente
 * chamar. O que *nao* cabe em props e o que eles tem em comum, e e justamente
 * o que e facil de errar duas vezes: o envio que nao dispara duas vezes, o
 * `aria-describedby` do campo com erro, o foco que vai para a mensagem.
 *
 * Nao ha biblioteca de formulario no projeto e esta entrega nao introduz uma
 * (spec). Sao dois campos e um botao; o estado deles e `useState`.
 */

import { useId, useState } from "react";
import { EmailJaUsado, ErroDeRede, mensagemDeErro } from "../api/client";
import type { Conta } from "../api/types";

/**
 * O minimo da senha, **espelhado** de `backend/app/services/conta.py`.
 *
 * Duplicado de proposito, e nao buscado num endpoint: uma requisicao para
 * descobrir o numero 8 atrasaria a tela por um valor que muda de ano em ano.
 * O preco e concordar com o backend — e o backend continua sendo quem recusa,
 * entao a divergencia vira uma mensagem estranha, nunca uma senha fraca
 * aceita.
 */
const MINIMO_DA_SENHA = 8;

/** Os requisitos, ditos **antes** do envio. Ver `Props.requisitos`. */
export const REQUISITOS_DA_SENHA = `Ao menos ${MINIMO_DA_SENHA} caracteres.`;

/**
 * O envio em curso, ou o que sobrou do ultimo.
 *
 * Um estado so, e nao um booleano `enviando` ao lado de uma `mensagem`: a
 * combinacao "enviando com erro na tela" existiria com dois, e e a que faz a
 * mensagem antiga ficar sob o botao ja clicado de novo. Aqui, enviar apaga o
 * erro porque `enviando` nao tem onde guardar um.
 */
type Envio =
  | { tipo: "parado" }
  | { tipo: "enviando" }
  /**
   * `culpado` diz **o que** falhou, e e o que decide quais campos aparecem
   * como invalidos. Nao muda a frase — quem a escreve e o backend, via
   * cliente —, muda para onde a tela aponta:
   *
   * - `credenciais`: o par esta errado, e nao se pode dizer qual metade (e o
   *   ponto da recusa unica). Os dois campos ficam invalidos.
   * - `email`: so o e-mail, que ja tem conta. A senha nao tem defeito, e
   *   marca-la mandaria procurar um erro que nao existe.
   * - `rede`: a requisicao nem chegou. Campo nenhum esta errado — os dados
   *   podem estar certos —, entao nenhum e marcado.
   */
  | { tipo: "erro"; mensagem: string; culpado: "credenciais" | "email" | "rede" };

type Props = {
  titulo: string;
  /** Uma frase sobre o que esta tela faz, sob o titulo. */
  subtitulo: string;
  /** O rotulo do botao: "Criar conta", "Entrar". */
  acao: string;
  /**
   * Os requisitos da senha, ou `null` na entrada.
   *
   * `null` na entrada de proposito: quem ja tem conta nao precisa saber a
   * regra — a senha dele ja passou por ela —, e repeti-la ali sugeriria que a
   * senha antiga pode ter deixado de servir.
   */
  requisitos: string | null;
  /** O que o campo de senha anuncia ao gerenciador de senhas do browser. */
  autocompletarSenha: "new-password" | "current-password";
  aoEnviar: (email: string, senha: string) => Promise<Conta>;
  aoConseguir: (conta: Conta) => void;
  /** O rodape com o caminho para a outra tela. */
  children: React.ReactNode;
};

export function FormularioDeConta({
  titulo,
  subtitulo,
  acao,
  requisitos,
  autocompletarSenha,
  aoEnviar,
  aoConseguir,
  children,
}: Props) {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [envio, setEnvio] = useState<Envio>({ tipo: "parado" });

  const idDoEmail = useId();
  const idDaSenha = useId();
  const idDoErro = useId();
  const idDosRequisitos = useId();

  const enviando = envio.tipo === "enviando";

  async function submeter(evento: React.FormEvent) {
    evento.preventDefault();
    // A guarda que impede o envio duplo, **alem** do `disabled` do botao: o
    // `disabled` some do botao um render depois do clique, e um `Enter`
    // repetido no campo submete o formulario sem passar pelo botao.
    if (enviando) return;

    setEnvio({ tipo: "enviando" });

    try {
      const conta = await aoEnviar(email, senha);
      // Sem `setEnvio` de volta para "parado": conseguir desmonta esta tela,
      // e um `setState` depois disso e trabalho para um componente que ja
      // saiu.
      aoConseguir(conta);
    } catch (falha: unknown) {
      setEnvio({
        tipo: "erro",
        mensagem: mensagemDeErro(falha, "Nao foi possivel concluir."),
        culpado:
          falha instanceof ErroDeRede
            ? "rede"
            : falha instanceof EmailJaUsado
              ? "email"
              : "credenciais",
      });
    }
  }

  /**
   * Quais campos aparecem como invalidos. Ver `Envio`.
   *
   * Numa falha de rede, nenhum: os campos nao tem defeito, e marca-los mandaria
   * quem usa leitor de tela procurar um erro de digitacao que nao existe.
   */
  const emailRecusado =
    envio.tipo === "erro" && (envio.culpado === "credenciais" || envio.culpado === "email");
  const senhaRecusada = envio.tipo === "erro" && envio.culpado === "credenciais";

  return (
    <section className="mx-auto w-full max-w-sm py-6">
      <h2 className="text-lg font-semibold">{titulo}</h2>
      <p className="mt-1 text-[13px] text-ink-2">{subtitulo}</p>

      <form onSubmit={submeter} className="mt-5 flex flex-col gap-4" noValidate>
        <div className="flex flex-col gap-1.5">
          <label htmlFor={idDoEmail} className="text-[12px] font-medium">
            E-mail
          </label>
          <input
            id={idDoEmail}
            type="email"
            value={email}
            onChange={(evento) => setEmail(evento.target.value)}
            autoComplete="email"
            required
            aria-invalid={emailRecusado || undefined}
            aria-describedby={envio.tipo === "erro" ? idDoErro : undefined}
            className="rounded-inner bg-card px-4 py-2.5 text-[13px] shadow-card outline-none placeholder:text-ink-3 focus:ring-2 focus:ring-brand/40"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor={idDaSenha} className="text-[12px] font-medium">
            Senha
          </label>
          <input
            id={idDaSenha}
            type="password"
            value={senha}
            onChange={(evento) => setSenha(evento.target.value)}
            autoComplete={autocompletarSenha}
            required
            aria-invalid={senhaRecusada || undefined}
            // Os requisitos entram no `describedby` junto com o erro: quem usa
            // leitor de tela os ouve ao chegar no campo, que e o "antes do
            // envio" que o ticket pede — nao so quem enxerga o texto cinza.
            aria-describedby={
              [requisitos ? idDosRequisitos : null, envio.tipo === "erro" ? idDoErro : null]
                .filter(Boolean)
                .join(" ") || undefined
            }
            className="rounded-inner bg-card px-4 py-2.5 text-[13px] shadow-card outline-none placeholder:text-ink-3 focus:ring-2 focus:ring-brand/40"
          />
          {requisitos && (
            <p id={idDosRequisitos} className="text-[11px] text-ink-2">
              {requisitos}
            </p>
          )}
        </div>

        {/*
          `role="alert"` e nao `status`: uma credencial recusada e o resultado
          de uma acao que a pessoa acabou de tomar, e interrompe a leitura de
          proposito. O elemento so existe quando ha erro, que e o que faz o
          leitor de tela anuncia-lo ao aparecer.
        */}
        {envio.tipo === "erro" && (
          <p id={idDoErro} role="alert" className="text-[12px] text-ink">
            {envio.mensagem}
          </p>
        )}

        <button
          type="submit"
          disabled={enviando}
          // `aria-busy` diz o que o rotulo tambem diz, para quem nao le o
          // rotulo trocado.
          aria-busy={enviando}
          className="mt-1 rounded-inner bg-brand px-4 py-2.5 text-[13px] font-medium text-white outline-none transition-opacity hover:opacity-90 focus-visible:ring-2 focus-visible:ring-brand/40 disabled:opacity-60"
        >
          {enviando ? "Enviando…" : acao}
        </button>
      </form>

      <p className="mt-5 text-[12px] text-ink-2">{children}</p>
    </section>
  );
}
