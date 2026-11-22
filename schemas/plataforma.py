from typing import List

from pydantic import BaseModel, Field

__all__ = [
    "PlataformaSchema", "PlataformaBuscaSchema",
    "PlataformaViewSchema", "ListagemPlataformasSchema",
]


class PlataformaSchema(BaseModel):
    """Dados para cadastrar ou alterar uma plataforma de reserva."""
    nome: str = Field(..., min_length=1, max_length=50, examples=["Vrbo"])
    taxa_comissao: float = Field(..., ge=0, le=100,
                                 description="Comissão cobrada pela plataforma, em %.",
                                 examples=[12.5])
    cor: str = Field("#6c757d", pattern=r"^#[0-9a-fA-F]{6}$",
                     description="Cor usada nos cards do front-end.", examples=["#1E90FF"])


class PlataformaBuscaSchema(BaseModel):
    """Identifica a plataforma pelo id."""
    id: int = Field(..., description="id da plataforma.")


class PlataformaViewSchema(BaseModel):
    id: int = Field(..., examples=[1])
    nome: str = Field(..., examples=["Airbnb"])
    taxa_comissao: float = Field(..., examples=[15.0])
    cor: str = Field(..., examples=["#FF5A5F"])


class ListagemPlataformasSchema(BaseModel):
    plataformas: List[PlataformaViewSchema]
