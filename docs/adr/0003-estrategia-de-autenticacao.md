# ADR 0003 — Estratégia de autenticação: JWT

**Status:** Aceito

## Contexto
O sistema tem dois perfis (Investidor e Consultor) com permissões distintas, e cada rota precisa saber quem está chamando e qual é o seu perfil. A API é REST, sem frontend acoplado, o que torna a gestão de sessão no servidor desnecessária.

## Decisão
Autenticar com **JWT (JSON Web Token)**: o login valida e-mail e senha (armazenada com hash bcrypt) e devolve um token com expiração curta, contendo o identificador e o perfil do usuário. Cada rota protegida valida o token e, em seguida, verifica a autorização sobre o recurso solicitado.

## Consequências
- (+) Stateless: o servidor não guarda sessões, simplificando a API e os testes.
- (+) O perfil vai no token, facilitando a separação de rotas entre Investidor e Consultor.
- (−) Revogar um token antes da expiração é difícil; mitigado com tempo de vida curto.
- (−) O token não substitui a autorização por recurso: a verificação de "este recurso pertence a este usuário" continua obrigatória em cada rota (RNF04, RN05).
