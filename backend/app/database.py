from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Mantenha apenas a string direta, sem o os.getenv
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:GGwaopq%401@127.0.0.1:3306/custo_medio"

# O engine é o motor que mantém a conexão viva
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Função usada pelas rotas para abrir e fechar a conexão
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()