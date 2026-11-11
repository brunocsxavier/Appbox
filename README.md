# Core Box — Core Bancário do Banco Box (v1, laboratório)

> ⚠️ **Aplicação intencionalmente vulnerável**, criada para o Projeto Integrador DevSecOps (Dia 02).
> Todos os dados, CPFs, chaves e segredos são **fictícios**. Não exponha esta aplicação além do ambiente do curso.

## O que é
Implementação funcional (Python 3 / Flask) do Core Box modelado no Dia 01: login, recuperação de senha,
home/extrato, Pix (envio, DICT, comprovante), abertura de conta (KYC) e backoffice das agências.
As telas reproduzem os protótipos T1–T6 analisados no Tour de UX Security.

## Rodar localmente
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python wsgi.py                      # http://localhost:8000
pytest                              # testes funcionais + abuse cases
```
Ou com Docker: `docker compose up --build`.

## Usuários de teste
| Perfil | Login | Senha |
|---|---|---|
| Cliente — Maria | CPF `987.654.321-00` | `123456` |
| Cliente — João | CPF `111.222.333-44` | `246810` |
| Cliente — Ana | CPF `555.666.777-88` | `123456` |
| Operador backoffice | usuário `admin` (em `/backoffice/login`) | `admin123` |

Chaves Pix: `+5511988887777` e `111.222.333-44` (João), `maria@exemplo.com` (Maria), `555.666.777-88` (Ana).

## Estrutura
```
app/            código da aplicação (Flask, blueprints por domínio)
app/templates/  telas (T1–T6 do Dia 01)
config/         configuração não sensível (YAML)
tests/          testes funcionais e abuse cases (critérios de aceite do Threat Model)
.semgrep/       regras SAST próprias do banco (derivadas do Threat Model)
deploy/         compose e script de deploy na VPS Debian
infra/          provisionamento da VPS (uso do professor)
docs/           mapa ameaça → código
EXCECOES.md     registro formal de exceções aos security gates
```

## API (principais rotas)
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/auth/login` | `{cpf, senha}` → JWT |
| GET | `/api/v1/contas/minha` | Saldo e limites |
| POST | `/api/v1/pix/transferencias` | `{chave, valor, descricao}` (+ header `Idempotency-Key`) |
| GET | `/api/v1/pix/dict/<chave>` | Consulta de chave |
| GET | `/comprovantes/<id>` | Comprovante |
| GET | `/health` | Saúde |

## Sua missão (Dia 02)
Construir a esteira CI/CD de 8 etapas no GitHub Actions, fazê-la **barrar** esta versão e corrigir o Core Box
até que ele chegue à produção na VPS — com aprovação manual. Detalhes no Caderno do Aluno.
