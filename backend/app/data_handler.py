import pandas as pd
import os
import re
import unicodedata

def normalizar_texto(texto):
    """Remove acentos, espaços extras e coloca em maiúsculo"""
    if pd.isna(texto) or texto == '':
        return "NÃO INFORMADO"
    # Remove acentos (Ex: 'Caxias do Sul' -> 'Caxias do Sul')
    nfkd_form = unicodedata.normalize('NFKD', str(texto))
    texto_sem_acento = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Limpa espaços e sobe para MAIÚSCULO
    return texto_sem_acento.strip().upper()

def extrair_numero(valor):
    """Extrai apenas números (MB, R$, etc)"""
    if pd.isna(valor) or valor == '': return 0
    apenas_numeros = re.sub(r'[^0-9,.]', '', str(valor)).replace(',', '.')
    try:
        return float(apenas_numeros)
    except:
        return 0

def carregar_dados_planilha():
    caminho_csv = os.path.join(os.path.dirname(__file__), '..', 'contratos.csv')
    try:
        df = pd.read_csv(caminho_csv, low_memory=False)
        mapeamento = {
            'Cidade A': 'cidade',
            'UF A': 'uf',
            'Serviço': 'tipo_servico',
            'Interface': 'interface',
            'IP Fixo': 'ip_fixo',
            'Capacidade (MB)': 'velocidade',
            'Vigência em (Meses)': 'prazo',
            'Valor Mensal (C/IMP) (R$)': 'valor'
        }
        colunas_reais = [col for col in mapeamento.keys() if col in df.columns]
        df = df[colunas_reais].rename(columns=mapeamento)

        # Normalização de NÚMEROS
        df['velocidade'] = df['velocidade'].apply(extrair_numero).astype(int)
        df['prazo'] = df['prazo'].apply(extrair_numero).astype(int)
        df['valor'] = df['valor'].apply(extrair_numero)

        # Normalização de TEXTO (Cidade, Serviço, etc)
        cols_texto = ['cidade', 'uf', 'tipo_servico', 'interface', 'ip_fixo']
        for col in cols_texto:
            if col in df.columns:
                df[col] = df[col].apply(normalizar_texto)

        return df[df['valor'] > 0]
    except Exception as e:
        print(f"Erro no processamento: {e}")
        return pd.DataFrame()

def obter_opcoes_filtros(df):
    if df is None or df.empty:
        return {"servicos": [], "interfaces": [], "ips": []}
    
    # Converte para string para evitar o erro de comparação float vs str
    return {
        "servicos": sorted([str(x) for x in df['tipo_servico'].unique() if x != "NÃO INFORMADO"]),
        "interfaces": sorted([str(x) for x in df['interface'].unique() if x != "NÃO INFORMADO"]),
        "ips": sorted([str(x) for x in df['ip_fixo'].unique() if x != "NÃO INFORMADO"])
    }