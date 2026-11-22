from pydantic import BaseModel, Field


class ErroSchema(BaseModel):
    """Formato das mensagens de erro da API."""
    mensagem: str = Field(..., examples=["Reserva 7 não encontrada."])


class MensagemSchema(BaseModel):
    """Confirmação de uma exclusão."""
    mensagem: str = Field(..., examples=["Registro removido com sucesso."])
    id: int = Field(..., examples=[7])
