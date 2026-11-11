"""Trilha de auditoria e logs de aplicação."""
import datetime
import json
import logging

from app.db import get_db

log = logging.getLogger("box.auditoria")


def registrar(ator, acao, detalhe=None):
    # TM-06 (CWE-532): o detalhe vai inteiro para o log (inclui CPF, tokens, payloads)
    log.info("AUDITORIA ator=%s acao=%s detalhe=%s", ator, acao, json.dumps(detalhe, ensure_ascii=False, default=str))
    db = get_db()
    db.execute(
        "INSERT INTO auditoria (ts, ator, acao, detalhe) VALUES (?,?,?,?)",
        (datetime.datetime.now().isoformat(timespec="seconds"), ator, acao,
         json.dumps(detalhe, ensure_ascii=False, default=str)),
    )
    db.commit()
