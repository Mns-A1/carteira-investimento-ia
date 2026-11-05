from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, services
from ..database import get_db
from ..schemas import LimiteIn, PropostaDeAnaliseIn, PropostaIn
from ..security import consultor_atual

router = APIRouter(prefix="/consultor", tags=["Consultor"])


def _investidor_vinculado(db: Session, consultor: models.Consultor, investidor_id: int) -> models.Investidor:
    inv = db.get(models.Investidor, investidor_id)
    if not inv or inv.consultor_id != consultor.id:
        raise HTTPException(403, "Investidor não vinculado a você (RN05).")
    return inv


@router.get("/investidores")
def listar_investidores(c: models.Consultor = Depends(consultor_atual), db: Session = Depends(get_db)):
    """RF08"""
    rows = (db.query(models.Investidor, models.Usuario).join(models.Usuario, models.Usuario.id == models.Investidor.usuario_id)
            .filter(models.Investidor.consultor_id == c.id).all())
    return [{"id": i.id, "nome": u.nome, "perfil_risco": i.perfil_risco, "limite_concentracao": i.limite_concentracao}
            for i, u in rows]


@router.get("/investidores/{investidor_id}/carteira")
def carteira_do_investidor(investidor_id: int, c: models.Consultor = Depends(consultor_atual), db: Session = Depends(get_db)):
    return services.consolidado(db, _investidor_vinculado(db, c, investidor_id))


@router.patch("/investidores/{investidor_id}/limite")
def definir_limite(investidor_id: int, dados: LimiteIn, c: models.Consultor = Depends(consultor_atual),
                   db: Session = Depends(get_db)):
    """RN02 — limite de concentração configurável por investidor."""
    inv = _investidor_vinculado(db, c, investidor_id)
    inv.limite_concentracao = dados.limite_concentracao
    services.registrar_evento(db, inv.id, c.usuario_id, "limite", f"Limite de concentração definido em {dados.limite_concentracao:.0f}%.")
    db.commit()
    return {"limite_concentracao": inv.limite_concentracao}


@router.post("/investimentos/{investimento_id}/liberar")
def liberar_ativo(investimento_id: int, c: models.Consultor = Depends(consultor_atual), db: Session = Depends(get_db)):
    """RF15 — revisão do Consultor que libera novos aportes em um ativo bloqueado."""
    i = db.get(models.Investimento, investimento_id)
    carteira = db.get(models.Carteira, i.carteira_id) if i else None
    if not i or i.removido:
        raise HTTPException(404, "Investimento não encontrado.")
    inv = _investidor_vinculado(db, c, carteira.investidor_id)
    i.bloqueado = False
    services.registrar_evento(db, inv.id, c.usuario_id, "liberacao", f"Ativo '{i.nome}' liberado pelo consultor.")
    db.commit()
    return {"id": i.id, "bloqueado": i.bloqueado}


@router.post("/investidores/{investidor_id}/analise")
def analisar_carteira(investidor_id: int, c: models.Consultor = Depends(consultor_atual), db: Session = Depends(get_db)):
    """RF14"""
    inv = _investidor_vinculado(db, c, investidor_id)
    return services.analise_out(services.executar_analise(db, inv, c.usuario_id))


@router.post("/propostas", status_code=201)
def criar_proposta(dados: PropostaIn, c: models.Consultor = Depends(consultor_atual), db: Session = Depends(get_db)):
    """RF09/RF10 — bloqueada automaticamente se fugir do perfil de risco."""
    inv = _investidor_vinculado(db, c, dados.investidor_id)
    p = services.criar_proposta(db, inv, c, dados.ajustes, dados.justificativa, "consultor")
    return services.proposta_out(p)


@router.post("/analises/{analise_id}/proposta", status_code=201)
def proposta_a_partir_da_analise(analise_id: int, dados: PropostaDeAnaliseIn | None = None,
                                 c: models.Consultor = Depends(consultor_atual), db: Session = Depends(get_db)):
    """RF16 — a sugestão da IA vira apenas uma proposta pendente; o investidor decide."""
    a = db.get(models.AnaliseIA, analise_id)
    if not a:
        raise HTTPException(404, "Análise não encontrada.")
    _investidor_vinculado(db, c, a.investidor_id)
    return services.proposta_out(services.proposta_de_analise(db, c, a, dados.indices if dados else None))


@router.get("/propostas")
def propostas_enviadas(c: models.Consultor = Depends(consultor_atual), db: Session = Depends(get_db)):
    """RF13 — o consultor acompanha aceites e recusas."""
    ps = db.query(models.Proposta).filter_by(consultor_id=c.id).order_by(models.Proposta.id.desc()).all()
    return [services.proposta_out(p) for p in ps]
