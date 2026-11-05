# Revisão multidimensional

Revisão do MVP em quatro dimensões (arquitetura, performance, segurança e observabilidade), feita em 05/11/2026 sobre o código completo. Cada achado indica a ação tomada e a evidência. Os problemas marcados como **corrigido** foram resolvidos e têm teste automatizado; os demais estão no backlog (`docs/tasks.md`, Fase 8).

## Arquitetura

| ID | Achado | Severidade | Ação | Situação |
|---|---|---|---|---|
| A1 | Camadas bem separadas (rotas, serviços, regras puras, modelos). As regras puras são testáveis sem banco: `rules.py` tem 99% de cobertura | Positivo | Manter | Atendido |
| A2 | **Bug de regra de negócio:** "ITUB3" e "itub3" contavam como ativos diferentes e escapavam do limite de concentração (RN02) | Média | Comparação sem diferenciar maiúsculas e espaços, e nome limpo na entrada | **Corrigido**. Teste: `test_concentracao_ignora_maiusculas_e_espacos` |
| A3 | Os serviços levantam erros HTTP (`HTTPException`), acoplando a regra de negócio ao protocolo web | Média | Criar exceções de domínio e traduzi-las nos routers | Backlog |
| A4 | Valores monetários em ponto flutuante | Média | Mitigado com arredondamento a 2 casas; migrar para Decimal ou centavos inteiros | Backlog |
| A5 | Rebalanceamento aceito pode concentrar valor em um único ativo (gera alerta, não bloqueio) | Baixa | Documentado em `spec.md`, RN02 e seção 10 | Aceito |

## Performance

| ID | Achado | Severidade | Ação | Situação |
|---|---|---|---|---|
| P1 | RNF01 (consulta da carteira em até 2 s) com 300 investimentos: mediana 12 ms e p95 12 ms. Com a ferramenta de cobertura ativa, que desacelera o código, ficou em ~95 ms | Positivo | Teste automatizado fixa o limite de 2 s | Atendido. Teste: `test_consulta_da_carteira_com_300_investimentos_em_ate_2s` |
| P2 | Algumas consultas ao banco se repetem dentro de uma mesma requisição (carteira e lista de investimentos) | Baixa | Reaproveitar a lista já carregada | Backlog |
| P3 | SQLite limita escritas simultâneas | Baixa | Já previsto no ADR 0001; migração para PostgreSQL é possível sem mudar o domínio | Aceito |

## Segurança

| ID | Achado | Severidade | Ação | Situação |
|---|---|---|---|---|
| S1 | Senhas com bcrypt, token JWT com expiração e autorização por recurso (um usuário não acessa dados de outro) | Positivo | Testes de 403 e 404 | Atendido. Testes: `test_consultor_so_acessa_investidores_vinculados`, `test_investidor_nao_acessa_investimento_de_outro` |
| S2 | Sem o `.env`, o sistema usava uma chave JWT padrão conhecida, o que permitiria forjar tokens | Média | Aviso no log ao iniciar com a chave padrão; README e `.env.example` pedem um segredo próprio | **Corrigido** (mitigação) |
| S3 | **Login sem limite de tentativas** (força bruta) | Média | Após 5 erros em 10 minutos, o e-mail é bloqueado (HTTP 429) | **Corrigido**. Testes: `test_login_bloqueado_apos_tentativas_erradas`, `test_login_correto_zera_o_contador` |
| S4 | Token JWT guardado em localStorage no navegador, exposto em caso de XSS | Média | Todo texto livre (nomes de ativo, justificativas) é escapado antes de ser exibido; migrar para cookie httpOnly | Mitigado; backlog |
| S5 | Campo livre (nome do ativo) segue para a IA: risco de injeção de instruções | Baixa | Defesa em camadas: a resposta passa por validação de schema, a proposta passa pela RN03 e só o aceite do investidor altera a carteira (RN04) | Mitigado |
| S6 | Dependências vulneráveis | Positivo | `pip-audit`: nenhuma vulnerabilidade conhecida (`docs/evidencias/pip-audit.txt`) | Atendido |
| S7 | O contador de tentativas de login fica em memória (zera ao reiniciar) | Baixa | Em produção, usar armazenamento compartilhado | Aceito |
| S8 | Senha só exige 6 caracteres | Baixa | Endurecer a regra de senha | Backlog |

## Observabilidade

| ID | Achado | Severidade | Ação | Situação |
|---|---|---|---|---|
| O1 | **Não havia logs da aplicação**, apenas a tabela de eventos | Média | Log de cada requisição (método, rota, status, tempo), cabeçalho `X-Process-Time-ms`, log das recusas por regra (concentração) e das falhas da IA, com fonte e duração de cada análise | **Corrigido**. Teste: `test_resposta_traz_tempo_de_processamento` |
| O2 | Trilha de auditoria (tabela Evento, rota `/historico`) cobre aportes, bloqueios, propostas e rebalanceamentos | Positivo | Manter | Atendido (RNF05) |
| O3 | Logs em texto simples, sem métricas nem alertas | Baixa | Logs estruturados (JSON) e métricas | Backlog |

## Resumo

- 4 achados corrigidos nesta revisão (A2, S2, S3, O1), todos com teste ou verificação.
- 8 itens vão para o backlog, nenhum bloqueia o uso do MVP.
- Resultado dos testes depois das correções: 37 aprovados, 94% de cobertura (`docs/evidencias/`).
