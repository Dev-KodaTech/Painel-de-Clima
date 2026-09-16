/**
 * A tela de cadastro.
 *
 * **Cadastrar entra**: o backend abre a sessao e carimba o cookie ja na
 * resposta do cadastro, entao nao ha uma chamada de entrada depois desta.
 * Quem acabou de escolher a senha nao a digita de novo.
 *
 * O caminho para a entrada fica no rodape, e o da entrada volta para ca: quem
 * errou a porta corrige sem voltar ao comeco.
 */

import { Link, useNavigate } from "react-router";
import { cadastrar } from "../api/client";
import type { Conta } from "../api/types";
import {
  FormularioDeConta,
  REQUISITOS_DA_SENHA,
} from "../components/FormularioDeConta";
import { useConta } from "../estadoDaConta";
import { CAMINHO_ENTRADA, useComCidade } from "../navegacao";

export function Cadastro() {
  const { aoEntrar } = useConta();
  const navegar = useNavigate();
  const comCidade = useComCidade();
  const paraEntrada = comCidade(CAMINHO_ENTRADA);
  const paraInicio = comCidade("/");

  function conseguiu(conta: Conta) {
    // Guarda a conta no estado da rota de layout em vez de reconsultar
    // `/api/quem-sou`: a resposta do cadastro ja **e** a conta, e a consulta
    // devolveria o mesmo e-mail depois de uma volta pela rede.
    aoEntrar(conta);
    // `replace`: sem ele, o Voltar traria de volta um formulario de cadastro
    // para quem ja esta cadastrado e dentro.
    navegar(paraInicio, { replace: true });
  }

  return (
    <FormularioDeConta
      titulo="Criar conta"
      subtitulo="Uma conta guarda seus locais salvos e os leva para qualquer navegador."
      acao="Criar conta"
      requisitos={REQUISITOS_DA_SENHA}
      autocompletarSenha="new-password"
      aoEnviar={cadastrar}
      aoConseguir={conseguiu}
    >
      Ja tem conta?{" "}
      <Link
        to={paraEntrada}
        className="text-brand-text underline underline-offset-2"
      >
        Entrar
      </Link>
      .
    </FormularioDeConta>
  );
}
