"""Testes unitários das regras puras (RN01–RN03, RF03)."""
from datetime import date, timedelta

from src.app import rules


def item(nome, classe, valor):
    return {"nome": nome, "classe": classe, "valor": valor}


def test_status_expira_ao_atingir_vencimento():  # RF03
    hoje = date(2026, 10, 22)
    assert rules.status_efetivo("ativo", hoje, hoje) == "expirado"
    assert rules.status_efetivo("ativo", hoje + timedelta(days=1), hoje) == "ativo"
    assert rules.status_efetivo("ativo", None, hoje) == "ativo"


def test_inativo_permanece_inativo():
    assert rules.status_efetivo("inativo", date(2020, 1, 1), date(2026, 1, 1)) == "inativo"


def test_alocacao_por_classe_soma_100():
    itens = [item("A", "tesouro", 500), item("B", "acoes", 300), item("C", "cdb_cdi", 200)]
    aloc = rules.alocacao_por_classe(itens)
    assert aloc == {"tesouro": 50.0, "cdb_cdi": 20.0, "acoes": 30.0, "poupanca": 0.0}


def test_concentracao_nao_vale_com_poucos_ativos():  # 1 ou 2 ativos sempre passariam de 40%
    excede, pct = rules.excede_concentracao([item("A", "acoes", 100)], "B", 100, 40)
    assert excede is False and pct == 50.0


def test_concentracao_excedida_com_tres_ativos():  # RN02
    itens = [item("A", "acoes", 1000), item("B", "tesouro", 1000), item("C", "cdb_cdi", 1000)]
    excede, pct = rules.excede_concentracao(itens, "A", 1000, 40)
    assert excede is True and pct == 50.0
    excede, _ = rules.excede_concentracao(itens, "A", 100, 40)
    assert excede is False


def test_proposta_dentro_do_perfil():  # RN03
    itens = [item("T", "tesouro", 8000), item("A", "acoes", 2000)]
    ok, _, proj = rules.validar_proposta(itens, [{"classe_de": "tesouro", "classe_para": "acoes", "percentual": 5}], "moderado")
    assert ok and proj["acoes"] == 25.0


def test_proposta_fora_do_perfil():  # RN03
    itens = [item("T", "tesouro", 8000), item("A", "acoes", 2000)]
    ok, motivo, _ = rules.validar_proposta(itens, [{"classe_de": "tesouro", "classe_para": "acoes", "percentual": 15}], "moderado")
    assert not ok and "30%" in motivo


def test_proposta_sem_saldo_na_classe_de_origem():
    itens = [item("T", "tesouro", 1000)]
    ok, motivo, _ = rules.validar_proposta(itens, [{"classe_de": "acoes", "classe_para": "tesouro", "percentual": 5}], "agressivo")
    assert not ok and "acoes" in motivo


def test_score_de_risco_limitado_a_100():
    assert rules.calcular_score_risco({"acoes": 100.0}, {"A": 100.0}) == 100
