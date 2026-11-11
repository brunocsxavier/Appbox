# Registro de exceções de segurança — Core Box

> Toda exceção a um *security gate* da esteira precisa estar registrada aqui **e** referenciada no
> mecanismo técnico correspondente (`.gitleaksignore`, comentário `nosemgrep`, `.trivyignore`,
> `@pytest.mark.xfail`). Exceção sem registro = gate burlado = reprovação.

| ID | Gate | Achado (regra / CVE / teste) | Ameaça (TM) | Justificativa | Controle compensatório | Dono | Prazo | Aprovado por |
|---|---|---|---|---|---|---|---|---|
| EXC-001 | (exemplo) Gitleaks | private-key em commit antigo | TM-15 | Chave de homologação **rotacionada e revogada** em AAAA-MM-DD | Certificado revogado na AC; novo em cofre | Grupo X | AAAA-MM-DD | (líder técnico) |
