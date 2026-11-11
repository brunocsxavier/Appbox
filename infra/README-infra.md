# Infraestrutura do Dia 02 — VPS Debian 12 na AWS

> Responsável: **professor** (antes da aula). Os alunos recebem: IP da VPS, usuário `deploy` e a orientação de gerar o par de chaves de deploy.

## 1. Provisionar uma VPS por grupo
```bash
./infra/provisionar-ec2.sh grupo01 sa-east-1
```
Cria: Security Group (80 e 22 abertos), par de chaves administrativo, EC2 `t3.small` Debian 12 com IMDSv2 obrigatório e disco cifrado, e executa `user-data-debian12.sh` (Docker Engine + compose + usuário `deploy`).

## 2. Chave de deploy do grupo
O grupo gera um par **exclusivo para a esteira** e envia ao professor apenas a chave **pública**:
```bash
ssh-keygen -t ed25519 -C "deploy-corebox-grupo01" -f deploy_corebox -N ""
```
O professor adiciona `deploy_corebox.pub` em `/home/deploy/.ssh/authorized_keys` da VPS do grupo.
A chave **privada** vira um *secret do Environment `producao`* no GitHub (nunca do repositório inteiro).

## 3. Copiar os arquivos de deploy para a VPS (feito pela esteira ou uma vez, manualmente)
```bash
scp -i deploy_corebox deploy/* deploy@<IP>:/opt/core-box/
```

## 4. Riscos conscientemente aceitos no Dia 02 (registrados em EXCECOES.md)
| Ameaça | Situação no Dia 02 | Tratamento planejado |
|---|---|---|
| TM-14 SSH exposto | Porta 22 aberta para o deploy via GitHub Actions | Dia 04: AWS SSM + OIDC, sem porta 22 |
| TM-13/TM-18 | App em HTTP na porta 80, VM única | Dia 04: ALB + TLS + WAF + desenho multi-AZ |
| TM-15 | Segredos de deploy em GitHub Secrets | Dia 04: OIDC + Secrets Manager |
