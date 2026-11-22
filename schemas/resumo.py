from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

__all__ = ["ResumoBuscaSchema", "ResumoViewSchema"]


class ResumoBuscaSchema(BaseModel):
    """Período do resumo. Sem mês, o resumo é do ano inteiro."""
    ano: int = Field(..., ge=2000, le=2100, examples=[2027])
    mes: Optional[int] = Field(None, ge=1, le=12, examples=[1])


class ResumoPlataformaSchema(BaseModel):
    plataforma: str = Field(..., examples=["Airbnb"])
    cor: str = Field(..., examples=["#FF5A5F"])
    reservas: int = Field(..., examples=[3])
    noites: int = Field(..., examples=[11])
    receita_bruta: float = Field(..., examples=[8400.0])
    comissoes: float = Field(..., examples=[1260.0])
    receita_liquida: float = Field(..., examples=[7140.0])


class ResumoCategoriaSchema(BaseModel):
    categoria: str = Field(..., examples=["manutencao"])
    total: float = Field(..., examples=[950.0])


class ResumoViewSchema(BaseModel):
    ano: int = Field(..., examples=[2027])
    mes: Optional[int] = Field(None, examples=[1])
    periodo_inicio: date = Field(..., examples=["2027-01-01"])
    periodo_fim: date = Field(..., examples=["2027-01-31"])
    receita_bruta: float = Field(..., examples=[12500.0])
    comissoes: float = Field(..., examples=[1500.0])
    receita_liquida: float = Field(..., examples=[11000.0])
    despesas: float = Field(..., examples=[2300.0])
    resultado: float = Field(..., description="Receita líquida menos despesas.", examples=[8700.0])
    situacao: Literal["lucro", "prejuizo", "equilibrio"] = Field(..., examples=["lucro"])
    reservas_confirmadas: int = Field(..., examples=[5])
    noites_ocupadas: int = Field(..., examples=[19])
    dias_no_periodo: int = Field(..., examples=[31])
    taxa_ocupacao: float = Field(..., description="Noites ocupadas / dias do período, em %.",
                                 examples=[61.3])
    por_plataforma: List[ResumoPlataformaSchema]
    despesas_por_categoria: List[ResumoCategoriaSchema]
