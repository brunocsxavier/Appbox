"""Integração com o PSTI (SPI/DICT). No laboratório opera em modo simulado."""
import logging
import os
import uuid
import datetime

import requests
from flask import current_app

log = logging.getLogger("box.psti")


def _gerar_e2e():
    agora = datetime.datetime.now().strftime("%Y%m%d%H%M")
    return f"E00000000{agora}{uuid.uuid4().hex[:11].upper()}"


def enviar_pacs008(transacao):
    """Envia a ordem de pagamento ao SPI via PSTI."""
    e2e = _gerar_e2e()
    if os.getenv("BOX_PSTI_MODO", "simulado") == "real":
        # TM-17: validação de certificado desligada "porque o certificado de homologação é autoassinado"
        resp = requests.post(
            current_app.config["PSTI_URL"] + "/pacs008",
            json={**transacao, "endToEndId": e2e},
            headers={"X-Api-Key": current_app.config["PSTI_API_KEY"]},
            verify=False,
            timeout=5,
        )
        resp.raise_for_status()
    log.info("pacs.008 enviado e2e=%s payload=%s", e2e, transacao)
    return e2e
