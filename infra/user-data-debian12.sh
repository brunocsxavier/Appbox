#!/bin/bash
# cloud-init (user-data) para a EC2 Debian 12 (bookworm) do Core Box.
# Instala Docker Engine + plugin compose a partir do repositório oficial da Docker
# e cria o usuário "deploy" usado pela esteira.
set -euxo pipefail

apt-get update
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

useradd -m -s /bin/bash deploy || true
usermod -aG docker deploy
install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
# A chave pública de deploy do grupo é adicionada pelo professor (ver infra/README-infra.md)
touch /home/deploy/.ssh/authorized_keys
chown deploy:deploy /home/deploy/.ssh/authorized_keys
chmod 600 /home/deploy/.ssh/authorized_keys
install -d -o deploy -g deploy /opt/core-box
systemctl enable --now docker
