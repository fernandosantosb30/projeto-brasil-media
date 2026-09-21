from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .data_handler import normalizar_texto


class Filtros(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cidade: str | None = Field(None, max_length=100)
    uf: str | None = Field(None, pattern=r"^[A-Z]{2}$")
    tipo_servico: str | None = Field(None, max_length=100)
    interface: str | None = Field(None, max_length=100)
    ip_fixo: str | None = Field(None, max_length=100)
    velocidade: int | None = Field(None, gt=0, le=1_000_000_000)
    prazo: int | None = Field(None, gt=0, le=1_000_000_000)

    @field_validator("cidade", "uf", "tipo_servico", "interface", "ip_fixo", mode="before")
    @classmethod
    def limpar_texto(cls, value):
        return normalizar_texto(value) or None


class Resultado(BaseModel):
    custo_medio: float | None
    quantidade_contratos: int
    tipo_resultado: Literal["especifico", "media_regional", "sem_dados"]
    mensagem: str
