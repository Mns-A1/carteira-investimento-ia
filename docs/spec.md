# Spec.md — Sistema de Carteira de Investimentos com Consultoria Assistida por IA

> Status: versão do MVP implementado, alinhada ao código (revisão final)
> Última atualização: 05/11/2026

## 1. Visão Geral

O sistema permite que **Investidores** gerenciem carteiras de investimento (Tesouro Direto, CDB/CDI, Ações, Poupança) e que **Consultores** acompanhem, analisem e proponham rebalanceamentos para as carteiras de seus clientes. Uma camada de IA analisa o histórico de cada carteira e retorna dados estruturados (score de risco, alertas de concentração, sugestões de rebalanceamento) que alimentam as regras de negócio do sistema — a decisão final é sempre do sistema ou do usuário, nunca da IA isoladamente.

## 1.1 Problema e Justificativa

Investidores pessoa física que aplicam em múltiplos tipos de ativo (Tesouro, CDB/CDI, Ações, Poupança) costumam enfrentar dois problemas combinados: falta de visão consolidada de risco (quanto está concentrado em um único ativo) e falta de acompanhamento personalizado que vá além de indicadores brutos. Ferramentas de consolidação de carteira existentes entregam dados, mas não julgamento; plataformas de educação financeira entregam conteúdo, mas não atuam sobre a carteira real do usuário. O sistema proposto ocupa esse espaço: une o registro real da carteira a um fluxo de consultoria ativa, apoiado por análise estruturada de IA, com decisão final sempre humana.

## 1.2 Público-Alvo

- **Investidores pessoa física iniciantes ou intermediários**, com carteira diversificada em mais de um tipo de ativo, que querem acompanhamento sem depender apenas de autoanálise de indicadores.
- **Consultores financeiros (ou estudantes/profissionais em formação na área)** que acompanham carteiras de terceiros e precisam de uma ferramenta para propor e justificar ajustes de forma estruturada e rastreável.

## 1.3 Escopo

**Está dentro do escopo:**
- Registro manual de investimentos, ganhos e status (ativo/inativo/expirado).
- Cálculo de consolidado de carteira e de ganhos por ativo e por período.
- Vínculo Consultor–Investidor e fluxo de proposta de rebalanceamento com aceite/recusa.
- Análise de carteira via IA retornando dados estruturados (score de risco, alertas de concentração, sugestões).
- Regras de bloqueio automáticas (concentração máxima, perfil de risco, status de investimento).

**Está fora do escopo:**
- Integração em tempo real com corretoras ou com a B3 (sincronização automática de operações).
- Execução real de ordens de compra/venda — o sistema é de acompanhamento e decisão, não uma corretora.
- Cotação de mercado em tempo real — valores de rendimento/preço são informados manualmente pelo usuário ou simulados.

## 1.4 Benchmark

Foram analisados dois sistemas existentes no mercado de finanças pessoais para calibrar a proposta:

| Critério | Finclass | StatusInvest | Este sistema |
|---|---|---|---|
| Carteira personalizada com dados reais do usuário | Não — carteira-modelo única, igual para todos os assinantes | Sim, com sincronização automática via B3 | Sim (registro manual) |
| Múltiplos perfis com interesses distintos | Não — apenas consumo de conteúdo | Não — apenas o investidor analisando indicadores sozinho | Sim — Investidor e Consultor, com fluxo de proposta e aprovação |
| Consultoria ativa e personalizada | Não — conteúdo gravado, sem interação 1:1 | Não — a própria plataforma recomenda buscar um consultor externo | Sim — Consultor propõe, sistema valida contra o perfil de risco |
| Análise automatizada de risco por IA | Não | Não — indicadores manuais | Sim — score de risco e alertas de concentração via IA |
| Regras de negócio automáticas (bloqueio por concentração/perfil) | Não | Não | Sim |

**Conclusão do benchmark:** o StatusInvest resolve a consolidação de dados, mas não o julgamento sobre eles; a Finclass resolve a educação, mas não atua sobre a carteira real do usuário. O sistema proposto se diferencia por unir dado real de carteira a uma camada de decisão (humana, apoiada por IA) — o consultor e o investidor decidem juntos, com regras de negócio explícitas mediando o processo.

## 2. Personas

### 2.1 Investidor
- **Quem é:** pessoa física que aplica seu próprio dinheiro em diferentes tipos de investimento.
- **Objetivo:** acompanhar rentabilidade, entender sua exposição a risco, decidir sobre propostas de rebalanceamento.
- **Dores:** dificuldade de enxergar concentração de risco; falta de clareza sobre por que um consultor sugere uma mudança.

### 2.2 Consultor
- **Quem é:** responsável por acompanhar as carteiras de um ou mais Investidores vinculados a ele.
- **Objetivo:** manter as carteiras dos clientes dentro do perfil de risco definido, propor ajustes com justificativa.
- **Dores:** acompanhar manualmente concentração de ativos em várias carteiras ao mesmo tempo; necessidade de justificar tecnicamente cada sugestão.

## 3. Modelo de Domínio (entidades principais)

- **Usuário** (atributos comuns: id, nome, email, perfil [Investidor | Consultor])
- **Investidor** (perfil_risco: conservador | moderado | agressivo; limite_concentracao, padrão 40%; consultor_vinculado)
- **Consultor** (lista de investidores vinculados)
- **Carteira** (pertence a um Investidor; contém lista de Investimentos)
- **Investimento** (tipo: Tesouro Selic | Tesouro IPCA | Tesouro Educa+ | CDB | CDI | Ação | Poupança; nome do ativo; valor_aplicado; data_aplicacao; data_vencimento (opcional); status: ativo | inativo | expirado; bloqueado; removido). O percentual de alocação não é armazenado: é calculado sobre os investimentos ativos da carteira.
- **Ganho** (vinculado a um Investimento; valor_recebido; data_recebimento; tipo: dividendo | rendimento)
- **PropostaDeRebalanceamento** (gerada por Consultor ou por análise de IA; contém lista de ajustes [de_ativo, para_ativo, percentual]; status: pendente | aceita | recusada | aceita_parcialmente; justificativa)
- **AnaliseIA** (snapshot da carteira no momento da análise; score_risco; alertas_concentracao; sugestoes; consumida por PropostaDeRebalanceamento)
- **Evento** (histórico de auditoria: tipo, descrição, data/hora e usuário responsável)

## 4. Requisitos Funcionais (notação EARS)

### 4.1 Gestão de Carteira (Investidor)

- **RF01** — Quando o Investidor informar uma nova aplicação, o sistema deve registrar o investimento na carteira com tipo, nome do ativo, valor, data de aplicação e vencimento (opcional), e calcular automaticamente o percentual de alocação.
- **RF02** — O sistema deve, sempre que solicitado pelo Investidor, exibir a visão consolidada da carteira com valores aplicados, percentual de alocação por investimento e por classe (Tesouro, CDB/CDI, Ações, Poupança) e os alertas de concentração. O registro de valores retirados está fora do escopo do MVP (backlog).
- **RF03** — Se um investimento atingir a data de vencimento, então o sistema deve alterar automaticamente seu status para "expirado".
- **RF04** — O sistema deve impedir novo aporte em um investimento com status "expirado" ou "inativo".
- **RF05** — Quando o Investidor solicitar a exclusão de um investimento sem aplicação ativa (inativo ou expirado), o sistema deve removê-lo da carteira de forma lógica, mantendo os ganhos já registrados nos relatórios, e registrar o evento no histórico.

### 4.2 Ganhos

- **RF06** — Quando o Investidor registrar um ganho (dividendo/rendimento) vinculado a um investimento, o sistema deve armazená-lo com valor, data e tipo.
- **RF07** — O sistema deve, sempre que solicitado, calcular e exibir o total de ganhos por ativo individual e o total consolidado no período (mês).

### 4.3 Consultoria (Consultor)

- **RF08** — O sistema deve permitir que um Consultor visualize as carteiras de todos os Investidores vinculados a ele.
- **RF09** — Quando o Consultor criar uma proposta de rebalanceamento, o sistema deve validar que a proposta respeita o perfil de risco declarado do Investidor antes de permitir o envio.
- **RF10** — Se a proposta de rebalanceamento não respeitar o perfil de risco do Investidor, então o sistema deve bloquear o envio e notificar o Consultor do motivo.
- **RF11** — Quando o Investidor receber uma proposta de rebalanceamento, o sistema deve permitir que ele aceite, recuse ou aceite parcialmente a proposta.
- **RF12** — Quando uma proposta for aceita (total ou parcialmente), o sistema deve aplicar os ajustes correspondentes na carteira e registrar o evento no histórico.
- **RF13** — Quando uma proposta for recusada, o sistema deve manter o registro da proposta e notificar o Consultor.

### 4.4 Análise por IA

- **RF14** — O sistema deve permitir a geração de uma análise de IA sobre a carteira de um Investidor, retornando dados estruturados: score de risco, alertas de concentração por ativo e sugestões de rebalanceamento.
- **RF15** — Se um aporte fizer um ativo ultrapassar o limite de concentração (padrão 40% da carteira, com 3 ou mais ativos), então o sistema deve recusar o aporte, gerar um alerta e bloquear novas aplicações naquele ativo até a revisão do Consultor. O alerta também aparece na visão consolidada sempre que algum ativo estiver acima do limite.
- **RF16** — O sistema deve utilizar a saída estruturada da IA apenas como insumo para gerar uma Proposta de Rebalanceamento — a aplicação do ajuste na carteira depende sempre da decisão do Investidor (RF11/RF12).
- **RF17** — Quando o Investidor informar o e-mail de um Consultor, o sistema deve vinculá-lo ao Investidor, autorizando o Consultor a acompanhar a carteira; o Investidor pode desfazer o vínculo a qualquer momento.
- **RF18** — Quando o Consultor definir um limite de concentração para um Investidor vinculado, o sistema deve usá-lo no lugar do padrão; quando o Consultor liberar um ativo bloqueado, o sistema deve voltar a aceitar aportes nele.

## 4.5 Requisitos Não Funcionais

- **RNF01 — Desempenho:** O sistema deve responder a requisições de consulta de carteira (RF02) em até 2 segundos sob condições normais de uso.
- **RNF02 — Disponibilidade da análise de IA:** Se a chamada à API de IA falhar ou expirar (timeout), o sistema deve informar o erro ao usuário sem interromper o funcionamento das demais funcionalidades (RF14).
- **RNF03 — Segurança de autenticação:** Senhas de usuários devem ser armazenadas com hash (nunca em texto plano); tokens de sessão devem expirar após um período definido de inatividade.
- **RNF04 — Confidencialidade:** Um Investidor nunca deve conseguir visualizar ou acessar dados de carteira de outro Investidor, mesmo por manipulação direta de URL/endpoint (autorização a nível de recurso, não apenas de tela).
- **RNF05 — Rastreabilidade:** Toda alteração relevante na carteira (aporte, rebalanceamento aplicado, exclusão) deve ficar registrada em log/histórico com data, hora e usuário responsável, para fins de auditoria.
- **RNF06 — Usabilidade da API:** A API deve fornecer documentação interativa (ex: Swagger/OpenAPI) que permita testar todos os endpoints sem necessidade de ferramentas externas.
- **RNF07 — Portabilidade de dados:** O sistema deve utilizar um banco de dados relacional padrão (SQLite em desenvolvimento, com possibilidade de migração para PostgreSQL) sem dependência de fornecedor proprietário.
- **RNF08 — Resiliência da IA:** O sistema deve validar o formato JSON retornado pela IA antes de processá-lo; uma resposta malformada deve ser descartada com log de erro, nunca aplicada à carteira (reforça RN04).
- **RNF09 — Manutenibilidade:** O código deve seguir uma separação clara entre camada de regras de negócio, camada de acesso a dados e camada de exposição (API), facilitando testes e futuras alterações sem reescrever o sistema inteiro.
- **RNF10 — Proteção contra força bruta:** Após 5 tentativas de login incorretas em 10 minutos, o sistema deve bloquear novas tentativas para aquele e-mail por até 10 minutos.
- **RNF11 — Observabilidade:** O sistema deve registrar em log cada requisição (método, rota, status e tempo), as recusas por regras de negócio e as falhas da IA, e devolver o tempo de resposta no cabeçalho `X-Process-Time-ms`.

## 5. Glossário

| Termo | Definição |
|---|---|
| **Ativo** | Qualquer instrumento financeiro no qual um valor pode ser aplicado (ex: ação, título do Tesouro, CDB). |
| **Alocação** | Percentual do valor total da carteira aplicado em um tipo específico de investimento. |
| **CDB (Certificado de Depósito Bancário)** | Título de renda fixa emitido por bancos, no qual o investidor empresta dinheiro à instituição em troca de rendimento. |
| **CDI (Certificado de Depósito Interbancário)** | Taxa de referência usada para indexar a rentabilidade de diversos investimentos de renda fixa. |
| **Concentração de ativo** | Percentual que um único ativo representa do valor total da carteira; concentração excessiva aumenta o risco. |
| **Consultor** | Perfil de usuário responsável por acompanhar e propor ajustes nas carteiras de Investidores vinculados a ele. |
| **Dividendo** | Parcela do lucro de uma empresa distribuída aos acionistas. |
| **Investidor** | Perfil de usuário que aplica recursos próprios em investimentos e acompanha sua carteira. |
| **JSON estruturado** | Formato de dados (JavaScript Object Notation) usado para que a IA retorne informações em campos previsíveis e processáveis pelo sistema, em vez de texto livre. |
| **Perfil de risco** | Classificação do Investidor (conservador, moderado ou agressivo) que define os limites aceitáveis de exposição a ativos de maior risco. |
| **Proposta de Rebalanceamento** | Sugestão formal de ajuste na composição da carteira, criada por um Consultor ou apoiada por análise de IA, sujeita a aceite do Investidor. |
| **Rebalanceamento** | Ação de ajustar a distribuição percentual dos ativos de uma carteira para alinhá-la a um perfil de risco ou estratégia definida. |
| **Rendimento** | Ganho financeiro obtido a partir de um investimento de renda fixa (ex: Tesouro, CDB). |
| **Score de risco** | Valor numérico gerado pela análise de IA que resume o nível de exposição a risco de uma carteira. |
| **Status do investimento** | Estado atual de um investimento na carteira: ativo, inativo ou expirado. |
| **Tesouro Direto** | Programa do governo federal para venda de títulos públicos a pessoas físicas (ex: Tesouro Selic, Tesouro IPCA). |

## 6. Regras de Negócio Explícitas

- **RN01** — Um investimento com status "expirado" ou "inativo" não pode receber novos aportes (suporta RF04).
- **RN02** — O limite máximo de concentração por ativo é de 40% do valor total dos investimentos ativos, salvo configuração do Consultor para aquele Investidor. A regra só é verificada quando a carteira tem 3 ou mais ativos distintos (com menos, qualquer carteira excederia o limite). Nomes de ativo são comparados sem diferenciar maiúsculas e espaços. Um aporte que ultrapasse o limite é recusado e o ativo fica bloqueado para novos aportes até o Consultor liberá-lo. Ajustes aplicados por propostas aceitas não são bloqueados, mas podem gerar alerta.
- **RN03** — Toda proposta de rebalanceamento deve manter a carteira dentro do perfil de risco do Investidor, medido pelo máximo de ações na carteira resultante: conservador 10%, moderado 30%, agressivo 60%. Propostas fora desse limite são bloqueadas automaticamente na criação e revalidadas no momento do aceite.
- **RN04** — A IA nunca aplica mudanças diretamente na carteira; toda sugestão da IA passa a ser uma Proposta de Rebalanceamento sujeita à aprovação do Investidor.
- **RN05** — Um Consultor só pode visualizar e propor mudanças em carteiras de Investidores explicitamente vinculados a ele.
- **RN06** — Apenas investimentos com status ativo entram no cálculo de alocação e de concentração. Investimentos inativos ou expirados não recebem aportes (RN01).

## 7. Casos de Uso (resumo inicial)

1. **UC01 — Registrar aplicação:** Investidor informa tipo, valor e data de um novo investimento.
2. **UC02 — Consultar carteira:** Investidor visualiza consolidado de valores, percentuais e status dos investimentos.
3. **UC03 — Registrar ganho:** Investidor lança dividendo/rendimento recebido em um ativo específico.
4. **UC04 — Solicitar análise de IA:** Investidor ou Consultor dispara análise; sistema retorna score de risco e alertas.
5. **UC05 — Propor rebalanceamento:** Consultor (com ou sem apoio da análise de IA) cria proposta de ajuste.
6. **UC06 — Responder proposta:** Investidor aceita, recusa ou aceita parcialmente a proposta recebida.
7. **UC07 — Editar/excluir investimento:** Investidor remove investimento sem aplicação ativa.
8. **UC08 — Vincular consultor:** Investidor autoriza um Consultor a acompanhar sua carteira.
9. **UC09 — Gerenciar limite e bloqueios:** Consultor define o limite de concentração e libera ativos bloqueados.
10. **UC10 — Consultar histórico:** Investidor consulta a trilha de auditoria da carteira.

## 8. Backlog (itens do MVP concluídos; pendências no fim)

- [x] Modelagem do banco de dados (entidades da seção 3)
- [x] CRUD de investimentos (Investidor)
- [x] Cálculo de consolidado da carteira
- [x] Registro e cálculo de ganhos
- [x] Vínculo Consultor–Investidor
- [x] Fluxo de criação e resposta de proposta de rebalanceamento
- [x] Integração com IA (prompt estruturado + parsing de JSON)
- [x] Regras de bloqueio (concentração, perfil de risco, status expirado)
- [x] Autenticação e diferenciação de perfil (Investidor vs Consultor)

- [ ] Registro de retiradas (valores retirados)
- [ ] Valores monetários com Decimal ou centavos inteiros
- [ ] Token de sessão em cookie httpOnly
- [ ] Exceções de domínio nos serviços (hoje elas levantam erros HTTP)

## 9. Decisões de implementação (mudanças em relação à versão inicial)

| # | Item | Decisão tomada | Motivo |
|---|---|---|---|
| 1 | RF01 | O percentual de alocação é calculado, não informado | Muda a cada novo aporte; armazenar geraria dados desatualizados |
| 2 | RF02 | Sem registro de retiradas no MVP | Fora do tempo disponível; vai para o backlog |
| 3 | RN02 | Limite só vale com 3 ou mais ativos; aporte que estoura é recusado e trava o ativo | Com 1 ou 2 ativos, qualquer carteira passaria de 40% e o sistema ficaria inutilizado |
| 4 | RN03 | Limites de ações por perfil: 10%, 30% e 60% | A versão inicial não definia valores concretos |
| 5 | RF08 / RF17 | O vínculo é iniciado pelo Investidor | O dono dos dados autoriza quem os acompanha |
| 6 | RF05 | Remoção lógica, preservando ganhos | Manter o lucro visível, como definido no caderno de requisitos inicial |
| 7 | RF03 | Expiração verificada a cada consulta ou aporte, sem job agendado | Simplicidade; o resultado para o usuário é o mesmo |
| 8 | RF14 | Sem chave da IA, a análise roda em modo local e a resposta marca fonte "regras-locais" | Permite usar e demonstrar o sistema sem depender de serviço externo |

## 10. Limitações conhecidas

- Um rebalanceamento aceito pode concentrar valor em um único ativo; o sistema mostra alerta, mas não bloqueia.
- A chamada real ao Claude depende de chave de API e não é coberta por teste automatizado (os testes cobrem a validação da resposta e as falhas).
- Valores monetários usam ponto flutuante, com arredondamento a 2 casas.
- O bloqueio de tentativas de login fica em memória: zera ao reiniciar o sistema.
- O token de sessão fica no localStorage do navegador; o texto exibido é sempre escapado para reduzir o risco de XSS.
