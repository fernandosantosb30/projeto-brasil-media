from fastapi import FastAPI
from .database import engine, Base
from .routes import contratos

# Cria as tabelas no MySQL automaticamente se elas não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema Custo Médio - Telecom")

# Inclui as rotas de contratos
app.include_router(contratos.router)

@app.get("/")
def home():
    return {"message": "API Custo Médio Online"}