import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("BOX_ANTIFRAUDE_INDISPONIVEL", raising=False)
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "teste.db"),
                      "UPLOAD_DIR": str(tmp_path / "uploads")})
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


MARIA = {"cpf": "987.654.321-00", "senha": "123456", "conta": "00012345-6"}
JOAO = {"cpf": "111.222.333-44", "senha": "246810", "conta": "00998877-1"}
ANA = {"cpf": "555.666.777-88", "senha": "123456", "conta": "00055566-7"}


def token(client, pessoa):
    r = client.post("/api/v1/auth/login", json={"cpf": pessoa["cpf"], "senha": pessoa["senha"]})
    assert r.status_code == 200, r.get_json()
    return {"Authorization": "Bearer " + r.get_json()["token"]}


def saldo(client, pessoa):
    return client.get("/api/v1/contas/minha", headers=token(client, pessoa)).get_json()["saldo"]


def login_backoffice(client):
    return client.post("/backoffice/login", data={"usuario": "admin", "senha": "admin123"})
