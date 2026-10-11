# ADR 0004 — Modelo de dados central

**Status:** Aceito

## Contexto
As regras de negócio (concentração por ativo, perfil de risco, propostas com aceite parcial, histórico de alterações) dependem de um modelo de dados que represente claramente o domínio descrito na seção 3 da spec.md.

## Decisão
Modelar o domínio com as entidades **Usuário, Investidor, Consultor, Carteira, Investimento, Ganho, PropostaDeRebalanceamento e AnaliseIA**, em banco relacional. O Investimento carrega seu **status** (ativo, inativo, expirado); a Proposta de Rebalanceamento carrega seu estado (pendente, aceita, recusada, aceita parcialmente); a AnaliseIA guarda o snapshot da carteira usado na análise, para rastreabilidade.

## Consequências
- (+) Estados explícitos permitem implementar as regras RN01–RN05 como validações simples e testáveis.
- (+) O snapshot da AnaliseIA permite auditar qualquer proposta gerada com apoio da IA (RNF05).
- (+) Um modelo relacional atende bem às consultas de consolidado e de ganhos por período.
- (−) Alterações de regra que exijam novos estados demandam migração do esquema.
- (−) Guardar snapshots aumenta o volume de dados; aceitável para o escopo do projeto.
