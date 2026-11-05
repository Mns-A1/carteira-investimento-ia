import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import config
from src.app.database import Base, get_db
from src.app.main import app


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")  # testes nunca chamam a IA real
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override():
        db = Sessao()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    from src.app.routers import auth
    auth._FALHAS.clear()
    yield TestClient(app)  # sem "with": não dispara o lifespan (não cria carteira.db)
    app.dependency_overrides.clear()


class Api:
    """Atalhos para os testes."""

    def __init__(self, client):
        self.c = client

    def usuario(self, perfil, email, nome="Teste", perfil_risco="moderado"):
        r = self.c.post("/auth/registrar", json={"nome": nome, "email": email, "senha": "senha123",
                                                  "perfil": perfil, "perfil_risco": perfil_risco})
        assert r.status_code == 201, r.text
        t = self.c.post("/auth/login", data={"username": email, "password": "senha123"})
        assert t.status_code == 200, t.text
        return {"Authorization": f"Bearer {t.json()['access_token']}"}

    def investir(self, h, nome, valor, tipo="acao", venc=None):
        body = {"tipo": tipo, "nome": nome, "valor_aplicado": valor, "data_aplicacao": "2026-01-10"}
        if venc:
            body["data_vencimento"] = venc
        return self.c.post("/investimentos", json=body, headers=h)

    def carteira(self, h):
        return self.c.get("/carteira", headers=h).json()


@pytest.fixture()
def api(client):
    return Api(client)
