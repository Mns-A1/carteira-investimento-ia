"""Camada de regras de negócio aplicadas ao banco (RF01–RF16, RN01–RN05)."""
import logging
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import ai, models, rules

log = logging.getLogger("carteira.regras")

DESTINO_PADRAO = {
    "tesouro": ("tesouro_selic", "Tesouro Selic"), "cdb_cdi": ("cdb", "CDB"),
    "acoes": ("acao", "Ações (rebalanceamento)"), "poupanca": ("poupanca", "Poupança"),
}


def agora() -> datetime:
    return datetime.now(timezone.utc)


def registrar_evento(db: Session, investidor_id: int, usuario_id: int | None, tipo: str, descricao: str) -> None:
    db.add(models.Evento(investidor_id=investidor_id, usuario_id=usuario_id, tipo=tipo, descricao=descricao))


def carteira_de(db: Session, investidor: models.Investidor) -> models.Carteira:
    return db.query(models.Carteira).filter_by(investidor_id=investidor.id).one()


def investimentos(db: Session, investidor: models.Investidor, incluir_removidos: bool = False) -> list[models.Investimento]:
    q = db.query(models.Investimento).filter_by(carteira_id=carteira_de(db, investidor).id)
    if not incluir_removidos:
        q = q.filter_by(removido=False)
    return q.order_by(models.Investimento.id).all()


def investimento_do(db: Session, investidor: models.Investidor, inv_id: int) -> models.Investimento:
    inv = db.get(models.Investimento, inv_id)
    if not inv or inv.removido or inv.carteira_id != carteira_de(db, investidor).id:
        raise HTTPException(404, "Investimento não encontrado.")  # RNF04
    return inv


def atualizar_status(db: Session, investidor: models.Investidor) -> None:
    """RF03: investimentos que atingiram o vencimento passam a 'expirado'."""
    mudou = False
    for inv in investimentos(db, investidor):
        novo = rules.status_efetivo(inv.status, inv.data_vencimento)
        if novo != inv.status:
            inv.status = novo
            mudou = True
            registrar_evento(db, investidor.id, None, "status", f"'{inv.nome}' (#{inv.id}) passou para '{novo}'.")
    if mudou:
        db.commit()


def itens_ativos(invs: list[models.Investimento]) -> list[dict]:
    return [{"id": i.id, "nome": i.nome, "classe": rules.classe_do_tipo(i.tipo), "valor": i.valor_aplicado}
            for i in invs if i.status == "ativo" and i.valor_aplicado > 0]


def consolidado(db: Session, investidor: models.Investidor) -> dict:
    """RF02 (sem 'valores retirados': o MVP não registra retiradas)."""
    atualizar_status(db, investidor)
    invs = investimentos(db, investidor)
    itens = itens_ativos(invs)
    t = rules.total(itens)
    return {
        "perfil_risco": investidor.perfil_risco,
        "limite_concentracao": investidor.limite_concentracao,
        "total_ativo": round(t, 2),
        "alocacao_por_classe": rules.alocacao_por_classe(itens),
        "alertas_concentracao": rules.alertas_concentracao(itens, investidor.limite_concentracao),
        "investimentos": [{
            "id": i.id, "tipo": i.tipo, "classe": rules.classe_do_tipo(i.tipo), "nome": i.nome,
            "valor_aplicado": i.valor_aplicado, "data_aplicacao": i.data_aplicacao,
            "data_vencimento": i.data_vencimento, "status": i.status, "bloqueado": i.bloqueado,
            "percentual": round(i.valor_aplicado / t * 100, 2) if (i.status == "ativo" and t > 0) else 0.0,
        } for i in invs],
    }


def checar_concentracao(db: Session, investidor: models.Investidor, nome: str, valor: float) -> None:
    """RN02/RF15: bloqueia aporte que estoura o limite e trava o ativo até revisão do Consultor."""
    invs = investimentos(db, investidor)
    mesmos = [i for i in invs if i.nome.strip().casefold() == nome.strip().casefold() and i.status == "ativo"]
    if any(i.bloqueado for i in mesmos):
        raise HTTPException(409, f"O ativo '{nome}' está bloqueado por concentração até revisão do Consultor (RN02).")
    excede, pct = rules.excede_concentracao(itens_ativos(invs), nome, valor, investidor.limite_concentracao)
    if excede:
        log.warning("aporte recusado por concentração: ativo=%s pct=%.2f limite=%.0f investidor=%s",
                    nome, pct, investidor.limite_concentracao, investidor.id)
        for i in mesmos:
            i.bloqueado = True
        registrar_evento(db, investidor.id, None, "bloqueio",
                         f"Aporte em '{nome}' recusado: ficaria com {pct:.2f}% (limite {investidor.limite_concentracao:.0f}%).")
        db.commit()
        raise HTTPException(409, f"Aporte recusado: '{nome}' ficaria com {pct:.2f}% da carteira, acima do limite de "
                                 f"{investidor.limite_concentracao:.0f}%. Novos aportes ficam bloqueados até revisão do Consultor (RN02).")


def novo_investimento(db: Session, investidor: models.Investidor, usuario_id: int, dados) -> models.Investimento:
    if dados.data_vencimento is not None and dados.data_vencimento <= date.today():
        raise HTTPException(422, "A data de vencimento deve ser futura.")
    atualizar_status(db, investidor)
    checar_concentracao(db, investidor, dados.nome, dados.valor_aplicado)
    inv = models.Investimento(
        carteira_id=carteira_de(db, investidor).id, tipo=dados.tipo, nome=dados.nome,
        valor_aplicado=dados.valor_aplicado, data_aplicacao=dados.data_aplicacao, data_vencimento=dados.data_vencimento)
    db.add(inv)
    registrar_evento(db, investidor.id, usuario_id, "aplicacao", f"Novo investimento '{dados.nome}': R$ {dados.valor_aplicado:.2f}.")
    db.commit()
    return inv


def aportar(db: Session, investidor: models.Investidor, usuario_id: int, inv_id: int, valor: float) -> models.Investimento:
    atualizar_status(db, investidor)
    inv = investimento_do(db, investidor, inv_id)
    if inv.status != "ativo":  # RN01
        raise HTTPException(409, f"Investimento '{inv.nome}' está {inv.status}: novos aportes não são permitidos (RN01).")
    checar_concentracao(db, investidor, inv.nome, valor)
    inv.valor_aplicado = round(inv.valor_aplicado + valor, 2)
    registrar_evento(db, investidor.id, usuario_id, "aporte", f"Aporte de R$ {valor:.2f} em '{inv.nome}'.")
    db.commit()
    return inv


# ---------- Propostas de rebalanceamento ----------
def _aj(a) -> dict:
    return {"classe_de": a.classe_de, "classe_para": a.classe_para, "percentual": a.percentual}


def criar_proposta(db, investidor, consultor, ajustes, justificativa, origem, analise_id=None) -> models.Proposta:
    atualizar_status(db, investidor)
    ok, motivo, _ = rules.validar_proposta(itens_ativos(investimentos(db, investidor)), [_aj(a) for a in ajustes],
                                           investidor.perfil_risco)
    if not ok:  # RF10 / RN03
        raise HTTPException(422, f"Proposta bloqueada (RN03): {motivo}")
    p = models.Proposta(investidor_id=investidor.id, consultor_id=consultor.id, analise_id=analise_id,
                        origem=origem, justificativa=justificativa)
    p.ajustes = [models.Ajuste(**_aj(a)) for a in ajustes]
    db.add(p)
    registrar_evento(db, investidor.id, consultor.usuario_id, "proposta", f"Proposta ({origem}) enviada ao investidor.")
    db.commit()
    return p


def aplicar_ajustes(db, investidor, ajustes, usuario_id) -> None:
    for a in ajustes:
        ativos = [i for i in investimentos(db, investidor) if i.status == "ativo"]
        valor = round(sum(i.valor_aplicado for i in ativos) * a.percentual / 100, 2)
        origem = [i for i in ativos if rules.classe_do_tipo(i.tipo) == a.classe_de]
        disponivel = sum(i.valor_aplicado for i in origem)
        if valor > disponivel + 0.01:
            raise HTTPException(409, f"A classe '{a.classe_de}' não tem saldo suficiente para o ajuste.")
        for i in origem:
            i.valor_aplicado = max(0.0, round(i.valor_aplicado - valor * i.valor_aplicado / disponivel, 2))
        destino = next((i for i in ativos if rules.classe_do_tipo(i.tipo) == a.classe_para and not i.bloqueado), None)
        if destino is None:
            tipo, nome = DESTINO_PADRAO[a.classe_para]
            destino = models.Investimento(carteira_id=carteira_de(db, investidor).id, tipo=tipo, nome=nome,
                                          valor_aplicado=0.0, data_aplicacao=date.today())
            db.add(destino)
        destino.valor_aplicado = round(destino.valor_aplicado + valor, 2)
        registrar_evento(db, investidor.id, usuario_id, "rebalanceamento",
                         f"Movidos R$ {valor:.2f} ({a.percentual}%) de '{a.classe_de}' para '{a.classe_para}'.")
        db.flush()


def responder_proposta(db, investidor, usuario_id, proposta, decisao, ids_aceitos) -> models.Proposta:
    if proposta.status != "pendente":
        raise HTTPException(409, f"A proposta já foi respondida ({proposta.status}).")
    atualizar_status(db, investidor)
    todos = list(proposta.ajustes)
    if decisao == "recusar":  # RF13
        for a in todos:
            a.aceito = False
        proposta.status = "recusada"
    else:  # RF11 / RF12
        if decisao == "aceitar":
            aceitos = todos
        else:
            ids = set(ids_aceitos or [])
            if not ids or not ids <= {a.id for a in todos}:
                raise HTTPException(422, "Informe em 'ajustes_aceitos' ao menos um ID de ajuste desta proposta.")
            aceitos = [a for a in todos if a.id in ids]
        ok, motivo, _ = rules.validar_proposta(itens_ativos(investimentos(db, investidor)),
                                               [_aj(a) for a in aceitos], investidor.perfil_risco)
        if not ok:
            raise HTTPException(409, f"A carteira mudou e o ajuste não é mais permitido (RN03): {motivo}")
        aplicar_ajustes(db, investidor, aceitos, usuario_id)
        for a in todos:
            a.aceito = a in aceitos
        proposta.status = "aceita" if len(aceitos) == len(todos) else "aceita_parcialmente"
    proposta.respondida_em = agora()
    registrar_evento(db, investidor.id, usuario_id, "resposta_proposta", f"Proposta #{proposta.id}: {proposta.status}.")
    db.commit()
    return proposta


def proposta_out(p: models.Proposta) -> dict:
    return {"id": p.id, "investidor_id": p.investidor_id, "origem": p.origem, "status": p.status,
            "justificativa": p.justificativa, "criada_em": p.criada_em, "respondida_em": p.respondida_em,
            "analise_id": p.analise_id,
            "ajustes": [{"id": a.id, "classe_de": a.classe_de, "classe_para": a.classe_para,
                         "percentual": a.percentual, "aceito": a.aceito} for a in p.ajustes]}


# ---------- Análise por IA ----------
def executar_analise(db, investidor, usuario_id) -> models.AnaliseIA:
    atualizar_status(db, investidor)
    itens = itens_ativos(investimentos(db, investidor))
    if not itens:
        raise HTTPException(422, "A carteira não tem investimentos ativos para analisar.")
    t = rules.total(itens)
    snapshot = {
        "perfil_risco": investidor.perfil_risco, "limite_concentracao": investidor.limite_concentracao,
        "limite_acoes_perfil": rules.LIMITE_ACOES_POR_PERFIL[investidor.perfil_risco], "total": round(t, 2),
        "alocacao_por_classe": rules.alocacao_por_classe(itens),
        "investimentos": [{"nome": i["nome"], "classe": i["classe"], "valor": i["valor"],
                           "percentual": round(i["valor"] / t * 100, 2)} for i in itens],
    }
    try:
        resultado, fonte = ai.analisar(snapshot)
    except ai.IAIndisponivel as e:  # RNF02
        log.error("IA indisponível (investidor=%s): %s", investidor.id, e)
        raise HTTPException(502, f"Serviço de IA indisponível: {e}")
    except ai.RespostaInvalida as e:  # RNF08
        log.error("resposta da IA descartada (investidor=%s): %s", investidor.id, e)
        raise HTTPException(502, f"A IA retornou uma resposta fora do formato esperado e ela foi descartada: {e}")
    analise = models.AnaliseIA(investidor_id=investidor.id, snapshot=snapshot, resultado=resultado.model_dump(), fonte=fonte)
    db.add(analise)
    registrar_evento(db, investidor.id, usuario_id, "analise", f"Análise de carteira gerada (fonte: {fonte}).")
    db.commit()
    return analise


def analise_out(a: models.AnaliseIA) -> dict:
    return {"id": a.id, "fonte": a.fonte, "criada_em": a.criada_em, "resultado": a.resultado,
            "aviso": "A análise é apenas insumo: nada é alterado na carteira sem uma proposta aceita pelo investidor (RN04)."}


def proposta_de_analise(db, consultor, analise: models.AnaliseIA, indices) -> models.Proposta:
    investidor = db.get(models.Investidor, analise.investidor_id)
    sugestoes = analise.resultado["sugestoes_rebalanceamento"]
    if indices is not None:
        if any(i < 0 or i >= len(sugestoes) for i in indices):
            raise HTTPException(422, "Índice de sugestão inexistente.")
        sugestoes = [sugestoes[i] for i in indices]
    if not sugestoes:
        raise HTTPException(422, "A análise não trouxe sugestões de rebalanceamento.")
    ajustes = [models.Ajuste(classe_de=s["classe_de"], classe_para=s["classe_para"], percentual=s["percentual"])
               for s in sugestoes]
    justificativa = " | ".join(s["justificativa"] for s in sugestoes)
    return criar_proposta(db, investidor, consultor, ajustes, justificativa, "ia", analise.id)
