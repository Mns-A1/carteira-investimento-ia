# ADR 0001 — Escolha da stack tecnológica

**Status:** Aceito

## Contexto
O projeto é desenvolvido por uma única pessoa, com prazo de um semestre, e o foco da avaliação está na qualidade da especificação e das regras de negócio, não na tecnologia em si. Era necessária uma stack de desenvolvimento rápido, com pouco código repetitivo, boa integração com APIs de IA e facilidade para testar regras de negócio isoladamente.

## Decisão
Adotar **Python + FastAPI** para a API, **SQLite** como banco de dados (acessado via **SQLAlchemy**) e **Pytest** para testes. A interface visual fica em segundo plano: a API é validada pela documentação interativa (Swagger) gerada automaticamente pelo FastAPI.

## Consequências
- (+) Desenvolvimento rápido e com pouco boilerplate, adequado a um projeto solo.
- (+) Documentação interativa da API sem esforço adicional (apoia o RNF06).
- (+) SQLite dispensa configuração de servidor; o uso do SQLAlchemy permite migrar para PostgreSQL depois sem reescrever o domínio (RNF07).
- (−) SQLite não é indicado para alta concorrência de escrita; aceitável para o escopo acadêmico.
- (−) Sem frontend completo, a demonstração depende do Swagger ou de templates simples (Jinja2), se sobrar tempo.
