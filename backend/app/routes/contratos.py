from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.calculos import processar_custo_medio

router = APIRouter(prefix="/contratos", tags=["Contratos"])

@router.get("/custo-medio")
def obter_custo_medio(
    tipo_servico: str = None,
    velocidade: int = None,
    cidade: str = None,
    uf: str = None,
    provedor: str = None,
    db: Session = Depends(get_db)
):
    filtros = {
        "tipo_servico": tipo_servico,
        "velocidade": velocidade,
        "cidade": cidade,
        "uf": uf,
        "provedor_nome": provedor
    }
    
    resultado = processar_custo_medio(db, filtros)
    return resultado