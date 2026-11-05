"""Configuração lida de variáveis de ambiente (.env). Segredos nunca vão para o repositório."""
import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./carteira.db")
JWT_SECRET_PADRAO = "chave-de-desenvolvimento-troque-em-producao-0123456789"
JWT_SECRET = os.getenv("JWT_SECRET", JWT_SECRET_PADRAO)
JWT_ALGORITHM = "HS256"
JWT_EXPIRA_MINUTOS = int(os.getenv("JWT_EXPIRA_MINUTOS", "60"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
LIMITE_CONCENTRACAO_PADRAO = 40.0  # RN02
