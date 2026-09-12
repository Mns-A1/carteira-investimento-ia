# Plan.md — Plano Técnico

> Este documento traduz a spec.md em decisões técnicas de implementação. Deve ser atualizado sempre que uma decisão de arquitetura mudar.

## 1. Stack Tecnológica

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Linguagem / Framework | Python + FastAPI | Desenvolvimento rápido para projeto solo, geração automática de documentação interativa (Swagger/OpenAPI), tipagem via Pydantic facilita validação das regras de negócio. |
| Banco de dados | SQLite (desenvolvimento) | Zero configuração, atende à exigência de persistência sem custo de infraestrutura. Migração futura para PostgreSQL é possível sem reescrever a camada de domínio. |
| ORM | SQLAlchemy | Mapeamento das entidades do modelo de domínio (spec.md, seção 3) para tabelas relacionais. |
| IA / LLM | API da Anthropic (Claude) | Geração de saída estruturada (JSON) para análise de carteira, conforme RF14–RF16. |
| Testes | Pytest | Padrão de mercado para Python, permite testes unitários das regras de negócio isoladas da API. |
| Interface | API via Swagger (fase inicial); Jinja2 Templates (se houver tempo, fase final) | Prioriza regras de negócio e persistência sobre interface visual, conforme escopo do projeto acadêmico. |

## 2. Arquitetura em Camadas

     Integração externa: 
     Camada de Regras de Negócio → API de IA (Claude) → JSON estruturado

     
A separação entre camadas segue o requisito não funcional RNF09 (manutenibilidade), evitando que regras de negócio fiquem misturadas com código de rota ou de acesso a dados.

## 3. Fases de Implementação

### Fase 1 — Fundação (Issues 1, 8)
- Modelagem do banco de dados (todas as entidades da spec.md, seção 3).
- Autenticação e diferenciação de perfil (Investidor / Consultor).

### Fase 2 — Núcleo do Investidor (Issues 2, 3)
- CRUD de investimentos.
- Registro e cálculo de ganhos.

### Fase 3 — Núcleo do Consultor (Issue 4)
- Vínculo Consultor–Investidor e restrição de acesso.

### Fase 4 — Regras Automáticas (Issue 7)
- Bloqueios por status de investimento e por concentração de ativo.

### Fase 5 — Fluxo de Rebalanceamento (Issue 5)
- Criação, validação, aceite/recusa de propostas.

### Fase 6 — Integração com IA (Issue 6)
- Chamada à API da Anthropic, parsing de JSON estruturado, tratamento de erro.

### Fase 7 — Testes e Documentação Final
- Cobertura de testes das regras de negócio críticas.
- ADRs consolidados, docs/review preenchido, README final.

## 4. Decisões que exigem ADR

- Escolha da stack (Python + FastAPI + SQLite).
- Escolha do provedor de IA (Anthropic Claude) para análise estruturada.
- Estratégia de autenticação (a definir: JWT ou sessão simples).
- Estrutura do modelo de dados central.

## 5. Riscos Identificados

| Risco | Mitigação |
|---|---|
| Resposta da IA fora do formato JSON esperado | Validação de schema antes de qualquer aplicação na carteira (RNF08). |
| Escopo maior do que o tempo disponível (projeto solo) | Priorização por fases; interface visual fica para o final, só se houver tempo sobrando. |
| Falta de revisor externo para Pull Requests (projeto solo) | Documentar como limitação conhecida em ADR; autorrevisão sistemática antes de cada merge. |
