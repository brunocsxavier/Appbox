"""Endpoints "internos" usados entre serviços (TM-16: sem autenticação entre serviços)."""
import jwt
from flask import Blueprint, request, jsonify

bp = Blueprint("interna", __name__, url_prefix="/api/v1/interno")


@bp.route("/token-info")
def token_info():
    token = request.args.get("token", "")
    # TM-16 (CWE-347): decodifica o JWT sem verificar a assinatura
    dados = jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])
    return jsonify(dados)
