# Registro de exceções de segurança — Core Box

> Toda exceção a um *security gate* da esteira precisa estar registrada aqui **e** referenciada no
> mecanismo técnico correspondente (`.gitleaksignore`, comentário `nosemgrep`, `.trivyignore`,
> `@pytest.mark.xfail`). Exceção sem registro = gate burlado = reprovação.

| ID | Gate | Achado (regra / CVE / teste) | Ameaça (TM) | Justificativa | Controle compensatório | Dono | Prazo | Aprovado por |
|---|---|---|---|---|---|---|---|---|
| EXC-001 | Gitleaks | `jwt` em `tests/fixtures/token_exemplo_expirado.txt` | N/A | JWT expirado/fictício mantido exclusivamente como fixture para testes automatizados; não representa credencial válida de produção | Supressão restrita ao fingerprint específico no `.gitleaksignore`; `tests/` continua sendo analisado; segredos reais continuam bloqueando a esteira | Grupo Core Box | 2026-11-30 | Líder do grupo |
