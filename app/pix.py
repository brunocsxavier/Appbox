"""Pix: envio, consulta de chave (DICT) e comprovante (telas T4 e T5 do Dia 01)."""
import datetime
import logging
from decimal import Decimal, InvalidOperation

from flask import Blueprint, current_app, render_template, request, g, jsonify, redirect

from app import antifraude, auditoria, psti_client
from app.contas import conta_do_usuario
from app.db import get_db
from app.seguranca import login_obrigatorio

bp = Blueprint("pix", __name__)
log = logging.getLogger("box.pix")


class ErroPix(Exception):
    def __init__(self, mensagem, status=422):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def _limite_vigente(conta, agora=None):
    agora = agora or datetime.datetime.now()
    noturno = agora.hour >= 20 or agora.hour < 6
    return conta["limite_noturno"] if noturno else conta["limite_diurno"]


def _converter_valor(valor_informado):
    """Converte e valida o valor sem expor excecoes internas."""
    try:
        valor = Decimal(str(valor_informado))
    except (InvalidOperation, TypeError, ValueError):
        raise ErroPix("Valor invalido.", 400)

    if not valor.is_finite() or valor <= 0:
        raise ErroPix("Valor invalido.", 400)

    if valor.as_tuple().exponent < -2:
        raise ErroPix("Valor invalido.", 400)

    return valor


def _mascarar_cpf(cpf):
    numeros = "".join(c for c in str(cpf) if c.isdigit())
    if len(numeros) != 11:
        return "***"
    return f"***.***.***-{numeros[-2:]}"


def executar_pix(usuario, dados, idempotency_key=None):
    db = get_db()

    # TM-06: nao registrar payload, CPF completo, token ou Authorization.
    log.info(
        "Pix solicitado usuario_id=%s",
        usuario["id"],
    )

    # TM-03: a conta de origem e determinada pelo usuario autenticado.
    conta_usuario = conta_do_usuario(usuario["id"])
    if conta_usuario is None:
        log.warning("Usuario autenticado sem conta associada usuario_id=%s", usuario["id"])
        raise ErroPix("Conta de origem nao encontrada.", 403)

    conta_origem = conta_usuario["numero"]
    conta_informada = dados.get("conta_origem")

    # Tentativa de usar conta de terceiro e um evento de seguranca.
    if conta_informada and str(conta_informada) != str(conta_origem):
        log.warning(
            "Tentativa de Pix com conta de terceiro usuario_id=%s",
            usuario["id"],
        )
        auditoria.registrar(
            _mascarar_cpf(usuario["cpf"]),
            "PIX_CONTA_ORIGEM_INVALIDA",
            {"usuario_id": usuario["id"]},
        )
        raise ErroPix("Operacao nao autorizada.", 403)

    origem = db.execute(
        "SELECT * FROM contas WHERE numero = ? AND usuario_id = ?",
        (conta_origem, usuario["id"]),
    ).fetchone()
    if origem is None:
        raise ErroPix("Conta de origem nao encontrada.", 403)

    # TM-07: entrada invalida nao pode gerar stack trace para o cliente.
    valor_decimal = _converter_valor(dados.get("valor"))
    valor = float(valor_decimal)

    chave = str(dados.get("chave") or "").strip()
    if not chave:
        raise ErroPix("Chave Pix invalida.", 400)

    destino_num = db.execute(
        "SELECT conta_numero FROM chaves_pix WHERE chave = ?",
        (chave,),
    ).fetchone()
    if destino_num is None:
        raise ErroPix("Chave Pix nao encontrada no DICT.", 404)

    destino = db.execute(
        "SELECT * FROM contas WHERE numero = ?",
        (destino_num[0],),
    ).fetchone()
    if destino is None:
        raise ErroPix("Conta de destino nao encontrada.", 404)

    # TM-04: limite_override enviado pelo cliente e ignorado.
    limite = float(_limite_vigente(origem))
    if valor > limite:
        raise ErroPix(f"Valor acima do seu limite atual de R$ {limite:.2f}.")

    if not antifraude.avaliar(
        {
            "valor": valor,
            "descricao": dados.get("descricao"),
            "cpf": usuario["cpf"],
        }
    ):
        raise ErroPix("Transacao nao autorizada pela analise de seguranca.", 403)

    if float(origem["saldo"]) < valor:
        raise ErroPix("Saldo insuficiente.")

    # TM-20: se uma chave ja foi processada para a conta, devolve a mesma transacao.
    if idempotency_key:
        existente = db.execute(
            "SELECT id, e2e, valor FROM transacoes "
            "WHERE conta_origem = ? AND idempotency_key = ?",
            (origem["numero"], idempotency_key),
        ).fetchone()
        if existente is not None:
            return {
                "id": existente["id"],
                "e2e": existente["e2e"],
                "valor": existente["valor"],
                "comprovante": f"/comprovantes/{existente['id']}",
            }

    try:
        # Debito condicional reduz risco de corrida por saldo.
        debito = db.execute(
            "UPDATE contas SET saldo = saldo - ? "
            "WHERE numero = ? AND usuario_id = ? AND saldo >= ?",
            (valor, origem["numero"], usuario["id"], valor),
        )
        if debito.rowcount != 1:
            db.rollback()
            raise ErroPix("Saldo insuficiente.")

        db.execute(
            "UPDATE contas SET saldo = saldo + ? WHERE numero = ?",
            (valor, destino["numero"]),
        )

        e2e = psti_client.enviar_pacs008(
            {
                "origem": origem["numero"],
                "destino": destino["numero"],
                "valor": valor,
            }
        )

        cur = db.execute(
            "INSERT INTO transacoes "
            "(e2e, conta_origem, conta_destino, valor, descricao, idempotency_key, criado_em) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                e2e,
                origem["numero"],
                destino["numero"],
                valor,
                dados.get("descricao"),
                idempotency_key,
                datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        db.commit()
    except ErroPix:
        raise
    except Exception:
        db.rollback()
        current_app.logger.exception(
            "Falha interna ao processar Pix usuario_id=%s",
            usuario["id"],
        )
        raise ErroPix("Nao foi possivel concluir a transferencia.", 500)

    tx_id = cur.lastrowid
    auditoria.registrar(
        _mascarar_cpf(usuario["cpf"]),
        "PIX_ENVIADO",
        {
            "id": tx_id,
            "e2e": e2e,
            "conta_origem": origem["numero"],
            "conta_destino": destino["numero"],
            "valor": valor,
        },
    )

    return {
        "id": tx_id,
        "e2e": e2e,
        "valor": valor,
        "comprovante": f"/comprovantes/{tx_id}",
    }


@bp.route("/pix", methods=["GET", "POST"])
@login_obrigatorio()
def pix_web():
    conta = conta_do_usuario(g.usuario["id"])
    if conta is None:
        return render_template(
            "pix.html",
            usuario=g.usuario,
            conta=None,
            erro="Conta nao encontrada.",
        ), 403

    if request.method == "GET":
        return render_template(
            "pix.html",
            usuario=g.usuario,
            conta=conta,
            conta_origem=conta["numero"],
            limite=_limite_vigente(conta),
        )

    try:
        resultado = executar_pix(
            g.usuario,
            request.form.to_dict(),
            request.headers.get("Idempotency-Key"),
        )
    except ErroPix as e:
        return render_template(
            "pix.html",
            usuario=g.usuario,
            conta=conta,
            conta_origem=conta["numero"],
            limite=_limite_vigente(conta),
            erro=e.mensagem,
        ), e.status

    return redirect(resultado["comprovante"])


@bp.route("/api/v1/pix/transferencias", methods=["POST"])
@login_obrigatorio(api=True)
def pix_api():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"erro": "Requisicao JSON invalida."}), 400

    try:
        resultado = executar_pix(
            g.usuario,
            dados,
            request.headers.get("Idempotency-Key"),
        )
    except ErroPix as e:
        return jsonify({"erro": e.mensagem}), e.status

    return jsonify(resultado), 201


@bp.route("/api/v1/pix/dict/<path:chave>")
@login_obrigatorio(api=True)
def consulta_dict(chave):
    # TM-19 permanece fora do conjunto must-fix desta alteracao.
    row = get_db().execute(
        "SELECT u.nome, u.cpf, c.agencia, c.numero "
        "FROM chaves_pix k JOIN contas c ON c.numero = k.conta_numero "
        "JOIN usuarios u ON u.id = c.usuario_id WHERE k.chave = ?",
        (chave,),
    ).fetchone()
    if not row:
        return jsonify({"erro": "Chave nao encontrada"}), 404

    resultado = dict(row)
    resultado["cpf"] = _mascarar_cpf(resultado.get("cpf"))
    return jsonify(resultado)


@bp.route("/comprovantes/<int:tx_id>")
@login_obrigatorio()
def comprovante(tx_id):
    # TM-08: exige autenticacao e restringe o comprovante as contas do usuario.
    db = get_db()
    conta_usuario = conta_do_usuario(g.usuario["id"])
    if conta_usuario is None:
        return render_template("comprovante.html", tx=None), 404

    tx = db.execute(
        "SELECT * FROM transacoes WHERE id = ? "
        "AND (conta_origem = ? OR conta_destino = ?)",
        (tx_id, conta_usuario["numero"], conta_usuario["numero"]),
    ).fetchone()
    if tx is None:
        return render_template("comprovante.html", tx=None), 404

    def titular(numero):
        row = db.execute(
            "SELECT u.nome, u.cpf, c.agencia, c.numero "
            "FROM contas c JOIN usuarios u ON u.id = c.usuario_id "
            "WHERE c.numero = ?",
            (numero,),
        ).fetchone()
        if row is None:
            return None
        return {
            "nome": row["nome"],
            "cpf": _mascarar_cpf(row["cpf"]),
            "agencia": row["agencia"],
            "numero": row["numero"],
        }

    return render_template(
        "comprovante.html",
        tx=tx,
        origem=titular(tx["conta_origem"]),
        destino=titular(tx["conta_destino"]),
        base_url=request.host_url,
    )
