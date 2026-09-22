import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from .data_handler import carregar_dados_planilha, obter_opcoes_filtros
from .middleware import LimitarUpload
from .routes.contratos import router

ROOT = Path(__file__).resolve().parents[2]


def create_app(data_path: Path | None = None):
    load_dotenv(ROOT / ".env", override=False)
    path = data_path or Path(os.getenv("CONTRATOS_CSV", "backend/contratos.csv"))
    if not path.is_absolute():
        path = ROOT / path

    @asynccontextmanager
    async def lifespan(app):
        # Uma base inválida interrompe a inicialização, sem simular resultados vazios.
        try:
            app.state.dados = carregar_dados_planilha(path)
        except (OSError, ValueError):
            raise RuntimeError(
                "Não foi possível carregar a base. Verifique CONTRATOS_CSV e o formato documentado."
            ) from None
        yield

    app = FastAPI(title="Painel de Custos de Conectividade", version="1.0.0", lifespan=lifespan)
    app.add_middleware(LimitarUpload)
    app.include_router(router)

    @app.get("/health", tags=["Sistema"])
    def health():
        return {"status": "ok"}

    @app.get("/filtros/opcoes", tags=["Contratos"])
    def opcoes(request: Request):
        return obter_opcoes_filtros(request.app.state.dados)

    app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
    return app


app = create_app()
