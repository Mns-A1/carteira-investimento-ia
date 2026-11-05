# Carteira de Investimento com Consultoria Assistida por IA

Sistema web com dois perfis de usuário. O **Investidor** registra e acompanha seus investimentos (Tesouro, CDB/CDI, Ações e Poupança). O **Consultor** acompanha as carteiras dos investidores que o vincularam e propõe rebalanceamentos. Uma **análise por IA** devolve dados estruturados (score de risco, alertas de concentração e sugestões), mas a decisão final é sempre do investidor: a IA nunca altera a carteira.

Projeto final de Modelagem de Software (2026-2, Turma 04G).
**Autor:** Pedro Meneses Neves, RA 10738187

## Funcionalidades

- Cadastro e login por perfil (Investidor e Consultor), com limite de tentativas de login
- Carteira consolidada: alocação por classe, percentual por investimento e alertas de concentração
- Aportes, inativação e remoção de investimentos, com expiração automática no vencimento
- Registro de ganhos (dividendos e rendimentos) com resumo por ativo e por mês
- Vínculo Consultor–Investidor, limite de concentração por investidor e liberação de ativos bloqueados
- Propostas de rebalanceamento validadas pelo perfil de risco; o investidor aceita, recusa ou aceita parcialmente
- Análise de carteira por IA (Claude) com resposta em JSON validada; funciona também em modo local, sem chave
- Histórico de auditoria de todas as operações

## Como executar

Requisitos: Python 3.10 ou superior. No Windows (PowerShell), dentro da pasta do projeto:

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.venv\Scripts\python.exe -m src.seed
.venv\Scripts\python.exe -m uvicorn src.app.main:app --reload
```

No Linux ou macOS, troque `.venv\Scripts\python.exe` por `.venv/bin/python` e `copy` por `cp`.

Abra **http://127.0.0.1:8000**. O comando `src.seed` cria dados de demonstração (senha `demo1234`):

- `investidor@demo.com`
- `consultor@demo.com`

A documentação interativa da API fica em `http://127.0.0.1:8000/docs`.

### Usar o Claude de verdade

Edite o `.env`, preencha `ANTHROPIC_API_KEY` e defina um `JWT_SECRET` próprio. Sem a chave, a análise roda em modo local e a resposta mostra `"fonte": "regras-locais"`; com a chave, mostra `"fonte": "claude"`.

## Testes

```
.venv\Scripts\python.exe -m pytest -v
```

37 testes, 94% de cobertura. Detalhes em [docs/testes.md](docs/testes.md).

## Estrutura

```
src/app/        código (routers, services, rules, models, ai, security) e tela web em static/
src/seed.py     dados de demonstração
tests/          testes automatizados
docs/           documentação (veja abaixo)
```

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/spec.md](docs/spec.md) | Requisitos em EARS, personas, modelo de domínio, regras de negócio, decisões de implementação |
| [docs/plan.md](docs/plan.md) | Plano técnico e fases |
| [docs/tasks.md](docs/tasks.md) | Tarefas atômicas e status |
| [docs/architecture.md](docs/architecture.md) | Arquitetura, diagrama de componentes e segurança |
| [docs/adr/](docs/adr) | Decisões de arquitetura (4 ADRs) |
| [docs/uml.md](docs/uml.md) | Diagramas UML (casos de uso, classes, sequência e estados) |
| [docs/review/](docs/review) | Revisão multidimensional: achados e ações |
| [docs/testes.md](docs/testes.md) | Estratégia de testes e evidências |
| [docs/seguranca-ssdlc.md](docs/seguranca-ssdlc.md) | Segurança e SSDLC |

## Limitações conhecidas

Veja a seção 10 de [docs/spec.md](docs/spec.md). As principais: valores monetários em ponto flutuante, contador de login em memória e chamada real ao Claude não coberta por teste automatizado.
