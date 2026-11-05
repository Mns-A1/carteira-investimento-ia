from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, services
from ..database import get_db
from ..schemas import (AporteIn, GanhoIn, InvestimentoIn, PerfilRiscoIn, RespostaPropostaIn, VinculoIn)
from ..security import investidor_atual

router = APIRouter(tags=["Investidor"])


@router.get("/carteira")
def ver_carteira(inv: models.Investidor = Depends(investidor_atual), db: Session = Depends(get_db)):
    """Visão consolidada: alocação por classe, % por investimento e alertas de concentração (RF02)."""
    return services.consolidado(db, inv)


@router.post("/investimentos", status_code=201)
def registrar_investimento(dados: InvestimentoIn, inv: models.Investidor = Depends(investidor_atual),
                           db: Session = Depends(get_db)):
    """RF01 — o percentual é calculado automaticamente sobre a carteira."""
    novo = services.novo_investimento(db, inv, inv.usuario_id, dados)
    return {"id": novo.id, "nome": novo.nome, "status": novo.status}


@router.post("/investimentos/{investimento_id}/aportes")
def novo_aporte(investimento_id: int, dados: AporteIn, inv: models.Investidor = Depends(investidor_atual),
                db: Session = Depends(get_db)):
    """RN01 (status) e RN02 (concentração) são verificadas aqui."""
    i = services.aportar(db, inv, inv.usuario_id, investimento_id, dados.valor)
    return {"id": i.id, "nome": i.nome, "valor_aplicado": i.valor_aplicado}


@router.patch("/investimentos/{investimento_id}/inativar")
def inativar(investimento_id: int, inv: models.Investidor = Depends(investidor_atual), db: Session = Depends(get_db)):
    i = services.investimento_do(db, inv, investimento_id)
    i.status = "inativo"
    services.registrar_evento(db, inv.id, inv.usuario_id, "status", f"'{i.nome}' (#{i.id}) marcado como inativo.")
    db.commit()
    return {"id": i.id, "status": i.status}


@router.delete("/investimentos/{investimento_id}", status_code=204)
def remover_investimento(investimento_id: int, inv: models.Investidor = Depends(investidor_atual),
                         db: Session = Depends(get_db)):
    """RF05 — só sem aplicação ativa; os ganhos já registrados continuam aparecendo."""
    services.atualizar_status(db, inv)
    i = services.investimento_do(db, inv, investimento_id)
    if i.status == "ativo":
        raise HTTPException(409, "Investimento ativo não pode ser removido. Marque-o como inativo primeiro.")
    i.removido = True
    services.registrar_evento(db, inv.id, inv.usuario_id, "remocao", f"'{i.nome}' (#{i.id}) removido da carteira.")
    db.commit()


@router.post("/ganhos", status_code=201)
def registrar_ganho(dados: GanhoIn, inv: models.Investidor = Depends(investidor_atual), db: Session = Depends(get_db)):
    """RF06"""
    i = services.investimento_do(db, inv, dados.investimento_id)
    g = models.Ganho(investimento_id=i.id, valor=dados.valor, data=dados.data, tipo=dados.tipo)
    db.add(g)
    services.registrar_evento(db, inv.id, inv.usuario_id, "ganho", f"Ganho de R$ {dados.valor:.2f} em '{i.nome}'.")
    db.commit()
    return {"id": g.id}


@router.get("/ganhos/resumo")
def resumo_ganhos(mes: str | None = Query(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="AAAA-MM (padrão: mês atual)"),
                  inv: models.Investidor = Depends(investidor_atual), db: Session = Depends(get_db)):
    """RF07 — total por ativo e consolidado no mês."""
    hoje = date.today()
    ano, m = (hoje.year, hoje.month) if mes is None else (int(mes[:4]), int(mes[5:]))
    ini, fim = date(ano, m, 1), date(ano + (m == 12), m % 12 + 1, 1)
    invs = {i.id: i for i in services.investimentos(db, inv, incluir_removidos=True)}
    ganhos = db.query(models.Ganho).filter(models.Ganho.investimento_id.in_(list(invs) or [0]),
                                           models.Ganho.data >= ini, models.Ganho.data < fim).all()
    por_ativo: dict[int, float] = {}
    for g in ganhos:
        por_ativo[g.investimento_id] = por_ativo.get(g.investimento_id, 0.0) + g.valor
    return {"mes": f"{ano:04d}-{m:02d}", "total_consolidado": round(sum(por_ativo.values()), 2),
            "por_ativo": [{"investimento_id": k, "nome": invs[k].nome, "removido": invs[k].removido, "total": round(v, 2)}
                          for k, v in por_ativo.items()]}


@router.put("/vinculo")
def vincular_consultor(dados: VinculoIn, inv: models.Investidor = Depends(investidor_atual), db: Session = Depends(get_db)):
    """O investidor autoriza um Consultor a acompanhar sua carteira (RF08 / RN05)."""
    u = db.query(models.Usuario).filter_by(email=dados.email_consultor.lower(), perfil="consultor").first()
    if not u:
        raise HTTPException(404, "Consultor não encontrado.")
    inv.consultor_id = db.query(models.Consultor).filter_by(usuario_id=u.id).one().id
    services.registrar_evento(db, inv.id, inv.usuario_id, "vinculo", f"Vinculado ao consultor {u.nome}.")
    db.commit()
    return {"consultor": u.nome}


@router.delete("/vinculo", status_code=204)
def desvincular_consultor(inv: models.Investidor = Depends(investidor_atual), db: Session = Depends(get_db)):
    inv.consultor_id = None
    services.registrar_evento(db, inv.id, inv.usuario_id, "vinculo", "Vínculo com o consultor removido.")
    db.commit()


@router.patch("/perfil-risco")
def alterar_perfil_risco(dados: PerfilRiscoIn, inv: models.Investidor = Depends(investidor_atual),
                         db: Session = Depends(get_db)):
    inv.perfil_risco = dados.perfil_risco
    services.registrar_evento(db, inv.id, inv.usuario_id, "perfil", f"Perfil de risco alterado para {dados.perfil_risco}.")
    db.commit()
    return {"perfil_risco": inv.perfil_risco}


@router.post("/analise")
def analisar_minha_carteira(inv: models.Investidor = Depends(investidor_atual), db: Session = Depends(get_db)):
    """RF14 — score de risco, alertas e sugestões (JSON validado). Não altera a carteira (RN04)."""
    return services.analise_out(services.executar_analise(db, inv, inv.usuario_id))


@router.get("/propostas")
def minhas_propostas(inv: models.Investidor = Depends(investidor_atual), db: Session = Depends(get_db)):
    ps = db.query(models.Proposta).filter_by(investidor_id=inv.id).order_by(models.Proposta.id.desc()).all()
    return [services.proposta_out(p) for p in ps]


@router.post("/propostas/{proposta_id}/responder")
def responder_proposta(proposta_id: int, dados: RespostaPropostaIn, inv: models.Investidor = Depends(investidor_atual),
                       db: Session = Depends(get_db)):
    """RF11–RF13 — aceitar, recusar ou aceitar parcialmente."""
    p = db.get(models.Proposta, proposta_id)
    if not p or p.investidor_id != inv.id:
        raise HTTPException(404, "Proposta não encontrada.")
    return services.proposta_out(services.responder_proposta(db, inv, inv.usuario_id, p, dados.decisao, dados.ajustes_aceitos))


@router.get("/historico")
def historico(inv: models.Investidor = Depends(investidor_atual), db: Session = Depends(get_db)):
    """RNF05 — trilha de auditoria."""
    es = db.query(models.Evento).filter_by(investidor_id=inv.id).order_by(models.Evento.id.desc()).limit(100).all()
    return [{"quando": e.criado_em, "tipo": e.tipo, "descricao": e.descricao} for e in es]
