import csv
import io
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import Response
from pydantic import ValidationError

from ..data_handler import extrair_numero, ler_csv
from ..schemas import Filtros, Resultado
from ..services.calculos import processar_custo_medio

router = APIRouter(prefix="/contratos", tags=["Contratos"])
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


@router.get("/custo-medio", response_model=Resultado)
def obter_custo_medio(request: Request, filtros: Annotated[Filtros, Query()]):
    return processar_custo_medio(request.app.state.dados, filtros)


def proteger_celula(value):
    """Impede interpretação de texto como fórmula ao abrir o CSV em planilhas."""
    text = str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")):
        return "'" + text
    return text


@router.post("/processar-planilha")
def processar_planilha(request: Request, file: Annotated[UploadFile, File()]):
    try:
        if not (file.filename or "").lower().endswith(".csv"):
            raise HTTPException(422, "Envie um arquivo com extensão .csv.")
        content = file.file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "O arquivo deve ter no máximo 2 MiB.")
        try:
            headers, rows = ler_csv(content)
            required = {"cidade", "uf", "tipo_servico", "velocidade"}
            allowed = set(Filtros.model_fields)
            if not required.issubset(headers) or not set(headers).issubset(allowed):
                raise ValueError(
                    "Use cidade, uf, tipo_servico e velocidade; opcionais: interface, ip_fixo e prazo."
                )
            output_rows = []
            for index, row in enumerate(rows, start=2):
                try:
                    if any(not row[key] for key in required):
                        raise ValueError("Campo obrigatório vazio.")
                    fields = dict(row)
                    for key in ("velocidade", "prazo"):
                        if fields.get(key):
                            value = extrair_numero(fields[key])
                            if value != value.to_integral_value():
                                raise ValueError("Use números inteiros.")
                            fields[key] = int(value)
                        elif key in fields:
                            fields[key] = None
                    filtros = Filtros.model_validate(fields)
                except (ValueError, ValidationError):
                    raise ValueError(f"Filtros inválidos na linha {index}.") from None
                result = processar_custo_medio(request.app.state.dados, filtros)
                output_rows.append(
                    {
                        **{k: proteger_celula(v) for k, v in row.items()},
                        "custo_medio_estimado": ""
                        if result.custo_medio is None
                        else f"{result.custo_medio:.2f}".replace(".", ","),
                        "amostragem_contratos": result.quantidade_contratos,
                        "tipo_resultado": result.tipo_resultado,
                    }
                )
        except ValueError as error:
            raise HTTPException(422, str(error)) from None
        output = io.StringIO(newline="")
        writer = csv.DictWriter(
            output,
            fieldnames=[*headers, "custo_medio_estimado", "amostragem_contratos", "tipo_resultado"],
            delimiter=";",
        )
        writer.writeheader()
        writer.writerows(output_rows)
        return Response(
            output.getvalue().encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="resultado_custos.csv"'},
        )
    finally:
        file.file.close()
