# ADR 0002 — Uso de IA (Claude) para análise estruturada da carteira

**Status:** Aceito

## Contexto
O sistema precisa analisar a carteira de um Investidor e apontar risco, concentração excessiva e sugestões de rebalanceamento. Essa análise deve produzir **dados estruturados consumidos pelo sistema**, e não apenas texto exibido ao usuário (seção 6.5 do edital). A decisão final não pode ficar a cargo do modelo.

## Decisão
Usar a **API da Anthropic (Claude)** para analisar um snapshot da carteira e devolver um **JSON com schema definido** (score de risco, alertas de concentração, sugestões). O sistema valida o schema, e somente então transforma a sugestão em uma Proposta de Rebalanceamento — que continua dependendo do aceite do Investidor.

## Consequências
- (+) Cumpre o padrão "o LLM classifica, o sistema decide": a IA nunca altera a carteira diretamente (RN04).
- (+) Respostas malformadas são descartadas pela validação de schema, sem afetar os dados (RNF08).
- (+) A lógica de negócio (limites de concentração, perfil de risco) permanece em código determinístico e testável.
- (−) Dependência de serviço externo: falha ou timeout da API precisa ser tratado sem derrubar o sistema (RNF02).
- (−) Custo por chamada e necessidade de proteger a chave de API (variável de ambiente, fora do repositório).
