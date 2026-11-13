"""Endpoints internos usados entre serviços."""

import jwt
from flask import Blueprint, current_app, request, jsonify

bp = Blueprint("interna", __name__, url_prefix="/api/v1/interno")


@bp.route("/token-info")
def token_info():
    token = request.args.get("token", "").strip()

    if not token:
        return jsonify({"erro": "Token não informado."}), 401

    try:
        dados = jwt.decode(
            token,
            current_app.config["JWT_SECRET"],
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return jsonify({"erro": "Token inválido ou expirado."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"erro": "Token inválido ou expirado."}), 401

    return jsonify(dados)
