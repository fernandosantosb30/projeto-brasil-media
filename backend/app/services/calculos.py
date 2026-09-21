from decimal import ROUND_HALF_UP, Decimal

from ..schemas import Filtros, Resultado


def processar_custo_medio(data, filtros: Filtros) -> Resultado:
    criterios = filtros.model_dump(exclude_none=True)

    def selecionar(campos):
        return [row for row in data if all(row[key] == value for key, value in campos.items())]

    matches = selecionar(criterios)
    tipo = "especifico"
    mensagem = "Média dos contratos que atendem aos filtros selecionados."
    # A alternativa regional relaxa somente a cidade, mantendo os demais critérios.
    if not matches and filtros.cidade and filtros.uf:
        matches = selecionar({key: value for key, value in criterios.items() if key != "cidade"})
        tipo = "media_regional"
        mensagem = "Média regional da UF: cidade desconsiderada; demais filtros preservados."
    if not matches:
        return Resultado(
            custo_medio=None,
            quantidade_contratos=0,
            tipo_resultado="sem_dados",
            mensagem="Nenhum contrato encontrado para estes filtros.",
        )
    media = sum((row["valor"] for row in matches), Decimal(0)) / len(matches)
    return Resultado(
        custo_medio=float(media.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        quantidade_contratos=len(matches),
        tipo_resultado=tipo,
        mensagem=mensagem,
    )
