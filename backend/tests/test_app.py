import csv
import io
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app.data_handler import extrair_numero
from backend.app.main import ROOT, create_app


@pytest.fixture
def client():
    with TestClient(create_app(ROOT / "backend/dados_ficticios.csv")) as client:
        yield client


def test_frontend_and_health(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert "contratos e valores" in client.get("/").text
    assert client.get("/src/services/script.js").status_code == 200
    assert client.get("/backend/dados_ficticios.csv").status_code == 404
    assert client.get("/backend/contratos.csv").status_code == 404
    assert client.get("/.env").status_code == 404


def test_normalization_and_exact_mean(client):
    result = client.get(
        "/contratos/custo-medio",
        params={"cidade": " curitiba ", "uf": "pr", "tipo_servico": "Link dedicado", "velocidade": 500},
    ).json()
    assert result["custo_medio"] == 1200
    assert result["quantidade_contratos"] == 2
    assert result["tipo_resultado"] == "especifico"


def test_regional_only_relaxes_city(client):
    params = {"cidade": "Maringá", "uf": "PR", "velocidade": 500, "tipo_servico": "Link dedicado"}
    result = client.get("/contratos/custo-medio", params=params).json()
    assert result["custo_medio"] == 1400
    assert result["tipo_resultado"] == "media_regional"
    for extra in ({"interface": "Rádio"}, {"prazo": 36}, {"ip_fixo": "Não"}):
        result = client.get("/contratos/custo-medio", params=params | extra).json()
        assert result["custo_medio"] is None
        assert result["quantidade_contratos"] == 0
        assert result["tipo_resultado"] == "sem_dados"


@pytest.mark.parametrize(
    "params", [{"velocidade": 0}, {"velocidade": -5}, {"prazo": "abc"}, {"uf": "ABC"}, {"inesperado": 1}]
)
def test_invalid_filters(client, params):
    assert client.get("/contratos/custo-medio", params=params).status_code == 422


@pytest.mark.parametrize(
    ("value", "expected"), [("R$ 1.234,56", "1234.56"), ("1200.50", "1200.50"), ("500 Mbps", "500")]
)
def test_numbers(value, expected):
    assert extrair_numero(value) == Decimal(expected)


@pytest.mark.parametrize("value", ["-100", "abc", "NaN", "inf", "1,2,3", "1.23,45", "0", "1 Gbps"])
def test_bad_numbers(value):
    with pytest.raises(ValueError):
        extrair_numero(value)


@pytest.mark.parametrize("encoding", ["utf-8-sig", "cp1252"])
@pytest.mark.parametrize("delimiter", [";", ","])
def test_batch_matches_individual(client, encoding, delimiter):
    content = io.StringIO()
    writer = csv.writer(content, delimiter=delimiter)
    writer.writerow(["cidade", "uf", "serviço", "velocidade", "interface", "prazo"])
    writer.writerows(
        [
            ["Curitiba", "PR", "Link dedicado", "500", "Fibra", "12"],
            ["Maringá", "PR", "Link dedicado", "500", "Fibra", "12"],
            ["Recife", "PE", "Banda larga", "100", "Rádio", "12"],
            ["Curitiba", "PR", "Link dedicado", "500", "Rádio", "36"],
        ]
    )
    response = client.post(
        "/contratos/processar-planilha", files={"file": ("entrada.csv", content.getvalue().encode(encoding))}
    )
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))
    assert [row["custo_medio_estimado"] for row in rows] == ["1200,00", "1400,00", "120,00", ""]
    assert [row["tipo_resultado"] for row in rows] == [
        "especifico",
        "media_regional",
        "especifico",
        "sem_dados",
    ]


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"cidade;uf\nA;PR\n",
        b"cidade;cidade\nA;A",
        b"cidade;uf;tipo_servico;velocidade\nA;PR;Link;abc",
        b"cidade;uf;tipo_servico;velocidade\nA;PR;Link;500;extra",
        b"cidade;uf;tipo_servico;velocidade\n;PR;Link;500",
        b"cidade;uf;tipo_servico;velocidade\nA;PR;Link;500.5",
    ],
)
def test_bad_csv(client, content):
    response = client.post("/contratos/processar-planilha", files={"file": ("entrada.csv", content)})
    assert response.status_code == 422


def test_formula_and_unicode_export(client):
    content = "cidade;uf;tipo_servico;velocidade\n=1+1;PR;Link dedicado;500\n🚀;PR;Link dedicado;500"
    response = client.post("/contratos/processar-planilha", files={"file": ("entrada.csv", content.encode())})
    assert response.status_code == 200
    assert "'=1+1" in response.content.decode("utf-8-sig")
    assert "🚀" in response.content.decode("utf-8-sig")


def test_upload_limits(client):
    response = client.post(
        "/contratos/processar-planilha", files={"file": ("entrada.csv", b"a" * (2 * 1024 * 1024 + 1))}
    )
    assert response.status_code == 413
    content = b"cidade;uf;tipo_servico;velocidade\n" + b"A;PR;Link;500\n" * 1001
    assert (
        client.post("/contratos/processar-planilha", files={"file": ("entrada.csv", content)}).status_code
        == 422
    )


def test_invalid_base_stops_startup(tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_text("cidade,uf\nCuritiba,PR")
    with pytest.raises(RuntimeError, match="Não foi possível carregar"), TestClient(create_app(path)):
        pass


def test_request_limit_before_multipart(client):
    def chunks():
        for _ in range(40):
            yield b"a" * 65536

    response = client.post(
        "/contratos/processar-planilha",
        content=chunks(),
        headers={"Content-Type": "multipart/form-data; boundary=test"},
    )
    assert response.status_code == 413


def test_base_validates_money_and_required_fields(tmp_path):
    from backend.app.data_handler import carregar_dados_planilha

    path = tmp_path / "base.csv"
    header = "cidade;uf;tipo_servico;interface;ip_fixo;velocidade;prazo;valor\n"
    path.write_text(header + "São Paulo;SP;Link;Fibra;Sim;500;12;R$ 1.234,56\n")
    assert carregar_dados_planilha(path)[0]["valor"] == Decimal("1234.56")
    path.write_text(header + "São Paulo;SP;Link;Fibra;Sim;500;12;inválido\n")
    with pytest.raises(ValueError, match="linha 2"):
        carregar_dados_planilha(path)
