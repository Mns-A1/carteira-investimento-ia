# Tasks.md — Tarefas Atômicas

> Status em 05/11/2026: todas as tarefas do MVP concluídas (evidências em docs/testes.md e docs/review). Cada tarefa referencia a Issue correspondente no GitHub e os requisitos da spec.md que ela implementa. Status é atualizado conforme o Kanban do projeto evolui.

## Fase 1 — Fundação

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Definir schema das entidades (Usuário, Investidor, Consultor, Carteira, Investimento, Ganho, PropostaDeRebalanceamento, AnaliseIA) | #1 | Spec seção 3 | Concluído |
| Criar o script de criação das tabelas (automático na inicialização do sistema) | #1 | Spec seção 3 | Concluído |
| Implementar hash de senha e modelo de autenticação | #8 | RNF03 | Concluído |
| Implementar diferenciação de rotas por perfil (Investidor/Consultor) | #8 | RF08, RN05 | Concluído |

## Fase 2 — Núcleo do Investidor

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Endpoint de registro de novo investimento | #2 | RF01 | Concluído |
| Endpoint de consulta consolidada da carteira | #2 | RF02 | Concluído |
| Validação de bloqueio de aporte em investimento expirado/inativo | #2, #7 | RF04, RN01 | Concluído |
| Endpoint de exclusão de investimento sem aplicação ativa | #2 | RF05 | Concluído |
| Endpoint de registro de ganho (dividendo/rendimento) | #3 | RF06 | Concluído |
| Cálculo de total de ganhos por ativo e por período | #3 | RF07 | Concluído |

## Fase 3 — Núcleo do Consultor

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Modelo de vínculo Consultor–Investidor | #4 | RF08 | Concluído |
| Endpoint de listagem de carteiras vinculadas ao Consultor | #4 | RF08 | Concluído |
| Bloqueio de acesso a carteira de Investidor não vinculado | #4 | RN05 | Concluído |

## Fase 4 — Regras Automáticas

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Verificação automática do status "expirado" (a cada consulta e aporte) | #7 | RF03 | Concluído |
| Cálculo de percentual de concentração por ativo | #7 | RF15, RN02 | Concluído |
| Bloqueio de novas aplicações em ativo acima do limite de concentração | #7 | RF15, RN02 | Concluído |

## Fase 5 — Fluxo de Rebalanceamento

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Endpoint de criação de proposta de rebalanceamento (Consultor) | #5 | RF09 | Concluído |
| Validação da proposta contra o perfil de risco do Investidor | #5 | RF10, RN03 | Concluído |
| Endpoint de resposta à proposta (aceitar/recusar/aceitar parcialmente) | #5 | RF11 | Concluído |
| Aplicação do ajuste na carteira quando aceito | #5 | RF12 | Concluído |
| Registro de histórico de propostas recusadas | #5 | RF13 | Concluído |

## Fase 6 — Integração com IA

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Montagem do prompt estruturado com snapshot da carteira | #6 | RF14 | Concluído |
| Chamada à API da Anthropic e recebimento da resposta | #6 | RF14 | Concluído |
| Validação de schema do JSON retornado | #6 | RNF08, RN04 | Concluído |
| Tratamento de erro/timeout da chamada de IA | #6 | RNF02 | Concluído |
| Conversão da sugestão da IA em Proposta de Rebalanceamento | #6 | RF16, RN04 | Concluído |

## Fase 7 — Testes e Documentação Final

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Testes unitários das regras de negócio críticas (RN01–RN05) | — | RNF09 | Concluído |
| Preenchimento de docs/review com achados de revisão | — | Seção 7 do edital | Concluído |
| Consolidação de ADRs (stack, IA, autenticação, modelo de dados) | — | Seção 8 do edital | Concluído |
| Atualização final do README com instruções de execução | — | Seção 9.1 do edital | Concluído |

## Fase 8 — Pós-MVP (backlog)

| Tarefa | Issue | Requisitos cobertos | Status |
|---|---|---|---|
| Registro de retiradas de investimentos | — | RF02 | A fazer |
| Valores monetários com Decimal ou centavos inteiros | — | Revisão (arquitetura) | A fazer |
| Token de sessão em cookie httpOnly | — | Revisão (segurança) | A fazer |
| Exceções de domínio nos serviços, traduzidas nos routers | — | Revisão (arquitetura) | A fazer |
| Logs estruturados (JSON) e métricas | — | RNF11 | A fazer |
