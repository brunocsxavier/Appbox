"""Acesso a dados (SQLite para o laboratório; em produção o Dia 01 previa PostgreSQL)."""
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    nascimento TEXT,
    nome_mae TEXT,
    celular TEXT,
    senha_hash TEXT NOT NULL,
    perfil TEXT NOT NULL DEFAULT 'cliente'
);
CREATE TABLE IF NOT EXISTS contas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    agencia TEXT NOT NULL,
    numero TEXT UNIQUE NOT NULL,
    saldo REAL NOT NULL DEFAULT 0,
    limite_diurno REAL NOT NULL,
    limite_noturno REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS chaves_pix (
    chave TEXT PRIMARY KEY,
    conta_numero TEXT NOT NULL REFERENCES contas(numero)
);
CREATE TABLE IF NOT EXISTS transacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    e2e TEXT NOT NULL,
    conta_origem TEXT NOT NULL,
    conta_destino TEXT NOT NULL,
    valor REAL NOT NULL,
    descricao TEXT,
    idempotency_key TEXT,
    criado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    ator TEXT,
    acao TEXT NOT NULL,
    detalhe TEXT
);
CREATE TABLE IF NOT EXISTS dispositivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    descricao TEXT,
    vinculado_em TEXT
);
CREATE TABLE IF NOT EXISTS otp (
    cpf TEXT PRIMARY KEY,
    codigo TEXT NOT NULL,
    expira_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tentativas_login (
    cpf TEXT PRIMARY KEY,
    falhas INTEGER NOT NULL DEFAULT 0,
    bloqueado_ate TEXT
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def seed(conn):
    from app.seguranca import hash_senha

    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]:
        return
    usuarios = [
        ("987.654.321-00", "Maria Aparecida da Silva", "14/03/1985", "Josefa da Silva",
         "(61) 99812-4471", "123456", "cliente"),
        ("111.222.333-44", "João Carlos Pereira", "02/07/1979", "Rita Pereira",
         "(11) 98888-7777", "246810", "cliente"),
        ("555.666.777-88", "Ana Lúcia Souza", "21/11/1990", "Clara Souza",
         "(21) 97777-1234", "123456", "cliente"),
        ("000.000.000-01", "admin", "01/01/1970", "-", "-", "admin123", "operador"),
    ]
    for cpf, nome, nasc, mae, cel, senha, perfil in usuarios:
        conn.execute(
            "INSERT INTO usuarios (cpf, nome, nascimento, nome_mae, celular, senha_hash, perfil)"
            " VALUES (?,?,?,?,?,?,?)",
            (cpf, nome, nasc, mae, cel, hash_senha(senha), perfil),
        )
    contas = [(1, "0001", "00012345-6", 48312.77), (2, "0420", "00998877-1", 1020.10),
              (3, "0001", "00055566-7", 312900.00)]
    for uid, ag, num, saldo in contas:
        conn.execute(
            "INSERT INTO contas (usuario_id, agencia, numero, saldo, limite_diurno, limite_noturno)"
            " VALUES (?,?,?,?,?,?)", (uid, ag, num, saldo, 5000.0, 1000.0))
    for chave, num in [("+5511988887777", "00998877-1"), ("111.222.333-44", "00998877-1"),
                       ("maria@exemplo.com", "00012345-6"), ("555.666.777-88", "00055566-7")]:
        conn.execute("INSERT INTO chaves_pix VALUES (?,?)", (chave, num))
    # comprovantes começam em 100229 (IDs sequenciais — TM-08)
    conn.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('transacoes', 100228)")
    conn.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        conn = sqlite3.connect(app.config["DATABASE"])
        seed(conn)
        conn.close()
