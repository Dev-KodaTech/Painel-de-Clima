/**
 * A tela de entrada.
 *
 * Gemea do cadastro, com tres diferencas que sao todas props: nao anuncia os
 * requisitos da senha — quem ja tem conta ja passou por eles, e repeti-los
 * sugeriria que a senha antiga deixou de servir —, pede
 * `autocomplete="current-password"` ao gerenciador do browser, e o rodape leva
 * para o cadastro em vez de vir dele.
 *
 * A mensagem de credencial recusada e a do backend, e **nao diz se o e-mail
 * existe**: a mesma frase para senha errada e para conta inexistente e o que
 * impede descobrir contas por tentativa. O frontend nao a reescreve.
 */

import { Link, useNavigate } from "react-router";
import { entrar } from "../api/client";
import type { Conta } from "../api/types";
import { FormularioDeConta } from "../components/FormularioDeConta";
import { useConta } from "../estadoDaConta";
import { CAMINHO_CADASTRO, useComCidade } from "../navegacao";

export function Entrada() {
  const { aoEntrar } = useConta();
  const navegar = useNavigate();
  const comCidade = useComCidade();
  const paraCadastro = comCidade(CAMINHO_CADASTRO);
  const paraInicio = comCidade("/");

  function conseguiu(conta: Conta) {
    aoEntrar(conta);
    // `replace`, como no cadastro: o Voltar nao deve reabrir o formulario de
    // quem acabou de entrar por ele.
    navegar(paraInicio, { replace: true });
  }

  return (
    <FormularioDeConta
      titulo="Entrar"
      subtitulo="Entre para reencontrar seus locais salvos."
      acao="Entrar"
      requisitos={null}
      autocompletarSenha="current-password"
      aoEnviar={entrar}
      aoConseguir={conseguiu}
    >
      Ainda nao tem conta?{" "}
      <Link
        to={paraCadastro}
        className="text-brand-text underline underline-offset-2"
      >
        Criar conta
      </Link>
      .
    </FormularioDeConta>
  );
}
