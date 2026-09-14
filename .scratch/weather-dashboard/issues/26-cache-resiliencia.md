# 26: Cache e resiliência

**What to build:** o painel se comporta bem quando as coisas demoram ou falham: mostra que está carregando, explica de forma compreensível quando o serviço externo está fora do ar, e não refaz trabalho desnecessário. A origem dos dados fica visível na página.

**Blocked by:** 23, 25

**Status:** ready-for-agent

Passada final cobrindo todos os caminhos de dados de uma vez — por isso depende dos dois ramos (23 e 25) terem convergido.

Referência: [spec](../spec.md), "Módulos do backend" e "Further Notes".

- [ ] Cache em memória, TTL de 10 min, chave por **coordenada arredondada**
- [ ] Estado de carregamento visível durante as requisições
- [ ] API externa fora do ar: mensagem compreensível, não stack trace
- [ ] Cidade não encontrada: mensagem clara orientando a corrigir o texto
- [ ] Rodapé de atribuição renderizado a partir do campo `attribution` do payload, nunca texto fixo no frontend
- [ ] Teste: duas requisições iguais produzem **uma** chamada externa; após o TTL, duas. Relógio injetado, sem `sleep`
- [ ] Teste: coordenadas próximas arredondam para a mesma chave de cache
- [ ] Teste: falha da API externa vira erro tratado
- [ ] **Um** teste de contrato marcado `contract`, **fora** da suíte padrão, batendo na API real e verificando apenas presença de campos — nunca valores
