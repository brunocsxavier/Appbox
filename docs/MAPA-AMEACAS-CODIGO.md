# Do Threat Model (Dia 01) ao código (Dia 02)

Este mapa liga cada ameaça modelada no Dia 01 ao lugar do código onde ela "mora" na versão v1.
Use-o para triagem: todo achado de ferramenta deve ser ligado a um TM-ID (ou virar um TM novo!).

| TM | Ameaça (Dia 01) | Onde está no código | Tela (Dia 01) | Quem deve pegar na esteira |
|---|---|---|---|---|
| TM-01 | Força bruta / credential stuffing | `app/auth.py::_autenticar` | T1-D | Teste abuse case (etapa 3) |
| TM-02 | ATO via recuperação / troca de celular | `app/auth.py::recuperar*`, `trocar_celular` | T2 | Revisão manual / Dia 03 |
| TM-03 | BOLA no Pix (`conta_origem`) | `app/pix.py::executar_pix` | T4-A | Semgrep (regra própria) + teste |
| TM-04 | `limite_override` | `app/pix.py::executar_pix` | T4-A/B | Regra própria + teste |
| TM-06 | Dados pessoais e tokens em log | `app/auditoria.py`, `app/pix.py` | — | Regra própria / revisão |
| TM-07 | Stack trace e debug | `app/__init__.py`, `app/config.py`, `wsgi.py` | T4-F, T1-E | Semgrep + teste + ZAP |
| TM-08 | Comprovante público sequencial | `app/pix.py::comprovante` | T5-B | Teste + ZAP |
| TM-10 | Ajuste sem maker-checker | `app/backoffice.py::ajuste` | T6-C | Teste |
| TM-11 | Limpar auditoria | `app/backoffice.py::limpar_auditoria` | T6-D | Revisão |
| TM-12 | MD5 para senha / hash exposto | `app/seguranca.py::hash_senha` | T6-E | Semgrep + teste |
| TM-15 | Segredos no código e no histórico | `app/config.py`, histórico do Git | — | Gitleaks (+ Semgrep/Trivy secret) |
| TM-16 | JWT HS256 fixo / decode sem verificar | `app/config.py`, `app/api_interna.py` | — | Semgrep |
| TM-17 | `verify=False` na integração PSTI | `app/psti_client.py` | — | Semgrep |
| TM-19 | DICT sem rate limit e com CPF | `app/pix.py::consulta_dict` | — | Dia 03 |
| TM-20 | Sem idempotência | `app/pix.py::executar_pix` | T4-F | Teste |
| TM-23 | Enumeração de CPF | `app/auth.py::_autenticar` | T1-A | Teste (+ regra própria bônus) |
| TM-25 | Vínculo automático de dispositivo | `app/auth.py::_vincular_dispositivo` | T3-E | Dia 03 |
| TM-28 | Upload sem validação / path traversal | `app/onboarding.py` | — | Semgrep |
| TM-29 | SQL injection na busca | `app/backoffice.py::painel` | T6-E | Semgrep + teste |
| TM-31 | Cadeia de suprimentos | `requirements.txt`, `Dockerfile`, esteira | — | Trivy fs/image + revisão da esteira |
| TM-32 | Antifraude fail-open | `app/antifraude.py::avaliar` | — | Revisão / Dia 03 |
| **NOVO?** | Injeção de comando no "diagnóstico" | `app/backoffice.py::diagnostico` | — | Semgrep — **não estava no Threat Model!** |
