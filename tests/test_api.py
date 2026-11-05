"""Testes de integração: fluxos principais da spec.md."""
from datetime import date, timedelta

from src.app import ai, rules


def montar_carteira(api, h):
    """Três ativos de R$ 1.000 (≈33% cada) — habilita a regra de concentração."""
    assert api.investir(h, "ITUB3", 1000, "acao").status_code == 201
    assert api.investir(h, "Tesouro Selic 2029", 1000, "tesouro_selic").status_code == 201
    assert api.investir(h, "CDB Inter", 1000, "cdb").status_code == 201


def vincular(api, h_inv, email_consultor):
    return api.c.put("/vinculo", json={"email_consultor": email_consultor}, headers=h_inv)


def test_registro_login_e_rotas_por_perfil(api):
    hi = api.usuario("investidor", "inv@x.com")
    hc = api.usuario("consultor", "con@x.com")
    assert api.c.get("/carteira", headers=hi).status_code == 200
    assert api.c.get("/carteira", headers=hc).status_code == 403
    assert api.c.get("/consultor/investidores", headers=hi).status_code == 403
    assert api.c.get("/consultor/investidores", headers=hc).status_code == 200
    assert api.c.get("/carteira").status_code == 401


def test_email_duplicado_e_senha_errada(api):
    api.usuario("investidor", "a@x.com")
    r = api.c.post("/auth/registrar", json={"nome": "Outro", "email": "a@x.com", "senha": "senha123", "perfil": "investidor"})
    assert r.status_code == 409
    assert api.c.post("/auth/login", data={"username": "a@x.com", "password": "errada"}).status_code == 401


def test_percentual_e_consolidado(api):
    h = api.usuario("investidor", "inv@x.com")
    montar_carteira(api, h)
    c = api.carteira(h)
    assert c["total_ativo"] == 3000
    assert c["alocacao_por_classe"]["acoes"] == 33.33
    assert all(i["percentual"] == 33.33 for i in c["investimentos"])


def test_aporte_bloqueado_em_inativo(api):  # RN01
    h = api.usuario("investidor", "inv@x.com")
    iid = api.investir(h, "CDB X", 500, "cdb").json()["id"]
    assert api.c.patch(f"/investimentos/{iid}/inativar", headers=h).status_code == 200
    assert api.c.post(f"/investimentos/{iid}/aportes", json={"valor": 10}, headers=h).status_code == 409


def test_expiracao_automatica_e_bloqueio_de_aporte(api, monkeypatch):  # RF03 + RN01
    h = api.usuario("investidor", "inv@x.com")
    iid = api.investir(h, "Tesouro 2026", 500, "tesouro_selic", venc=(date.today() + timedelta(days=1)).isoformat()).json()["id"]
    assert api.carteira(h)["investimentos"][0]["status"] == "ativo"

    class FakeDate(date):
        @classmethod
        def today(cls):
            return date.today() + timedelta(days=5)

    monkeypatch.setattr(rules, "date", FakeDate)  # "viaja" 5 dias no tempo
    assert api.carteira(h)["investimentos"][0]["status"] == "expirado"
    assert api.c.post(f"/investimentos/{iid}/aportes", json={"valor": 10}, headers=h).status_code == 409


def test_vencimento_no_passado_e_rejeitado(api):
    h = api.usuario("investidor", "inv@x.com")
    assert api.investir(h, "Velho", 100, "cdb", venc="2020-01-01").status_code == 422


def test_concentracao_bloqueia_e_consultor_libera(api):  # RN02 / RF15
    hi = api.usuario("investidor", "inv@x.com")
    hc = api.usuario("consultor", "con@x.com")
    montar_carteira(api, hi)
    itub = next(i for i in api.carteira(hi)["investimentos"] if i["nome"] == "ITUB3")["id"]

    r = api.c.post(f"/investimentos/{itub}/aportes", json={"valor": 1000}, headers=hi)  # ITUB3 iria a 50%
    assert r.status_code == 409 and "limite" in r.json()["detail"]
    # até revisão, nem um aporte pequeno passa
    assert api.c.post(f"/investimentos/{itub}/aportes", json={"valor": 1}, headers=hi).status_code == 409
    assert api.carteira(hi)["investimentos"][0]["bloqueado"] is True

    # consultor não vinculado não libera (RN05); depois do vínculo, libera
    assert api.c.post(f"/consultor/investimentos/{itub}/liberar", headers=hc).status_code == 403
    assert vincular(api, hi, "con@x.com").status_code == 200
    assert api.c.post(f"/consultor/investimentos/{itub}/liberar", headers=hc).status_code == 200
    assert api.c.post(f"/investimentos/{itub}/aportes", json={"valor": 1}, headers=hi).status_code == 200


def test_consultor_define_limite_e_alerta_aparece(api):
    hi = api.usuario("investidor", "inv@x.com")
    hc = api.usuario("consultor", "con@x.com")
    montar_carteira(api, hi)
    vincular(api, hi, "con@x.com")
    inv_id = api.c.get("/consultor/investidores", headers=hc).json()[0]["id"]
    assert api.c.patch(f"/consultor/investidores/{inv_id}/limite", json={"limite_concentracao": 30}, headers=hc).status_code == 200
    alertas = api.carteira(hi)["alertas_concentracao"]  # 33,33% > 30%
    assert len(alertas) == 3 and alertas[0]["status"] == "acima"


def test_consultor_so_acessa_investidores_vinculados(api):  # RN05
    hi = api.usuario("investidor", "inv@x.com")
    hc1 = api.usuario("consultor", "c1@x.com")
    hc2 = api.usuario("consultor", "c2@x.com")
    vincular(api, hi, "c1@x.com")
    inv_id = api.c.get("/consultor/investidores", headers=hc1).json()[0]["id"]
    assert api.c.get(f"/consultor/investidores/{inv_id}/carteira", headers=hc1).status_code == 200
    assert api.c.get(f"/consultor/investidores/{inv_id}/carteira", headers=hc2).status_code == 403
    assert api.c.get("/consultor/investidores", headers=hc2).json() == []


def test_investidor_nao_acessa_investimento_de_outro(api):  # RNF04
    h1 = api.usuario("investidor", "a@x.com")
    h2 = api.usuario("investidor", "b@x.com")
    iid = api.investir(h1, "CDB A", 100, "cdb").json()["id"]
    assert api.c.post(f"/investimentos/{iid}/aportes", json={"valor": 10}, headers=h2).status_code == 404
    assert api.c.delete(f"/investimentos/{iid}", headers=h2).status_code == 404


def test_ganhos_por_ativo_e_consolidado_no_mes(api):
    h = api.usuario("investidor", "inv@x.com")
    a = api.investir(h, "ITUB3", 1000, "acao").json()["id"]
    b = api.investir(h, "PRIO3", 1000, "acao").json()["id"]
    for inv_id, valor, data in [(a, 50, "2026-10-05"), (a, 25, "2026-10-20"), (b, 10, "2026-10-07"), (b, 99, "2026-09-30")]:
        r = api.c.post("/ganhos", json={"investimento_id": inv_id, "valor": valor, "data": data, "tipo": "dividendo"}, headers=h)
        assert r.status_code == 201
    r = api.c.get("/ganhos/resumo?mes=2026-10", headers=h).json()
    assert r["total_consolidado"] == 85
    assert {x["nome"]: x["total"] for x in r["por_ativo"]} == {"ITUB3": 75, "PRIO3": 10}


def test_remocao_so_sem_aplicacao_ativa_e_ganhos_permanecem(api):  # RF05
    h = api.usuario("investidor", "inv@x.com")
    iid = api.investir(h, "CDB velho", 500, "cdb").json()["id"]
    api.c.post("/ganhos", json={"investimento_id": iid, "valor": 40, "data": "2026-10-10", "tipo": "rendimento"}, headers=h)
    assert api.c.delete(f"/investimentos/{iid}", headers=h).status_code == 409
    api.c.patch(f"/investimentos/{iid}/inativar", headers=h)
    assert api.c.delete(f"/investimentos/{iid}", headers=h).status_code == 204
    assert api.carteira(h)["investimentos"] == []
    resumo = api.c.get("/ganhos/resumo?mes=2026-10", headers=h).json()
    assert resumo["total_consolidado"] == 40 and resumo["por_ativo"][0]["removido"] is True


def cart_acoes(api, h):
    api.investir(h, "Tesouro", 8000, "tesouro_selic")
    api.investir(h, "ITUB3", 2000, "acao")  # 20% em ações


def preparar_proposta(api, ajustes, perfil_risco="moderado"):
    hi = api.usuario("investidor", "inv@x.com", perfil_risco=perfil_risco)
    hc = api.usuario("consultor", "con@x.com")
    cart_acoes(api, hi)
    vincular(api, hi, "con@x.com")
    inv_id = api.c.get("/consultor/investidores", headers=hc).json()[0]["id"]
    r = api.c.post("/consultor/propostas", json={"investidor_id": inv_id, "justificativa": "Diversificar", "ajustes": ajustes}, headers=hc)
    return hi, hc, inv_id, r


def test_proposta_fora_do_perfil_e_bloqueada(api):  # RF10 / RN03
    _, _, _, r = preparar_proposta(api, [{"classe_de": "tesouro", "classe_para": "acoes", "percentual": 15}])
    assert r.status_code == 422 and "RN03" in r.json()["detail"]


def test_proposta_aceita_aplica_ajuste_na_carteira(api):  # RF09, RF11, RF12
    hi, hc, _, r = preparar_proposta(api, [{"classe_de": "tesouro", "classe_para": "acoes", "percentual": 5}])
    assert r.status_code == 201 and r.json()["status"] == "pendente"
    pid = r.json()["id"]
    assert api.carteira(hi)["alocacao_por_classe"]["acoes"] == 20.0  # nada muda antes do aceite
    resp = api.c.post(f"/propostas/{pid}/responder", json={"decisao": "aceitar"}, headers=hi)
    assert resp.status_code == 200 and resp.json()["status"] == "aceita"
    c = api.carteira(hi)
    assert c["alocacao_por_classe"]["acoes"] == 25.0 and c["total_ativo"] == 10000
    assert api.c.post(f"/propostas/{pid}/responder", json={"decisao": "aceitar"}, headers=hi).status_code == 409
    assert any(e["tipo"] == "rebalanceamento" for e in api.c.get("/historico", headers=hi).json())


def test_proposta_recusada_nao_altera_e_consultor_ve(api):  # RF13
    hi, hc, _, r = preparar_proposta(api, [{"classe_de": "tesouro", "classe_para": "acoes", "percentual": 5}])
    api.c.post(f"/propostas/{r.json()['id']}/responder", json={"decisao": "recusar"}, headers=hi)
    assert api.carteira(hi)["alocacao_por_classe"]["acoes"] == 20.0
    assert api.c.get("/consultor/propostas", headers=hc).json()[0]["status"] == "recusada"


def test_aceite_parcial(api):  # RF11
    ajustes = [{"classe_de": "tesouro", "classe_para": "acoes", "percentual": 2},
               {"classe_de": "tesouro", "classe_para": "cdb_cdi", "percentual": 3}]
    hi, _, _, r = preparar_proposta(api, ajustes)
    p = r.json()
    primeiro = p["ajustes"][0]["id"]
    resp = api.c.post(f"/propostas/{p['id']}/responder", json={"decisao": "parcial", "ajustes_aceitos": [primeiro]}, headers=hi).json()
    assert resp["status"] == "aceita_parcialmente"
    assert [a["aceito"] for a in resp["ajustes"]] == [True, False]
    aloc = api.carteira(hi)["alocacao_por_classe"]
    assert aloc["acoes"] == 22.0 and aloc["cdb_cdi"] == 0.0


def test_parcial_sem_ids_e_rejeitada(api):
    hi, _, _, r = preparar_proposta(api, [{"classe_de": "tesouro", "classe_para": "acoes", "percentual": 2}])
    resp = api.c.post(f"/propostas/{r.json()['id']}/responder", json={"decisao": "parcial", "ajustes_aceitos": []}, headers=hi)
    assert resp.status_code == 422


def test_analise_local_e_proposta_da_ia_nao_altera_carteira(api):  # RF14, RF16, RN04
    hi = api.usuario("investidor", "inv@x.com")  # moderado: máx. 30% em ações
    hc = api.usuario("consultor", "con@x.com")
    api.investir(hi, "ITUB3", 5000, "acao")
    api.investir(hi, "Tesouro", 5000, "tesouro_selic")  # ações = 50%
    vincular(api, hi, "con@x.com")
    inv_id = api.c.get("/consultor/investidores", headers=hc).json()[0]["id"]

    a = api.c.post(f"/consultor/investidores/{inv_id}/analise", headers=hc).json()
    assert a["fonte"] == "regras-locais"
    sug = a["resultado"]["sugestoes_rebalanceamento"][0]
    assert (sug["classe_de"], sug["classe_para"], sug["percentual"]) == ("acoes", "tesouro", 20.0)

    p = api.c.post(f"/consultor/analises/{a['id']}/proposta", headers=hc)
    assert p.status_code == 201 and p.json()["origem"] == "ia" and p.json()["status"] == "pendente"
    assert api.carteira(hi)["alocacao_por_classe"]["acoes"] == 50.0  # a IA não mexe na carteira

    api.c.post(f"/propostas/{p.json()['id']}/responder", json={"decisao": "aceitar"}, headers=hi)
    assert api.carteira(hi)["alocacao_por_classe"]["acoes"] == 30.0


def test_analise_de_carteira_vazia(api):
    h = api.usuario("investidor", "inv@x.com")
    assert api.c.post("/analise", headers=h).status_code == 422


def test_falha_da_ia_retorna_502_sem_quebrar_o_sistema(api, monkeypatch):  # RNF02
    from src.app import config
    h = api.usuario("investidor", "inv@x.com")
    api.investir(h, "ITUB3", 1000, "acao")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "chave-falsa")

    def indisponivel(_):
        raise ai.IAIndisponivel("timeout")

    monkeypatch.setattr(ai, "analisar_com_claude", indisponivel)
    assert api.c.post("/analise", headers=h).status_code == 502
    assert api.c.get("/carteira", headers=h).status_code == 200  # resto do sistema segue de pé


def test_resposta_malformada_da_ia_e_descartada(api, monkeypatch):  # RNF08
    from src.app import config
    h = api.usuario("investidor", "inv@x.com")
    api.investir(h, "ITUB3", 1000, "acao")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "chave-falsa")
    monkeypatch.setattr(ai, "analisar_com_claude", lambda s: ai.validar_resposta("desculpe, não consegui analisar"))
    r = api.c.post("/analise", headers=h)
    assert r.status_code == 502 and "descartada" in r.json()["detail"]


def test_validar_resposta_da_ia():
    ok = ai.validar_resposta('```json\n{"score_risco": 40, "concentracao_alertas": [], "sugestoes_rebalanceamento": []}\n```')
    assert ok.score_risco == 40
    import pytest
    with pytest.raises(ai.RespostaInvalida):
        ai.validar_resposta('{"score_risco": 400, "concentracao_alertas": [], "sugestoes_rebalanceamento": []}')  # fora de 0-100
    with pytest.raises(ai.RespostaInvalida):
        ai.validar_resposta('{"score_risco": 10, "concentracao_alertas": [], "sugestoes_rebalanceamento": [{"classe_de": "cripto", "classe_para": "tesouro", "percentual": 5, "justificativa": "x"}]}')


def test_tela_web_e_servida(client):
    r = client.get("/app/")
    assert r.status_code == 200 and "Carteira de Investimento" in r.text
    assert client.get("/", follow_redirects=False).headers["location"] == "/app/"


def test_login_bloqueado_apos_tentativas_erradas(api):  # segurança: força bruta
    api.usuario("investidor", "alvo@x.com")
    for _ in range(5):
        assert api.c.post("/auth/login", data={"username": "alvo@x.com", "password": "errada"}).status_code == 401
    r = api.c.post("/auth/login", data={"username": "alvo@x.com", "password": "senha123"})  # até a senha certa é barrada
    assert r.status_code == 429


def test_login_correto_zera_o_contador(api):
    api.usuario("investidor", "ok@x.com")
    for _ in range(4):
        api.c.post("/auth/login", data={"username": "ok@x.com", "password": "errada"})
    assert api.c.post("/auth/login", data={"username": "ok@x.com", "password": "senha123"}).status_code == 200
    assert api.c.post("/auth/login", data={"username": "ok@x.com", "password": "errada"}).status_code == 401


def test_resposta_traz_tempo_de_processamento(api):  # observabilidade
    r = api.c.get("/saude")
    assert float(r.headers["X-Process-Time-ms"]) >= 0


def test_concentracao_ignora_maiusculas_e_espacos(api):  # achado da revisão: "ITUB3" = "itub3"
    h = api.usuario("investidor", "inv@x.com")
    montar_carteira(api, h)
    r = api.investir(h, "  itub3 ", 1000, "acao")
    assert r.status_code == 409 and "limite" in r.json()["detail"]
