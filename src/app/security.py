"""Autenticação JWT e autorização por perfil (ADR 0003, RNF03, RNF04)."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import config, models
from .database import get_db

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha: str, hash_: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode(), hash_.encode())
    except ValueError:
        return False


def criar_token(usuario: models.Usuario) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=config.JWT_EXPIRA_MINUTOS)
    return jwt.encode({"sub": str(usuario.id), "perfil": usuario.perfil, "exp": exp},
                      config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def usuario_atual(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> models.Usuario:
    try:
        uid = int(jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Token inválido ou expirado.")
    usuario = db.get(models.Usuario, uid)
    if not usuario:
        raise HTTPException(401, "Usuário não encontrado.")
    return usuario


def investidor_atual(u: models.Usuario = Depends(usuario_atual), db: Session = Depends(get_db)) -> models.Investidor:
    if u.perfil != "investidor":
        raise HTTPException(403, "Acesso restrito a investidores.")
    return db.query(models.Investidor).filter_by(usuario_id=u.id).one()


def consultor_atual(u: models.Usuario = Depends(usuario_atual), db: Session = Depends(get_db)) -> models.Consultor:
    if u.perfil != "consultor":
        raise HTTPException(403, "Acesso restrito a consultores.")
    return db.query(models.Consultor).filter_by(usuario_id=u.id).one()
