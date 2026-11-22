from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

__all__ = [
    "CategoriaDespesa", "DespesaSchema", "DespesaBuscaSchema", "DespesaFiltroSchema",
    "DespesaViewSchema", "ListagemDespesasSchema",
]

CategoriaDespesa = Literal[
    "manutencao", "limpeza", "contas", "impostos", "condominio", "enxoval", "outros"
]


class DespesaSchema(BaseModel):
    """Dados para cadastrar ou alterar uma despesa da casa."""
    data: date = Field(..., description="Data do gasto (AAAA-MM-DD).", examples=["2027-01-13"])
    categoria: CategoriaDespesa = Field(..., examples=["limpeza"])
    descricao: str = Field(..., min_length=1, max_length=200, examples=["Faxina pós check-out"])
    valor: float = Field(..., gt=0, description="Valor em R$.", examples=[180.0])
    reserva_id: Optional[int] = Field(None, description="Opcional: liga a despesa a uma reserva.",
                                      examples=[1])


class DespesaBuscaSchema(BaseModel):
    """Identifica a despesa pelo id."""
    id: int = Field(..., examples=[1])


class DespesaFiltroSchema(BaseModel):
    """Filtros opcionais da listagem de despesas."""
    ano: Optional[int] = Field(None, ge=2000, le=2100, examples=[2027])
    mes: Optional[int] = Field(None, ge=1, le=12, examples=[1])
    categoria: Optional[CategoriaDespesa] = None

    @model_validator(mode="after")
    def mes_exige_ano(self):
        if self.mes and not self.ano:
            raise ValueError("Para filtrar por mês, informe também o ano.")
        return self


class DespesaViewSchema(BaseModel):
    id: int = Field(..., examples=[1])
    data: date = Field(..., examples=["2027-01-13"])
    categoria: CategoriaDespesa = Field(..., examples=["limpeza"])
    descricao: str = Field(..., examples=["Faxina pós check-out"])
    valor: float = Field(..., examples=[180.0])
    reserva_id: Optional[int] = Field(None, examples=[1])
    reserva_hospede: Optional[str] = Field(None, examples=["Mariana Souza"])


class ListagemDespesasSchema(BaseModel):
    despesas: List[DespesaViewSchema]
