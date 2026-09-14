# 21: Buscar cidade e ver a temperatura atual

**What to build:** a pessoa digita o nome de uma cidade, escolhe entre as candidatas quando o nome é ambíguo, e vê o card do dia com a temperatura atual, a descrição em palavras, o ícone, a sensação térmica e a máxima/mínima. É a primeira fatia que entrega valor real ao usuário.

**Blocked by:** 20

**Status:** ready-for-agent

Referência: [spec](../spec.md), seções "Contrato da API", "Armadilhas de formato da API externa", "Módulos do backend".

- [ ] `GET /api/cities?q=` devolve candidatas com nome, estado, país e população
- [ ] `GET /api/weather` devolve os blocos `location`, `current`, `units` e `attribution`
- [ ] Tabela WMO no **backend** traduz código em texto e nome de ícone, com fallback para código desconhecido
- [ ] A chave `results` **ausente** na resposta do geocoding vira "cidade não encontrada", não exceção
- [ ] `current.high`/`low` vêm do bloco diário, que a API não fornece em `current`
- [ ] Campo de busca com dropdown de desambiguação exibindo estado e país
- [ ] Card do dia renderizado com os tokens do ticket 20 e ícones Meteocons
- [ ] Modelos Pydantic espelhando o payload; tipos TypeScript espelhando o mesmo no frontend
- [ ] Testes na costura HTTP: cidade encontrada, cidade não encontrada (fixture com `results` ausente), nome ambíguo
- [ ] Teste da tabela WMO: todo código emitido tem texto e ícone
