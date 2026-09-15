/**
 * A cidade com que o app abre quando ninguem escolheu nenhuma.
 *
 * Duas origens, nesta ordem: a **cidade detectada** e a **ultima cidade**.
 * A detectada ganha porque conceder a permissao de localizacao *e* a pessoa
 * dizendo "use minha localizacao" — honra-la nao e inferencia, e cumprir uma
 * instrucao que ela ja deu.
 *
 * Nenhuma origem reclama quando falha: timeout, coordenada longe demais,
 * browser sem Permissions API. Cada uma devolve `null` e o degrau seguinte
 * assume. Negar nao e falha, e nao merece mensagem.
 */

import { buscarCidadePorCoordenada } from "./api/client";
import { parametrosDaCidade } from "./cidadeNaUrl";
import { pedirLocalizacao, permissaoConcedida } from "./localizacao";
import { ultimaCidade } from "./ultimaCidade";

/**
 * A cidade resolvida a partir da coordenada do navegador.
 *
 * O navegador entrega **coordenada**, nunca cidade — quem resolve e o backend,
 * sobre o dataset local. Acima de 50 km da cidade mais proxima nao ha cidade
 * detectada, e isso e resultado normal: sugerir uma cidade a centenas de
 * quilometros e pior que o silencio.
 */
async function cidadeDetectada(
  aoComecarADetectar: () => void,
): Promise<URLSearchParams | null> {
  // Consulta o estado da permissao; nunca dispara pop-up.
  if (!(await permissaoConcedida())) return null;

  // Daqui em diante ha carga a caminho, e quem chama precisa saber **agora**:
  // `getCurrentPosition` espera ate 10 s por um GPS lento, e ate a coordenada
  // chegar a tela ficaria em branco se ela ainda estivesse esperando a decisao.
  aoComecarADetectar();

  const localizacao = await pedirLocalizacao();
  if (localizacao.tipo !== "coordenada") return null;

  try {
    const cidade = await buscarCidadePorCoordenada(
      localizacao.latitude,
      localizacao.longitude,
    );
    return cidade ? parametrosDaCidade(cidade) : null;
  } catch {
    // O backend fora do ar no carregamento cai para a ultima cidade, que e
    // exatamente do que ela serve.
    return null;
  }
}

/**
 * A cidade inicial, como parametros de URL, ou `null` se nao houver nenhuma.
 *
 * `aoComecarADetectar` avisa o momento em que a resposta deixa de ser rapida:
 * a consulta da permissao e a leitura da ultima cidade sao instantaneas, mas
 * esperar a coordenada nao e. Sem esse aviso, quem tem a permissao concedida
 * veria a tela em branco ate o GPS responder.
 */
export async function descobrirCidadeInicial(
  aoComecarADetectar: () => void,
): Promise<URLSearchParams | null> {
  return (await cidadeDetectada(aoComecarADetectar)) ?? ultimaCidade();
}
