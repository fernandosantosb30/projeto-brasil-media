from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ContratoBase(BaseModel):
    provedor_nome: str
    tipo_servico: str
    velocidade: int
    bloco_ip: Optional[str]
    cidade: str
    uf: str
    valor_mensal: float
    vigencia: int
    tipo_rede: str

class ContratoCreate(ContratoBase):
    pass

class ContratoResponse(ContratoBase):
    id: int
    data_importacao: datetime

    class Config:
        from_attributes = True