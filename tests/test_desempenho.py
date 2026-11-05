"""RNF01: a consulta da carteira responde em até 2 s (aqui, com 300 investimentos)."""
import statistics
import time

from src.app import models
from src.app.database import get_db
from src.app.main import app


def test_consulta_da_carteira_com_300_investimentos_em_ate_2s(api):
    h = api.usuario("investidor", "perf@x.com")
    db = next(app.dependency_overrides[get_db]())
    carteira = db.query(models.Carteira).one()
    db.add_all([models.Investimento(carteira_id=carteira.id, tipo="acao", nome=f"ATIVO{i}", valor_aplicado=100.0,
                                    data_aplicacao=__import__("datetime").date.today()) for i in range(300)])
    db.commit()
    tempos = []
    for _ in range(20):
        t = time.perf_counter()
        r = api.c.get("/carteira", headers=h)
        tempos.append(time.perf_counter() - t)
        assert r.status_code == 200 and len(r.json()["investimentos"]) == 300
    p95 = sorted(tempos)[int(len(tempos) * 0.95) - 1]
    print(f"\n[RNF01] 300 investimentos, 20 consultas: mediana={statistics.median(tempos)*1000:.0f} ms, p95={p95*1000:.0f} ms")
    assert p95 < 2.0
