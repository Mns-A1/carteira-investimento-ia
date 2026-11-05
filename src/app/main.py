import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .database import Base, engine
from .routers import auth, consultor, investidor


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("carteira")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    if config.JWT_SECRET == config.JWT_SECRET_PADRAO:
        log.warning("JWT_SECRET padrão em uso: defina um segredo próprio no .env antes de publicar o sistema.")
    yield


app = FastAPI(
    title="Carteira de Investimento com Consultoria Assistida por IA",
    version="0.1.0",
    description="Investidores gerenciam carteiras; Consultores propõem rebalanceamentos; a IA analisa e sugere, "
                "mas a decisão final é sempre do investidor. Use **Authorize** com e-mail e senha para testar.",
    lifespan=lifespan,
)
app.include_router(auth.router)
app.include_router(investidor.router)
app.include_router(consultor.router)


app.mount("/app", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="app")


@app.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse("/app/")


@app.get("/saude", tags=["Sistema"])
def saude():
    return {"status": "ok"}


@app.middleware("http")
async def registrar_requisicoes(request: Request, call_next):
    """Observabilidade: log de cada chamada da API e cabeçalho com o tempo de resposta."""
    inicio = time.perf_counter()
    resposta = await call_next(request)
    ms = (time.perf_counter() - inicio) * 1000
    resposta.headers["X-Process-Time-ms"] = f"{ms:.1f}"
    if not request.url.path.startswith("/app"):
        log.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, resposta.status_code, ms)
    return resposta
