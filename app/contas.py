"""Home e extrato (tela T3 do Dia 01)."""
from flask import Blueprint, render_template, g, jsonify

from app.db import get_db
from app.seguranca import login_obrigatorio

bp = Blueprint("contas", __name__)


def conta_do_usuario(usuario_id):
    return get_db().execute("SELECT * FROM contas WHERE usuario_id = ?", (usuario_id,)).fetchone()


@bp.route("/home")
@login_obrigatorio()
def home():
    db = get_db()
    conta = conta_do_usuario(g.usuario["id"])
    disp = db.execute("SELECT * FROM dispositivos WHERE usuario_id = ? ORDER BY id DESC LIMIT 1",
                      (g.usuario["id"],)).fetchone()
    return render_template("home.html", usuario=g.usuario, conta=conta, dispositivo=disp)


@bp.route("/extrato")
@login_obrigatorio()
def extrato():
    conta = conta_do_usuario(g.usuario["id"])
    txs = get_db().execute(
        "SELECT * FROM transacoes WHERE conta_origem = ? OR conta_destino = ? ORDER BY id DESC LIMIT 50",
        (conta["numero"], conta["numero"])).fetchall()
    return render_template("extrato.html", usuario=g.usuario, conta=conta, transacoes=txs)


@bp.route("/api/v1/contas/minha")
@login_obrigatorio(api=True)
def api_minha_conta():
    c = conta_do_usuario(g.usuario["id"])
    return jsonify({"agencia": c["agencia"], "numero": c["numero"], "saldo": c["saldo"],
                    "limite_diurno": c["limite_diurno"], "limite_noturno": c["limite_noturno"]})
