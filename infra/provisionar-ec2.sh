#!/usr/bin/env bash
# Provisiona UMA VPS Debian 12 por grupo (executado pelo PROFESSOR antes da aula).
# Requer AWS CLI v2 autenticado. Uso: ./provisionar-ec2.sh grupo01 sa-east-1
# Observação: Terraform + Checkov chegam no Dia 04 — aqui é provisionamento "artesanal" de propósito.
set -euo pipefail
GRUPO="${1:?nome do grupo}"; REGIAO="${2:-sa-east-1}"
DEBIAN_OWNER="136693071363"   # conta oficial do projeto Debian na AWS

AMI=$(aws ec2 describe-images --region "$REGIAO" --owners "$DEBIAN_OWNER" \
  --filters "Name=name,Values=debian-12-amd64-*" "Name=architecture,Values=x86_64" \
  --query 'sort_by(Images,&CreationDate)[-1].ImageId' --output text)
VPC=$(aws ec2 describe-vpcs --region "$REGIAO" --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)

SG=$(aws ec2 create-security-group --region "$REGIAO" --vpc-id "$VPC" \
  --group-name "corebox-$GRUPO" --description "Core Box $GRUPO (Dia 02)" --query GroupId --output text)
# HTTP público para o app; SSH aberto para o deploy pela esteira (risco ACEITO e registrado: TM-14 -> Dia 04)
aws ec2 authorize-security-group-ingress --region "$REGIAO" --group-id "$SG" --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --region "$REGIAO" --group-id "$SG" --protocol tcp --port 22 --cidr 0.0.0.0/0

aws ec2 create-key-pair --region "$REGIAO" --key-name "corebox-$GRUPO-admin" \
  --query KeyMaterial --output text > "corebox-$GRUPO-admin.pem"
chmod 600 "corebox-$GRUPO-admin.pem"

ID=$(aws ec2 run-instances --region "$REGIAO" --image-id "$AMI" --instance-type t3.small \
  --key-name "corebox-$GRUPO-admin" --security-group-ids "$SG" \
  --user-data file://"$(dirname "$0")/user-data-debian12.sh" \
  --metadata-options HttpTokens=required,HttpEndpoint=enabled \
  --block-device-mappings 'DeviceName=/dev/xvda,Ebs={VolumeSize=20,Encrypted=true}' \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=corebox-$GRUPO},{Key=Projeto,Value=DevSecOps-Box}]" \
  --query 'Instances[0].InstanceId' --output text)
aws ec2 wait instance-running --region "$REGIAO" --instance-ids "$ID"
IP=$(aws ec2 describe-instances --region "$REGIAO" --instance-ids "$ID" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "Grupo $GRUPO: instancia $ID IP $IP (usuario admin com corebox-$GRUPO-admin.pem)"
