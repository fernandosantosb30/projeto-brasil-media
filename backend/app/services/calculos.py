import pandas as pd
from sqlalchemy.orm import Session
from ..models import Contrato

def processar_custo_medio(db: Session, filtros: dict):
    # Inicia a consulta no banco de dados
    query = db.query(Contrato)
    
    # Aplica filtros dinâmicos (Cidade, UF, Velocidade, etc)
    for key, value in filtros.items():
        if value is not None: # Garante que filtros vazios não quebrem a query
            query = query.filter(getattr(Contrato, key) == value)
    
    # Converte a query do SQLAlchemy para um DataFrame do Pandas
    df = pd.read_sql(query.statement, db.bind)
    
    if df.empty:
        return {
            "mensagem": "Nenhum dado encontrado para esses filtros",
            "custo_medio": 0,
            "quantidade_contratos": 0
        }

    # Retorna os cálculos estatísticos
    return {
        "custo_medio": round(float(df['valor_mensal'].mean()), 2),
        "quantidade_contratos": int(len(df)),
        "maximo": float(df['valor_mensal'].max()),
        "minimo": float(df['valor_mensal'].min()),
        "filtros_aplicados": filtros
    }

def definir_tipo_rede(valor):
    """
    Regra de Negócio: 
    Se o valor for nulo ou igual a 0, é considerado Rede Própria.
    """
    if valor is None or valor == 0:
        return "Rede Própria"
    return "Rede Last-mile"