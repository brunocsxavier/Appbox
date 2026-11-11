"""Abuse cases derivados do Threat Model do Dia 01.

Cada teste é o CRITÉRIO DE ACEITE de uma ameaça (TM-xx) escrito como código.
Hoje (versão v1 do Core Box) eles FALHAM — essa é a prova de que a ameaça existe.
Quando a correção for feita, o teste passa e passa a proteger contra regressão.

Processo de exceção: se o grupo NÃO corrigir uma ameaça hoje, marque o teste com
    @pytest.mark.xfail(reason="TM-xx: risco aceito até AAAA-MM-DD — ticket BOX-123 — dono: fulano")
e registre a exceção no arquivo EXCECOES.md. Teste apagado = reprovação no critério.
"""
import hashlib

from tests.conftest import MARIA, JOAO, ANA, token, saldo, login_backoffice


# ---------------------------------------------------------------- MUST-FIX (obrigatórios)

def test_tm03_bola_pix_nao_debita_conta_de_terceiro(client):
    """TM-03: Maria não pode enviar Pix a partir da conta da Ana."""
    h = token(client, MARIA)
    antes_ana = saldo(client, ANA)
    r = client.post("/api/v1/pix/transferencias", headers=h,
                    json={"conta_origem": ANA["conta"], "chave": "+5511988887777", "valor": 300.0})
    assert r.status_code in (403, 404), "API aceitou conta_origem de outro cliente (BOLA)"
    assert saldo(client, ANA) == antes_ana


def test_tm23_login_nao_revela_se_cpf_e_cliente(client):
    """TM-23: mesma mensagem e mesmo status para CPF inexistente e senha errada."""
    r1 = client.post("/api/v1/auth/login", json={"cpf": "123.456.789-00", "senha": "111111"})
    r2 = client.post("/api/v1/auth/login", json={"cpf": MARIA["cpf"], "senha": "111111"})
    assert r1.status_code == r2.status_code
    assert r1.get_json() == r2.get_json()


def test_tm07_erro_nao_expoe_stack_trace(client):
    """TM-07: entrada inválida não pode devolver stack trace nem detalhes internos."""
    h = token(client, MARIA)
    r = client.post("/api/v1/pix/transferencias", headers=h,
                    json={"chave": "+5511988887777", "valor": "abc"})
    corpo = r.get_data(as_text=True)
    assert "Traceback" not in corpo and "File \"" not in corpo and ".py" not in corpo
    assert r.status_code in (400, 422)


def test_tm12_senha_nao_armazenada_em_md5(app, client):
    """TM-12: hash de senha não pode ser MD5 (nem qualquer hash rápido sem salt)."""
    from app.db import get_db
    with app.app_context():
        h = get_db().execute("SELECT senha_hash FROM usuarios WHERE cpf = ?", (MARIA["cpf"],)).fetchone()[0]
    assert h != hashlib.md5(b"123456").hexdigest()
    assert h != hashlib.sha1(b"123456").hexdigest() and h != hashlib.sha256(b"123456").hexdigest()
    # e o login continua funcionando
    assert client.post("/api/v1/auth/login", json={"cpf": MARIA["cpf"], "senha": "123456"}).status_code == 200


def test_tm29_busca_backoffice_resiste_a_sql_injection(client):
    """TM-29: a busca do backoffice não pode ser manipulada com SQL."""
    login_backoffice(client)
    r = client.get("/backoffice", query_string={"q": "x' OR '1'='1"})
    corpo = r.get_data(as_text=True)
    assert "João Carlos Pereira" not in corpo and "Ana Lúcia Souza" not in corpo


# ---------------------------------------------------------------- BÔNUS (desejáveis)

def test_tm01_bloqueio_apos_tentativas_invalidas(client):
    """TM-01: após 5 falhas seguidas o CPF fica temporariamente bloqueado (HTTP 429)."""
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"cpf": JOAO["cpf"], "senha": "000000"})
    r = client.post("/api/v1/auth/login", json={"cpf": JOAO["cpf"], "senha": JOAO["senha"]})
    assert r.status_code == 429


def test_tm04_limite_override_e_ignorado(client):
    """TM-04: o cliente não pode furar o limite enviando limite_override=true."""
    h = token(client, ANA)
    r = client.post("/api/v1/pix/transferencias", headers=h,
                    json={"chave": "+5511988887777", "valor": 20000.0, "limite_override": "true"})
    assert r.status_code == 422


def test_tm08_comprovante_exige_dono_autenticado(client):
    """TM-08: comprovante não é público; terceiros e anônimos não acessam."""
    h = token(client, MARIA)
    tx = client.post("/api/v1/pix/transferencias", headers=h,
                     json={"chave": "+5511988887777", "valor": 15.0}).get_json()
    anonimo = client.application.test_client()
    r = anonimo.get(tx["comprovante"])
    assert r.status_code in (401, 403, 404) or (r.status_code == 302 and "/login" in r.headers["Location"])
    assert anonimo.get(tx["comprovante"], headers=token(anonimo, ANA)).status_code in (403, 404)


def test_tm20_idempotency_key_evita_pix_duplicado(client):
    """TM-20: a mesma Idempotency-Key não pode gerar dois débitos."""
    h = token(client, MARIA)
    h["Idempotency-Key"] = "c0ffee00-0000-4000-8000-000000000001"
    antes = saldo(client, MARIA)
    for _ in range(2):
        client.post("/api/v1/pix/transferencias", headers=h, json={"chave": "+5511988887777", "valor": 70.0})
    assert saldo(client, MARIA) == antes - 70.0


def test_tm10_ajuste_exige_justificativa_e_alcada(client):
    """TM-10: sem justificativa é recusado; acima de R$ 10.000 fica pendente de 2ª aprovação."""
    login_backoffice(client)
    antes = saldo(client, JOAO)
    sem_just = client.post("/backoffice/ajuste", data={"conta": JOAO["conta"], "tipo": "credito", "valor": "10"},
                           headers={"Accept": "application/json"})
    assert sem_just.status_code == 400
    alto = client.post("/backoffice/ajuste", data={"conta": JOAO["conta"], "tipo": "credito", "valor": "250000",
                                                  "justificativa": "teste"}, headers={"Accept": "application/json"})
    assert alto.status_code == 202
    assert saldo(client, JOAO) == antes
