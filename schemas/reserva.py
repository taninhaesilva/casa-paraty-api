from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

__all__ = [
    "StatusReserva", "ReservaSchema", "ReservaBuscaSchema", "ReservaFiltroSchema",
    "ReservaViewSchema", "ListagemReservasSchema",
]

StatusReserva = Literal["confirmada", "cancelada"]


class ReservaSchema(BaseModel):
    """Dados para cadastrar ou alterar uma reserva."""
    hospede: str = Field(..., min_length=1, max_length=100, examples=["Mariana Souza"])
    plataforma_id: int = Field(..., description="id da plataforma (veja GET /plataformas).",
                               examples=[1])
    check_in: date = Field(..., description="Data de entrada (AAAA-MM-DD).", examples=["2027-01-08"])
    check_out: date = Field(..., description="Data de saída (AAAA-MM-DD).", examples=["2027-01-12"])
    num_hospedes: int = Field(1, ge=1, le=20, examples=[4])
    valor_bruto: float = Field(..., gt=0, description="Valor total pago pelo hóspede, em R$.",
                               examples=[3200.00])
    status: StatusReserva = Field("confirmada", examples=["confirmada"])
    observacao: Optional[str] = Field(None, max_length=500, examples=["Chegam tarde, deixar chave no cofre."])

    @model_validator(mode="after")
    def validar_datas(self):
        if self.check_out <= self.check_in:
            raise ValueError("O check-out deve ser depois do check-in.")
        return self


class ReservaBuscaSchema(BaseModel):
    """Identifica a reserva pelo id."""
    id: int = Field(..., description="id da reserva.")


class ReservaFiltroSchema(BaseModel):
    """Filtros opcionais da listagem. Com ano (e mês), traz as estadias daquele período."""
    ano: Optional[int] = Field(None, ge=2000, le=2100, description="Ano, ex.: 2027.")
    mes: Optional[int] = Field(None, ge=1, le=12, description="Mês de 1 a 12 (exige o ano).")
    plataforma_id: Optional[int] = Field(None, description="id da plataforma.")
    status: Optional[StatusReserva] = Field(None, description="confirmada ou cancelada.")

    @model_validator(mode="after")
    def mes_exige_ano(self):
        if self.mes and not self.ano:
            raise ValueError("Para filtrar por mês, informe também o ano.")
        return self


class ReservaViewSchema(BaseModel):
    id: int = Field(..., examples=[1])
    hospede: str = Field(..., examples=["Mariana Souza"])
    plataforma_id: int = Field(..., examples=[1])
    plataforma_nome: str = Field(..., examples=["Airbnb"])
    plataforma_cor: str = Field(..., examples=["#FF5A5F"])
    check_in: date = Field(..., examples=["2027-01-08"])
    check_out: date = Field(..., examples=["2027-01-12"])
    noites: int = Field(..., examples=[4])
    num_hospedes: int = Field(..., examples=[4])
    valor_bruto: float = Field(..., examples=[3200.0])
    taxa_aplicada: float = Field(..., description="Comissão (%) vigente quando a reserva foi feita.",
                                 examples=[15.0])
    valor_comissao: float = Field(..., examples=[480.0])
    valor_liquido: float = Field(..., examples=[2720.0])
    status: StatusReserva = Field(..., examples=["confirmada"])
    observacao: Optional[str] = None


class ListagemReservasSchema(BaseModel):
    reservas: List[ReservaViewSchema]
