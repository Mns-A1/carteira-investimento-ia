"""Regras de negócio puras (sem banco e sem FastAPI) — RN01..RN05 da spec.md.

Cada "item" é um dict: {"nome": str, "classe": str, "valor": float}.
"""
from datetime import date

CLASSE_POR_TIPO = {
    "tesouro_selic": "tesouro", "tesouro_ipca": "tesouro", "tesouro_educa": "tesouro",
    "cdb": "cdb_cdi", "cdi": "cdb_cdi", "acao": "acoes", "poupanca": "poupanca",
}
CLASSES = ("tesouro", "cdb_cdi", "acoes", "poupanca")
LIMITE_ACOES_POR_PERFIL = {"conservador": 10.0, "moderado": 30.0, "agressivo": 60.0}  # RN03
MIN_ATIVOS_PARA_CONCENTRACAO = 3  # com menos ativos, 40% por ativo é inviável


def classe_do_tipo(tipo: str) -> str:
    return CLASSE_POR_TIPO[tipo]


def status_efetivo(status_atual: str, data_vencimento: date | None, hoje: date | None = None) -> str:
    """RF03: o investimento expira ao atingir a data de vencimento."""
    if status_atual == "inativo":
        return "inativo"
    hoje = hoje or date.today()
    if data_vencimento is not None and hoje >= data_vencimento:
        return "expirado"
    return status_atual


def total(itens: list[dict]) -> float:
    return sum(i["valor"] for i in itens)


def alocacao_por_classe(itens: list[dict]) -> dict[str, float]:
    t = total(itens)
    aloc = {c: 0.0 for c in CLASSES}
    if t <= 0:
        return aloc
    for i in itens:
        aloc[i["classe"]] += i["valor"] / t * 100
    return {c: round(v, 2) for c, v in aloc.items()}


def concentracao_por_ativo(itens: list[dict]) -> dict[str, float]:
    t = total(itens)
    if t <= 0:
        return {}
    por_nome: dict[str, float] = {}
    rotulos: dict[str, str] = {}
    for i in itens:  # "ITUB3" e "itub3" são o mesmo ativo
        k = i["nome"].strip().casefold()
        rotulos.setdefault(k, i["nome"].strip())
        por_nome[k] = por_nome.get(k, 0.0) + i["valor"]
    return {rotulos[k]: round(v / t * 100, 2) for k, v in por_nome.items()}


def excede_concentracao(itens: list[dict], nome: str, valor_extra: float, limite: float) -> tuple[bool, float]:
    """RN02: o ativo ficaria acima do limite após receber valor_extra?"""
    conc = concentracao_por_ativo(itens + [{"nome": nome, "classe": "?", "valor": valor_extra}])
    pct = next((p for n, p in conc.items() if n.casefold() == nome.strip().casefold()), 0.0)
    return (len(conc) >= MIN_ATIVOS_PARA_CONCENTRACAO and pct > limite), pct


def alertas_concentracao(itens: list[dict], limite: float) -> list[dict]:
    conc = concentracao_por_ativo(itens)
    if len(conc) < MIN_ATIVOS_PARA_CONCENTRACAO:
        return []
    return [
        {"ativo": n, "percentual": p, "limite": limite, "status": "acima"}
        for n, p in sorted(conc.items(), key=lambda x: -x[1]) if p > limite
    ]


def projetar_alocacao(aloc: dict[str, float], ajustes: list[dict]) -> dict[str, float]:
    proj = dict(aloc)
    for a in ajustes:
        if proj[a["classe_de"]] + 1e-9 < a["percentual"]:
            raise ValueError(
                f"A classe '{a['classe_de']}' tem apenas {proj[a['classe_de']]:.2f}% da carteira; "
                f"não é possível mover {a['percentual']}%."
            )
        proj[a["classe_de"]] -= a["percentual"]
        proj[a["classe_para"]] += a["percentual"]
    return {c: round(v, 2) for c, v in proj.items()}


def validar_proposta(itens: list[dict], ajustes: list[dict], perfil_risco: str) -> tuple[bool, str, dict]:
    """RN03: a carteira resultante precisa respeitar o perfil de risco. Retorna (ok, motivo, projeção)."""
    aloc = alocacao_por_classe(itens)
    if total(itens) <= 0:
        return False, "A carteira não tem investimentos ativos.", aloc
    try:
        proj = projetar_alocacao(aloc, ajustes)
    except ValueError as e:
        return False, str(e), aloc
    limite = LIMITE_ACOES_POR_PERFIL[perfil_risco]
    if proj["acoes"] > limite + 1e-9:
        return False, (f"perfil {perfil_risco}: ações ficariam com {proj['acoes']:.2f}%, "
                       f"acima do máximo de {limite:.0f}%."), proj
    return True, "", proj


def calcular_score_risco(aloc: dict[str, float], conc: dict[str, float]) -> int:
    score = aloc["acoes"] * 1.2 + max(conc.values(), default=0.0) * 0.5
    return int(max(0, min(100, round(score))))


def analise_local(snapshot: dict) -> dict:
    """Análise determinística usada quando não há chave de IA configurada (modo local)."""
    itens = snapshot["investimentos"]
    perfil, limite = snapshot["perfil_risco"], snapshot["limite_concentracao"]
    aloc, conc = alocacao_por_classe(itens), concentracao_por_ativo(itens)
    sugestoes = []
    limite_acoes = LIMITE_ACOES_POR_PERFIL[perfil]
    if aloc["acoes"] > limite_acoes:
        excesso = round(aloc["acoes"] - limite_acoes, 2)
        sugestoes.append({
            "classe_de": "acoes", "classe_para": "tesouro", "percentual": excesso,
            "justificativa": f"Ações em {aloc['acoes']:.2f}% excedem o máximo de {limite_acoes:.0f}% do perfil {perfil}.",
        })
    return {
        "score_risco": calcular_score_risco(aloc, conc),
        "concentracao_alertas": alertas_concentracao(itens, limite),
        "sugestoes_rebalanceamento": sugestoes,
    }
