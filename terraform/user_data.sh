#!/bin/bash
set -euo pipefail

# Update system
apt-get update
apt-get upgrade -y

# Install runtime dependencies
apt-get install -y docker.io awscli postgresql-client curl
systemctl start docker
systemctl enable docker

# Install and enable the Systems Manager agent for remote deployments.
if command -v snap >/dev/null 2>&1; then
  snap list amazon-ssm-agent >/dev/null 2>&1 || snap install amazon-ssm-agent --classic
  snap start amazon-ssm-agent
else
  curl -fsSL "https://s3.${AWS_REGION}.amazonaws.com/amazon-ssm-${AWS_REGION}/latest/debian_amd64/amazon-ssm-agent.deb" -o /tmp/amazon-ssm-agent.deb
  dpkg -i /tmp/amazon-ssm-agent.deb
  systemctl enable --now amazon-ssm-agent
fi

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb

dpkg -i -E ./amazon-cloudwatch-agent.deb

# Create application directory
mkdir -p /opt/app
cd /opt/app

# Use the shared production secret so the app and RDS credentials stay aligned.
if [ -n "${DB_SECRET_NAME}" ]; then
  DB_PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id "${DB_SECRET_NAME}" \
    --query SecretString --output text)
fi

# Create environment file
cat > .env << EOF
DB_HOST=${DB_HOST}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=$${DB_PASSWORD}
DB_PORT=5432
ENVIRONMENT=production
EOF
chmod 600 .env

# Create a docker-compose file that runs the app container and exposes the ALB health endpoint
cat > docker-compose.yml <<EOF
services:
  app:
    image: ${APP_NAME}:latest
    container_name: myapp
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      DB_PORT: 5432
      FLASK_ENV: production
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8000/health/ready >/dev/null || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF

# Resolve the ECR registry and pull the latest app image before starting the service.
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || true)
if [ -n "$${ACCOUNT_ID}" ] && [ "$${ACCOUNT_ID}" != "None" ]; then
  ECR_REGISTRY="$${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
  aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "$${ECR_REGISTRY}"
  docker pull "$${ECR_REGISTRY}/${APP_NAME}:latest" || true
  sed -i "s|image: .*|image: $${ECR_REGISTRY}/${APP_NAME}:latest|" docker-compose.yml
fi

# Start the application so the ALB target health checks can pass.
docker-compose up -d --force-recreate

docker-compose ps

echo "EC2 instance initialized at $(date)" >> /var/log/startup.log
