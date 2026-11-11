"""Testes funcionais — garantem que o Core Box continua funcionando após as correções."""
from tests.conftest import MARIA, JOAO, token, saldo, login_backoffice


def test_health(client):
    assert client.get("/health").status_code == 200


def test_login_web_redireciona_para_home(client):
    r = client.post("/login", data={"cpf": MARIA["cpf"], "senha": MARIA["senha"]})
    assert r.status_code == 302 and r.headers["Location"].endswith("/home")


def test_home_mostra_saldo(client):
    client.post("/login", data={"cpf": MARIA["cpf"], "senha": MARIA["senha"]})
    r = client.get("/home")
    assert r.status_code == 200 and "Saldo disponível" in r.get_data(as_text=True)


def test_login_api_invalido_retorna_erro(client):
    r = client.post("/api/v1/auth/login", json={"cpf": MARIA["cpf"], "senha": "000000"})
    assert r.status_code in (400, 401, 403)


def test_pix_da_propria_conta(client):
    h = token(client, MARIA)
    antes_maria, antes_joao = saldo(client, MARIA), saldo(client, JOAO)
    r = client.post("/api/v1/pix/transferencias", headers=h,
                    json={"chave": "+5511988887777", "valor": 100.0, "descricao": "aluguel"})
    assert r.status_code == 201, r.get_json()
    assert saldo(client, MARIA) == antes_maria - 100.0
    assert saldo(client, JOAO) == antes_joao + 100.0


def test_pix_acima_do_limite_e_recusado(client):
    h = token(client, MARIA)
    r = client.post("/api/v1/pix/transferencias", headers=h,
                    json={"chave": "+5511988887777", "valor": 20000.0})
    assert r.status_code == 422


def test_pix_saldo_insuficiente(client):
    h = token(client, JOAO)
    r = client.post("/api/v1/pix/transferencias", headers=h,
                    json={"chave": "maria@exemplo.com", "valor": 4999.0})
    assert r.status_code == 422


def test_comprovante_do_dono_acessivel(client):
    h = token(client, MARIA)
    tx = client.post("/api/v1/pix/transferencias", headers=h,
                     json={"chave": "+5511988887777", "valor": 10.0}).get_json()
    r = client.get(tx["comprovante"], headers=h)
    assert r.status_code == 200


def test_backoffice_login_e_busca(client):
    login_backoffice(client)
    r = client.get("/backoffice?q=Maria")
    assert r.status_code == 200 and "Maria" in r.get_data(as_text=True)


def test_backoffice_ajuste_pequeno_com_justificativa(client):
    login_backoffice(client)
    antes = saldo(client, JOAO)
    r = client.post("/backoffice/ajuste", data={"conta": JOAO["conta"], "tipo": "credito", "valor": "50",
                                               "justificativa": "Estorno tarifa indevida - chamado 123"},
                    headers={"Accept": "application/json"})
    assert r.status_code == 200
    assert saldo(client, JOAO) == antes + 50
