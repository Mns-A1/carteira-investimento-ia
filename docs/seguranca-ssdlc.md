# Segurança e SSDLC

## 1. Controles implementados

| Controle | Requisito | Onde | Verificação |
|---|---|---|---|
| Senhas com hash bcrypt | RNF03 | `security.py` | `test_registro_login_e_rotas_por_perfil` |
| JWT com expiração | RNF03, ADR 0003 | `security.py` | `test_registro_login_e_rotas_por_perfil` |
| Autorização por perfil e por recurso | RNF04, RN05 | `security.py`, `services.py`, routers | `test_consultor_so_acessa_investidores_vinculados`, `test_investidor_nao_acessa_investimento_de_outro` |
| Limite de tentativas de login | RNF10 | `routers/auth.py` | `test_login_bloqueado_apos_tentativas_erradas` |
| Consultas parametrizadas (ORM) contra SQL Injection | RNF04 | `models.py`, `services.py` | Revisão de código: sem SQL manual |
| Validação de entrada (Pydantic) | RNF04 | `schemas.py` | Revisão de código (tipos e faixas nos schemas); sem teste dedicado |
| Validação do JSON da IA antes de uso | RNF08 | `ai.py` | `test_validar_resposta_da_ia` |
| Segredos fora do repositório (`.env`) | RNF03 | `config.py`, `.gitignore` | `.env.example` sem valores reais |
| Texto livre (nomes, justificativas) escapado na tela | Revisão S4 | `static/index.html` | Revisão de código |
| Trilha de auditoria | RNF05 | `models.Evento`, `/historico` | `test_proposta_aceita_aplica_ajuste_na_carteira` |
| Auditoria de dependências | Revisão S6 | `pip-audit` | `docs/evidencias/pip-audit.txt` |

## 2. SSDLC: segurança em cada fase

| Fase | Prática adotada |
|---|---|
| Requisitos | Requisitos de segurança escritos em EARS (RNF03, RNF04, RNF08, RNF10) |
| Projeto | ADR 0003 (autenticação), ADR 0002 (IA só sugere, nunca altera a carteira) e seção de segurança em `architecture.md` |
| Implementação | Hash de senha, ORM, validação de entrada, segredos em variável de ambiente, escape de saída |
| Verificação | Testes automatizados de autorização e de limite de login, `pip-audit` e revisão multidimensional |
| Manutenção | Achados registrados em `docs/review` com severidade, ação e situação; backlog de endurecimento em `docs/tasks.md` (Fase 8) |

## 3. Ameaças consideradas

| Ameaça | Mitigação | Risco residual |
|---|---|---|
| Acesso a dados de outro usuário | Autorização por recurso em toda rota | Baixo |
| Adivinhação de senha | bcrypt, limite de tentativas, senha mínima | Médio: contador em memória e senha curta permitida |
| Token forjado | Segredo próprio no `.env`, aviso quando o padrão é usado | Médio se o aviso for ignorado em produção |
| Roubo de token por XSS | Escape de saída | Médio: token em localStorage |
| Injeção de instruções na IA pelo nome do ativo | Schema validado, regra RN03, aceite humano | Baixo |
| IA indisponível ou com resposta inválida | Erro 502 tratado, resposta descartada, resto do sistema segue de pé | Baixo |
| Dados em trânsito | HTTPS é obrigatório em produção (não aplicável na execução local) | Depende da implantação |
