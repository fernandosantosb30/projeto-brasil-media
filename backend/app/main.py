from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
# Importamos a função de normalização para usar nos filtros de busca
from .data_handler import carregar_dados_planilha, obter_opcoes_filtros, normalizar_texto

app = FastAPI()

# --- CARREGAMENTO ÚNICO EM MEMÓRIA ---
try:
    DADOS_FIXOS = carregar_dados_planilha()
    OPCOES_FILTROS = obter_opcoes_filtros(DADOS_FIXOS)
    print("✅ Planilha carregada e limpa com sucesso!")
except Exception as e:
    print(f"❌ Erro na inicialização: {e}")
    DADOS_FIXOS = None
    OPCOES_FILTROS = {"servicos": [], "interfaces": [], "ips": []}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/filtros/opcoes")
def get_opcoes():
    return OPCOES_FILTROS

@app.get("/contratos/custo-medio")
def calcular_media(
    cidade: str = Query(None),
    uf: str = Query(None),
    tipo_servico: str = Query(None),
    interface: str = Query(None),
    ip_fixo: str = Query(None),
    velocidade: int = Query(None),
    prazo: int = Query(None)
):
    # Se a planilha não carregou, retorna vazio para não travar o site
    if DADOS_FIXOS is None or DADOS_FIXOS.empty:
        return {"custo_medio": 0, "quantidade_contratos": 0}

    # Criamos uma cópia dos dados para aplicar os filtros da busca atual
    df = DADOS_FIXOS.copy()
    
    # --- FILTROS COM NORMALIZAÇÃO ---
    # Usamos normalizar_texto em tudo para ignorar acentos e maiúsculas/minúsculas
    
    if cidade:
        df = df[df['cidade'] == normalizar_texto(cidade)]
    
    if uf:
        df = df[df['uf'] == normalizar_texto(uf)]

    if tipo_servico:
        df = df[df['tipo_servico'] == normalizar_texto(tipo_servico)]

    if interface:
        df = df[df['interface'] == normalizar_texto(interface)]

    if ip_fixo:
        df = df[df['ip_fixo'] == normalizar_texto(ip_fixo)]

    # Filtros Numéricos (já limpos como int no data_handler)
    if velocidade:
        df = df[df['velocidade'] == velocidade]

    if prazo:
        df = df[df['prazo'] == prazo]

    # --- CÁLCULO DOS RESULTADOS ---
    qtd = len(df)
    media = df['valor'].mean() if qtd > 0 else 0

    return {
        "custo_medio": round(float(media), 2),
        "quantidade_contratos": int(qtd)
    }