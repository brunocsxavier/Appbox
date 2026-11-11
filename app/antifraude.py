"""Cliente do antifraude (simulado no laboratório)."""
import logging
import os

log = logging.getLogger("box.antifraude")


class AntifraudeIndisponivel(Exception):
    pass


def _consultar_score(transacao):
    if os.getenv("BOX_ANTIFRAUDE_INDISPONIVEL") == "1":
        raise AntifraudeIndisponivel("timeout após 2s")
    score = 10
    descricao = (transacao.get("descricao") or "").lower()
    if any(p in descricao for p in ("urgente", "hospital", "sequestro", "presente")):
        score += 50
    if transacao["valor"] >= 10000:
        score += 30
    return score


def avaliar(transacao):
    """Retorna True se a transação pode seguir."""
    try:
        score = _consultar_score(transacao)
    except AntifraudeIndisponivel:
        # TM-32 (CWE-636): fail-open — "não podemos atrapalhar o cliente"
        log.warning("Antifraude indisponível, aprovando transação por padrão: %s", transacao)
        return True
    return score < 90
