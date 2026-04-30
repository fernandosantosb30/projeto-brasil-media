from sqlalchemy import Column, Integer, String, Float, DateTime
from .database import Base
import datetime

class Contrato(Base): # <--- O erro diz que este nome 'Contrato' não foi achado
    __tablename__ = "contratos"

    id = Column(Integer, primary_key=True, index=True)
    provedor_nome = Column(String(255))
    tipo_servico = Column(String(100))
    velocidade = Column(Integer)  # Mbps
    bloco_ip = Column(String(100))
    cidade = Column(String(100))
    uf = Column(String(2))
    valor_mensal = Column(Float)
    vigencia = Column(Integer)    # Meses
    tipo_rede = Column(String(50)) # Própria ou Last-mile
    data_importacao = Column(DateTime, default=datetime.datetime.utcnow)