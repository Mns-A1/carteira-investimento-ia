"""Integração com a IA (ADR 0002). A IA classifica e sugere; o sistema valida e decide (RN04).

- Com ANTHROPIC_API_KEY: chama o Claude e valida o JSON retornado (RNF08).
- Sem chave: usa a análise local determinística e marca fonte="regras-locais".
- Falha/timeout da IA: levanta exceção -> a API responde 502 sem afetar o resto do sistema (RNF02).
"""
import json
import logging
import time
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from . import config, rules

log = logging.getLogger("carteira.ia")
ClasseLit = Literal["tesouro", "cdb_cdi", "acoes", "poupanca"]


class Alerta(BaseModel):
    ativo: str
    percentual: float
    limite: float
    status: Literal["acima", "dentro"]


class Sugestao(BaseModel):
    classe_de: ClasseLit
    classe_para: ClasseLit
    percentual: float = Field(gt=0, le=100)
    justificativa: str


class ResultadoAnalise(BaseModel):
    score_risco: int = Field(ge=0, le=100)
    concentracao_alertas: list[Alerta]
    sugestoes_rebalanceamento: list[Sugestao]


class IAIndisponivel(Exception):
    pass


class RespostaInvalida(Exception):
    pass


PROMPT_SISTEMA = """Você é um analista de risco de carteiras de investimento.
Receberá um JSON com o snapshot de uma carteira. Responda APENAS com um objeto JSON válido,
sem texto antes ou depois e sem markdown, exatamente neste formato:
{"score_risco": <inteiro 0-100>,
 "concentracao_alertas": [{"ativo": "<nome>", "percentual": <número>, "limite": <número>, "status": "acima"}],
 "sugestoes_rebalanceamento": [{"classe_de": "<classe>", "classe_para": "<classe>", "percentual": <número>, "justificativa": "<texto curto>"}]}
Regras: classes válidas: tesouro, cdb_cdi, acoes, poupanca. Em concentracao_alertas inclua apenas ativos
acima do campo limite_concentracao. As sugestões devem respeitar o campo limite_acoes_perfil (máximo de
ações da carteira após o ajuste). Percentuais são pontos percentuais da carteira total. No máximo 3 sugestões."""


def _extrair_json(texto: str) -> str:
    texto = texto.strip().replace("```json", "").replace("```", "")
    ini, fim = texto.find("{"), texto.rfind("}")
    if ini == -1 or fim == -1:
        raise RespostaInvalida("a resposta não contém um objeto JSON")
    return texto[ini:fim + 1]


def validar_resposta(texto: str) -> ResultadoAnalise:
    try:
        return ResultadoAnalise.model_validate(json.loads(_extrair_json(texto)))
    except (ValueError, ValidationError) as e:  # json.JSONDecodeError é ValueError
        raise RespostaInvalida(str(e)) from e


def analisar_com_claude(snapshot: dict) -> ResultadoAnalise:
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, timeout=30.0, max_retries=1)
        msg = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1000,
            system=PROMPT_SISTEMA,
            messages=[{"role": "user", "content": json.dumps(snapshot, ensure_ascii=False)}],
        )
        texto = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    except Exception as e:
        raise IAIndisponivel(str(e)) from e
    return validar_resposta(texto)


def analisar(snapshot: dict) -> tuple[ResultadoAnalise, str]:
    inicio = time.perf_counter()
    if not config.ANTHROPIC_API_KEY:
        resultado, fonte = ResultadoAnalise.model_validate(rules.analise_local(snapshot)), "regras-locais"
    else:
        resultado, fonte = analisar_com_claude(snapshot), "claude"
    log.info("análise concluída fonte=%s duração=%.0fms", fonte, (time.perf_counter() - inicio) * 1000)
    return resultado, fonte
