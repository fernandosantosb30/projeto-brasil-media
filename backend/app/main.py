from fastapi import FastAPI, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import sys
import os

# Adiciona a pasta atual ao PATH do sistema
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Query, File, UploadFile
# Agora o import vai funcionar 100%
from data_handler import carregar_dados_planilha, obter_opcoes_filtros, normalizar_texto, extrair_numero
# Importamos as funções do seu arquivo de lógica de dados
# Removi o ponto (from .data_handler) para rodar direto na pasta backend
from data_handler import (
    carregar_dados_planilha, 
    obter_opcoes_filtros, 
    normalizar_texto, 
    extrair_numero
)

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
    if DADOS_FIXOS is None or DADOS_FIXOS.empty:
        return {"custo_medio": 0, "quantidade_contratos": 0, "tipo_resultado": "vazio"}

    df_especifico = DADOS_FIXOS.copy()
    
    if uf: df_especifico = df_especifico[df_especifico['uf'] == normalizar_texto(uf)]
    if cidade: df_especifico = df_especifico[df_especifico['cidade'] == normalizar_texto(cidade)]
    if tipo_servico: df_especifico = df_especifico[df_especifico['tipo_servico'] == normalizar_texto(tipo_servico)]
    if interface: df_especifico = df_especifico[df_especifico['interface'] == normalizar_texto(interface)]
    if ip_fixo: df_especifico = df_especifico[df_especifico['ip_fixo'] == normalizar_texto(ip_fixo)]
    if velocidade: df_especifico = df_especifico[df_especifico['velocidade'] == velocidade]
    if prazo: df_especifico = df_especifico[df_especifico['prazo'] == prazo]

    qtd_especifica = len(df_especifico)

    if qtd_especifica > 0:
        media = df_especifico['valor'].mean()
        return {
            "custo_medio": round(float(media), 2),
            "quantidade_contratos": int(qtd_especifica),
            "tipo_resultado": "especifico"
        }

    df_uf = DADOS_FIXOS.copy()
    if uf:
        df_uf = df_uf[df_uf['uf'] == normalizar_texto(uf)]
        if tipo_servico: df_uf = df_uf[df_uf['tipo_servico'] == normalizar_texto(tipo_servico)]
        if velocidade: df_uf = df_uf[df_uf['velocidade'] == velocidade]
        
        qtd_uf = len(df_uf)
        if qtd_uf > 0:
            media_uf = df_uf['valor'].mean()
            return {
                "custo_medio": round(float(media_uf), 2),
                "quantidade_contratos": int(qtd_uf),
                "tipo_resultado": "media_regional",
                "mensagem": "Exibindo média regional (UF)."
            }

    return {"custo_medio": 0, "quantidade_contratos": 0, "tipo_resultado": "sem_dados"}

@app.post("/contratos/processar-planilha")
async def processar_planilha_lote(file: UploadFile = File(...)):
    if DADOS_FIXOS is None:
        return {"erro": "Base de dados não carregada"}

    content = await file.read()
    
    try:
        # Tenta ler CSV MS-DOS (Excel Brasil)
        df_entrada = pd.read_csv(io.BytesIO(content), sep=';', encoding='latin-1')
        if len(df_entrada.columns) <= 1:
            raise ValueError("Separador incorreto")
    except:
        # Tenta CSV Padrão
        df_entrada = pd.read_csv(io.BytesIO(content), sep=',', encoding='utf-8')

    df_entrada.columns = [c.lower().strip() for c in df_entrada.columns]
    
    resultados_custo = []
    quantidades = []

    for index, row in df_entrada.iterrows():
        cidade = str(row.get('cidade', '')).strip()
        uf = str(row.get('uf', '')).strip()
        servico = str(row.get('servico', row.get('serviço', ''))).strip()
        
        # Garante que a velocidade seja processada como número
        try:
            vel_raw = row.get('velocidade', 0)
            vel = int(extrair_numero(vel_raw)) if vel_raw else 0
        except:
            vel = 0

        df_temp = DADOS_FIXOS.copy()
        
        df_filtrado = df_temp[
            (df_temp['uf'] == normalizar_texto(uf)) &
            (df_temp['tipo_servico'] == normalizar_texto(servico)) &
            (df_temp['velocidade'] == vel)
        ]
        
        df_cidade = df_filtrado[df_filtrado['cidade'] == normalizar_texto(cidade)]
        
        if not df_cidade.empty:
            valor = df_cidade['valor'].mean()
            qtd = len(df_cidade)
        elif not df_filtrado.empty:
            valor = df_filtrado['valor'].mean()
            qtd = len(df_filtrado)
        else:
            valor = 0
            qtd = 0
            
        resultados_custo.append(round(float(valor), 2))
        quantidades.append(int(qtd))

    df_entrada['custo_medio_estimado'] = resultados_custo
    df_entrada['amostragem_contratos'] = quantidades

    # Gera a saída formatada para Excel (Latin-1 e Ponto e Vírgula)
    output = io.StringIO()
    df_entrada.to_csv(output, index=False, sep=';', encoding='latin-1')
    
    # Converte para bytes para o StreamingResponse não falhar
    response_content = output.getvalue().encode('latin-1')
    
    return StreamingResponse(
        io.BytesIO(response_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=resultado_custos_tecpar.csv"}
    )