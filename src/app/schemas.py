from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

TipoInvestimento = Literal["tesouro_selic", "tesouro_ipca", "tesouro_educa", "cdb", "cdi", "acao", "poupanca"]
Classe = Literal["tesouro", "cdb_cdi", "acoes", "poupanca"]
PerfilRisco = Literal["conservador", "moderado", "agressivo"]
EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegistroIn(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: str = Field(pattern=EMAIL, max_length=160)
    senha: str = Field(min_length=6, max_length=72)
    perfil: Literal["investidor", "consultor"]
    perfil_risco: PerfilRisco = "moderado"


class TokenOut(BaseModel):
    access_token: str
    token_type: str
    perfil: str


class InvestimentoIn(BaseModel):
    tipo: TipoInvestimento
    nome: str = Field(min_length=1, max_length=120, strip_whitespace=True, description="Ex.: ITUB3, Tesouro Selic 2029, CDB Banco Inter")
    valor_aplicado: float = Field(gt=0)
    data_aplicacao: date
    data_vencimento: date | None = None


class AporteIn(BaseModel):
    valor: float = Field(gt=0)


class GanhoIn(BaseModel):
    investimento_id: int
    valor: float = Field(gt=0)
    data: date
    tipo: Literal["dividendo", "rendimento"]


class VinculoIn(BaseModel):
    email_consultor: str = Field(pattern=EMAIL)


class PerfilRiscoIn(BaseModel):
    perfil_risco: PerfilRisco


class LimiteIn(BaseModel):
    limite_concentracao: float = Field(gt=0, le=100)


class AjusteIn(BaseModel):
    classe_de: Classe
    classe_para: Classe
    percentual: float = Field(gt=0, le=100)

    @model_validator(mode="after")
    def _classes_diferentes(self):
        if self.classe_de == self.classe_para:
            raise ValueError("classe_de e classe_para devem ser diferentes")
        return self


class PropostaIn(BaseModel):
    investidor_id: int
    justificativa: str = Field(min_length=3)
    ajustes: list[AjusteIn] = Field(min_length=1)


class PropostaDeAnaliseIn(BaseModel):
    indices: list[int] | None = Field(default=None, description="Quais sugestões usar (padrão: todas)")


class RespostaPropostaIn(BaseModel):
    decisao: Literal["aceitar", "recusar", "parcial"]
    ajustes_aceitos: list[int] | None = Field(default=None, description="IDs dos ajustes aceitos (decisão 'parcial')")
