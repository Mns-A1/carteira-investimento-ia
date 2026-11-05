# Estratégia de testes e evidências de qualidade

## 1. Estratégia

| Nível | O que cobre | Ferramenta | Quantidade |
|---|---|---|---|
| Unitário | Regras de negócio puras (`rules.py`): expiração, alocação, concentração, perfil de risco, score | pytest | 9 |
| Integração (API + banco) | Fluxos completos pelas rotas, com banco SQLite em memória e usuários reais de cada perfil | pytest + TestClient | 27 |
| Desempenho | RNF01: consulta da carteira com 300 investimentos em até 2 s | pytest | 1 |
| Falhas da IA | Indisponibilidade, resposta malformada e validação do schema da resposta | pytest (monkeypatch) | 3 |
| Ponta a ponta no navegador | Roteiro manual: login, carteira, aporte, análise, consultor gera proposta, investidor aceita | Chromium (Playwright), executado durante o desenvolvimento | roteiro |

Os 3 testes de falha da IA fazem parte dos 27 de integração. Os testes nunca chamam a IA real: sem `ANTHROPIC_API_KEY`, a análise roda em modo local.

## 2. Como executar

```
.venv\Scripts\python.exe -m pytest -v
.venv\Scripts\python.exe -m pytest --cov=src/app --cov-report=term-missing
```

## 3. Resultados (05/11/2026)

- **37 testes aprovados**, nenhum falho (`docs/evidencias/pytest.txt`).
- **Cobertura de 94%** (728 instruções, 47 não cobertas) (`docs/evidencias/cobertura.txt`).
- **Desempenho:** consulta da carteira com 300 investimentos, mediana de 12 ms e p95 de 12 ms (`docs/evidencias/desempenho.txt`).
- **Dependências:** nenhuma vulnerabilidade conhecida (`docs/evidencias/pip-audit.txt`).

## 4. Rastreabilidade (requisito para teste)

| Requisito | Testes |
|---|---|
| RF01, RF02 | `test_percentual_e_consolidado` |
| RF03, RN01 | `test_status_expira_ao_atingir_vencimento`, `test_expiracao_automatica_e_bloqueio_de_aporte`, `test_aporte_bloqueado_em_inativo`, `test_vencimento_no_passado_e_rejeitado` |
| RF05 | `test_remocao_so_sem_aplicacao_ativa_e_ganhos_permanecem` |
| RF06, RF07 | `test_ganhos_por_ativo_e_consolidado_no_mes` |
| RF08, RN05 | `test_consultor_so_acessa_investidores_vinculados` |
| RF09, RF10, RN03 | `test_proposta_dentro_do_perfil`, `test_proposta_fora_do_perfil`, `test_proposta_fora_do_perfil_e_bloqueada`, `test_proposta_sem_saldo_na_classe_de_origem` |
| RF11, RF12 | `test_proposta_aceita_aplica_ajuste_na_carteira`, `test_aceite_parcial`, `test_parcial_sem_ids_e_rejeitada` |
| RF13 | `test_proposta_recusada_nao_altera_e_consultor_ve` |
| RF14, RF16, RN04 | `test_analise_local_e_proposta_da_ia_nao_altera_carteira`, `test_analise_de_carteira_vazia` |
| RF15, RN02 | `test_concentracao_nao_vale_com_poucos_ativos`, `test_concentracao_excedida_com_tres_ativos`, `test_concentracao_bloqueia_e_consultor_libera`, `test_consultor_define_limite_e_alerta_aparece`, `test_concentracao_ignora_maiusculas_e_espacos` |
| RNF01 | `test_consulta_da_carteira_com_300_investimentos_em_ate_2s` |
| RNF02 | `test_falha_da_ia_retorna_502_sem_quebrar_o_sistema` |
| RNF03, RNF10 | `test_registro_login_e_rotas_por_perfil`, `test_email_duplicado_e_senha_errada`, `test_login_bloqueado_apos_tentativas_erradas`, `test_login_correto_zera_o_contador` |
| RNF04 | `test_investidor_nao_acessa_investimento_de_outro` |
| RNF05 | `test_proposta_aceita_aplica_ajuste_na_carteira` (confere o histórico) |
| RNF08 | `test_resposta_malformada_da_ia_e_descartada`, `test_validar_resposta_da_ia` |
| RNF11 | `test_resposta_traz_tempo_de_processamento` |
| Tela web | `test_tela_web_e_servida` |

## 5. Lacunas conhecidas

- A chamada real ao Claude (linhas 75 a 88 de `ai.py`) não é coberta por teste automatizado, pois depende de chave e rede. A validação da resposta e as falhas são cobertas.
- A interface web não tem testes automatizados versionados; foi validada pelo roteiro de ponta a ponta no navegador.
- O desempenho foi medido com SQLite em memória, sem rede, em um computador de desenvolvimento.

## 6. Melhorias feitas a partir dos testes e da revisão

Veja `docs/review/revisao-multidimensional.md`: correção da comparação de ativos (A2), limite de tentativas de login (S3), aviso de chave JWT padrão (S2) e logs de requisição (O1).
