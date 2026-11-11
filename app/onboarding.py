"""Abertura de conta digital / KYC."""
import os

from flask import Blueprint, render_template, request, current_app, Response

from app import auditoria

bp = Blueprint("onboarding", __name__)


@bp.route("/abrir-conta", methods=["GET", "POST"])
def abrir_conta():
    if request.method == "GET":
        return render_template("abrir_conta.html")
    cpf = request.form.get("cpf", "")
    salvos = []
    os.makedirs(current_app.config["UPLOAD_DIR"], exist_ok=True)
    for campo in ("documento", "selfie"):
        arq = request.files.get(campo)
        if arq is None or arq.filename == "":
            continue
        # TM-28 (CWE-434 / CWE-22): nome original, sem validar tipo, tamanho ou caminho
        destino = os.path.join(current_app.config["UPLOAD_DIR"], arq.filename)
        arq.save(destino)
        salvos.append("/uploads/" + arq.filename)
    auditoria.registrar(cpf, "KYC_UPLOAD", {"cpf": cpf, "arquivos": salvos})
    return render_template("abrir_conta.html", enviados=salvos)


@bp.route("/uploads/<path:nome>")
def ver_upload(nome):
    # TM-09: documentos e selfies públicos, sem autenticação; leitura com caminho controlado pelo usuário
    caminho = os.path.join(current_app.config["UPLOAD_DIR"], nome)
    with open(caminho, "rb") as f:
        return Response(f.read(), mimetype="application/octet-stream")
