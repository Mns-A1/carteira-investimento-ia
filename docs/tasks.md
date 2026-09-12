# Tasks.md — Tarefas Atômicas

> Cada tarefa referencia a Issue correspondente no GitHub e os requisitos da spec.md que ela implementa. Status é atualizado conforme o Kanban do projeto evolui.

## Fase 1 — Fundação

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Definir schema das entidades (Usuário, Investidor, Consultor, Carteira, Investimento, Ganho, PropostaDeRebalanceamento, AnaliseIA) | #1 | Spec seção 3 | A fazer |
| Criar migrations/script de criação das tabelas | #1 | Spec seção 3 | A fazer |
| Implementar hash de senha e modelo de autenticação | #8 | RNF03 | A fazer |
| Implementar diferenciação de rotas por perfil (Investidor/Consultor) | #8 | RF08, RN05 | A fazer |

## Fase 2 — Núcleo do Investidor

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Endpoint de registro de novo investimento | #2 | RF01 | A fazer |
| Endpoint de consulta consolidada da carteira | #2 | RF02 | A fazer |
| Validação de bloqueio de aporte em investimento expirado/inativo | #2, #7 | RF04, RN01 | A fazer |
| Endpoint de exclusão de investimento sem aplicação ativa | #2 | RF05 | A fazer |
| Endpoint de registro de ganho (dividendo/rendimento) | #3 | RF06 | A fazer |
| Cálculo de total de ganhos por ativo e por período | #3 | RF07 | A fazer |

## Fase 3 — Núcleo do Consultor

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Modelo de vínculo Consultor–Investidor | #4 | RF08 | A fazer |
| Endpoint de listagem de carteiras vinculadas ao Consultor | #4 | RF08 | A fazer |
| Bloqueio de acesso a carteira de Investidor não vinculado | #4 | RN05 | A fazer |

## Fase 4 — Regras Automáticas

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Job/verificação de mudança automática de status para "expirado" | #7 | RF03 | A fazer |
| Cálculo de percentual de concentração por ativo | #7 | RF15, RN02 | A fazer |
| Bloqueio de novas aplicações em ativo acima do limite de concentração | #7 | RF15, RN02 | A fazer |

## Fase 5 — Fluxo de Rebalanceamento

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Endpoint de criação de proposta de rebalanceamento (Consultor) | #5 | RF09 | A fazer |
| Validação da proposta contra o perfil de risco do Investidor | #5 | RF10, RN03 | A fazer |
| Endpoint de resposta à proposta (aceitar/recusar/aceitar parcialmente) | #5 | RF11 | A fazer |
| Aplicação do ajuste na carteira quando aceito | #5 | RF12 | A fazer |
| Registro de histórico de propostas recusadas | #5 | RF13 | A fazer |

## Fase 6 — Integração com IA

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Montagem do prompt estruturado com snapshot da carteira | #6 | RF14 | A fazer |
| Chamada à API da Anthropic e recebimento da resposta | #6 | RF14 | A fazer |
| Validação de schema do JSON retornado | #6 | RNF08, RN04 | A fazer |
| Tratamento de erro/timeout da chamada de IA | #6 | RNF02 | A fazer |
| Conversão da sugestão da IA em Proposta de Rebalanceamento | #6 | RF16, RN04 | A fazer |

## Fase 7 — Testes e Documentação Final

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Testes unitários das regras de negócio críticas (RN01–RN05) | — | RNF09 | A fazer |
| Preenchimento de docs/review com achados de revisão | — | Seção 7 do edital | A fazer |
| Consolidação de ADRs (stack, IA, autenticação, modelo de dados) | — | Seção 8 do edital | A fazer |
| Atualização final do README com instruções de execução | — | Seção 9.1 do edital | A fazer |
