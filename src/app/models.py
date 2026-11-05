"""Modelo de dados central (ADR 0004 / spec.md seção 3)."""
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(100))
    perfil: Mapped[str] = mapped_column(String(20))  # investidor | consultor


class Consultor(Base):
    __tablename__ = "consultores"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True)


class Investidor(Base):
    __tablename__ = "investidores"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True)
    perfil_risco: Mapped[str] = mapped_column(String(20), default="moderado")
    limite_concentracao: Mapped[float] = mapped_column(Float, default=40.0)
    consultor_id: Mapped[int | None] = mapped_column(ForeignKey("consultores.id"), nullable=True)


class Carteira(Base):
    __tablename__ = "carteiras"
    id: Mapped[int] = mapped_column(primary_key=True)
    investidor_id: Mapped[int] = mapped_column(ForeignKey("investidores.id"), unique=True)


class Investimento(Base):
    __tablename__ = "investimentos"
    id: Mapped[int] = mapped_column(primary_key=True)
    carteira_id: Mapped[int] = mapped_column(ForeignKey("carteiras.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(20))
    nome: Mapped[str] = mapped_column(String(120))
    valor_aplicado: Mapped[float] = mapped_column(Float)
    data_aplicacao: Mapped[date] = mapped_column(Date)
    data_vencimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(15), default="ativo")  # ativo | inativo | expirado
    bloqueado: Mapped[bool] = mapped_column(Boolean, default=False)  # RN02: aguardando revisão do Consultor
    removido: Mapped[bool] = mapped_column(Boolean, default=False)  # RF05: some da carteira, ganhos permanecem


class Ganho(Base):
    __tablename__ = "ganhos"
    id: Mapped[int] = mapped_column(primary_key=True)
    investimento_id: Mapped[int] = mapped_column(ForeignKey("investimentos.id"), index=True)
    valor: Mapped[float] = mapped_column(Float)
    data: Mapped[date] = mapped_column(Date)
    tipo: Mapped[str] = mapped_column(String(15))  # dividendo | rendimento


class AnaliseIA(Base):
    __tablename__ = "analises_ia"
    id: Mapped[int] = mapped_column(primary_key=True)
    investidor_id: Mapped[int] = mapped_column(ForeignKey("investidores.id"), index=True)
    snapshot: Mapped[dict] = mapped_column(JSON)
    resultado: Mapped[dict] = mapped_column(JSON)
    fonte: Mapped[str] = mapped_column(String(20))  # claude | regras-locais
    criada_em: Mapped[datetime] = mapped_column(DateTime, default=_agora)


class Proposta(Base):
    __tablename__ = "propostas"
    id: Mapped[int] = mapped_column(primary_key=True)
    investidor_id: Mapped[int] = mapped_column(ForeignKey("investidores.id"), index=True)
    consultor_id: Mapped[int] = mapped_column(ForeignKey("consultores.id"))
    analise_id: Mapped[int | None] = mapped_column(ForeignKey("analises_ia.id"), nullable=True)
    origem: Mapped[str] = mapped_column(String(15))  # consultor | ia
    status: Mapped[str] = mapped_column(String(25), default="pendente")
    justificativa: Mapped[str] = mapped_column(Text, default="")
    criada_em: Mapped[datetime] = mapped_column(DateTime, default=_agora)
    respondida_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ajustes: Mapped[list["Ajuste"]] = relationship(cascade="all, delete-orphan", order_by="Ajuste.id")


class Ajuste(Base):
    __tablename__ = "ajustes"
    id: Mapped[int] = mapped_column(primary_key=True)
    proposta_id: Mapped[int] = mapped_column(ForeignKey("propostas.id"), index=True)
    classe_de: Mapped[str] = mapped_column(String(15))
    classe_para: Mapped[str] = mapped_column(String(15))
    percentual: Mapped[float] = mapped_column(Float)
    aceito: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class Evento(Base):
    """Histórico de auditoria (RNF05)."""
    __tablename__ = "eventos"
    id: Mapped[int] = mapped_column(primary_key=True)
    investidor_id: Mapped[int] = mapped_column(ForeignKey("investidores.id"), index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(30))
    descricao: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_agora)
