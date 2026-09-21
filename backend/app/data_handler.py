"""Leitura e validação de CSV sem persistir arquivos enviados."""

import csv
import io
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path

TEXT_FIELDS = ("cidade", "uf", "tipo_servico", "interface", "ip_fixo")
BASE_FIELDS = (*TEXT_FIELDS, "velocidade", "prazo", "valor")
ALIASES = {
    "cidade a": "cidade",
    "uf a": "uf",
    "servico": "tipo_servico",
    "ip fixo": "ip_fixo",
    "capacidade (mb)": "velocidade",
    "vigencia em (meses)": "prazo",
    "valor mensal (c/imp) (r$)": "valor",
}


def normalizar_texto(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    return " ".join("".join(c for c in texto if not unicodedata.combining(c)).upper().split())


def extrair_numero(valor):
    """Aceita decimal com ponto ou formato brasileiro com vírgula e milhar."""
    texto = str(valor).strip()
    texto = re.sub(r"^(?:R\$)\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s*(?:Mbps|MB|meses)$", "", texto, flags=re.IGNORECASE).strip()
    if "," in texto:
        if not re.fullmatch(r"(?:\d+|\d{1,3}(?:\.\d{3})+),\d+", texto):
            raise ValueError("Número inválido.")
        texto = texto.replace(".", "").replace(",", ".")
    elif not re.fullmatch(r"\d+(?:\.\d+)?", texto):
        raise ValueError("Número inválido.")
    try:
        numero = Decimal(texto)
    except InvalidOperation:
        raise ValueError("Número inválido.") from None
    if not numero.is_finite() or numero <= 0 or numero > 1_000_000_000:
        raise ValueError("Número fora do intervalo permitido.")
    return numero


def ler_csv(content: bytes, max_rows=1000):
    if not content or b"\x00" in content:
        raise ValueError("Envie um CSV não vazio, em UTF-8 ou Windows-1252.")
    try:
        texto = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            texto = content.decode("cp1252")
        except UnicodeDecodeError:
            raise ValueError("Codificação inválida. Utilize UTF-8.") from None
    try:
        first_line = texto.splitlines()[0]
        delimiter = ";" if ";" in first_line else ","
        reader = csv.reader(io.StringIO(texto, newline=""), delimiter=delimiter, strict=True)
        raw_headers = next(reader)
        headers = [normalizar_texto(c).lower() for c in raw_headers]
        headers = [ALIASES.get(c, c) for c in headers]
        if not headers or any(not c for c in headers) or len(set(headers)) != len(headers):
            raise ValueError("Cabeçalhos vazios ou duplicados.")
        rows = []
        for row in reader:
            if not row or all(not c.strip() for c in row):
                continue
            if len(row) != len(headers):
                raise ValueError("Quantidade de campos incompatível com o cabeçalho.")
            rows.append(dict(zip(headers, (c.strip() for c in row))))
            if len(rows) > max_rows:
                raise ValueError(f"O CSV deve conter no máximo {max_rows} registros.")
        if not rows:
            raise ValueError("O CSV precisa conter ao menos um registro.")
        return headers, rows
    except (csv.Error, StopIteration, IndexError):
        raise ValueError("CSV inválido. Verifique delimitadores e aspas.") from None


def carregar_dados_planilha(caminho: Path):
    headers, rows = ler_csv(caminho.read_bytes(), max_rows=100_000)
    if not set(BASE_FIELDS).issubset(headers):
        raise ValueError("A base não contém todas as colunas obrigatórias.")
    data = []
    for index, row in enumerate(rows, start=2):
        try:
            record = {key: normalizar_texto(row[key]) for key in TEXT_FIELDS}
            if any(not value for value in record.values()) or not re.fullmatch("[A-Z]{2}", record["uf"]):
                raise ValueError("Campos de texto obrigatórios ou UF inválidos.")
            for key in ("velocidade", "prazo", "valor"):
                value = extrair_numero(row[key])
                if key != "valor" and value != value.to_integral_value():
                    raise ValueError("Velocidade e prazo devem ser inteiros.")
                record[key] = value if key == "valor" else int(value)
            data.append(record)
        except ValueError:
            raise ValueError(f"Registro inválido na linha {index} da base.") from None
    return data


def obter_opcoes_filtros(data):
    return {
        output: sorted({row[field] for row in data})
        for output, field in (("servicos", "tipo_servico"), ("interfaces", "interface"), ("ips", "ip_fixo"))
    }
