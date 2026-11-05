import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import config, models
from ..database import get_db
from ..schemas import RegistroIn, TokenOut
from ..security import criar_token, hash_senha, usuario_atual, verificar_senha

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Proteção contra força bruta: após MAX_FALHAS erros em JANELA segundos, o e-mail fica bloqueado (em memória).
MAX_FALHAS, JANELA = 5, 600
_FALHAS: dict[str, list[float]] = {}


def _falhas_recentes(email: str) -> list[float]:
    recentes = [t for t in _FALHAS.get(email, []) if time.time() - t < JANELA]
    _FALHAS[email] = recentes
    return recentes


@router.post("/registrar", status_code=201)
def registrar(dados: RegistroIn, db: Session = Depends(get_db)):
    email = dados.email.lower()
    if db.query(models.Usuario).filter_by(email=email).first():
        raise HTTPException(409, "E-mail já cadastrado.")
    if len(dados.senha.encode()) > 72:
        raise HTTPException(422, "Senha muito longa (máximo de 72 bytes).")
    u = models.Usuario(nome=dados.nome, email=email, senha_hash=hash_senha(dados.senha), perfil=dados.perfil)
    db.add(u)
    db.flush()
    if dados.perfil == "investidor":
        inv = models.Investidor(usuario_id=u.id, perfil_risco=dados.perfil_risco,
                                limite_concentracao=config.LIMITE_CONCENTRACAO_PADRAO)
        db.add(inv)
        db.flush()
        db.add(models.Carteira(investidor_id=inv.id))
    else:
        db.add(models.Consultor(usuario_id=u.id))
    db.commit()
    return {"id": u.id, "nome": u.nome, "email": u.email, "perfil": u.perfil}


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """No Swagger, use o e-mail no campo 'username'."""
    email = form.username.lower()
    if len(_falhas_recentes(email)) >= MAX_FALHAS:
        raise HTTPException(429, "Muitas tentativas de login. Aguarde alguns minutos e tente novamente.")
    u = db.query(models.Usuario).filter_by(email=email).first()
    if not u or not verificar_senha(form.password, u.senha_hash):
        _FALHAS.setdefault(email, []).append(time.time())
        raise HTTPException(401, "E-mail ou senha incorretos.")
    _FALHAS.pop(email, None)
    return {"access_token": criar_token(u), "token_type": "bearer", "perfil": u.perfil}


@router.get("/eu")
def eu(u: models.Usuario = Depends(usuario_atual)):
    return {"id": u.id, "nome": u.nome, "email": u.email, "perfil": u.perfil}
