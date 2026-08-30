#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
apt-get install -y docker.io
systemctl start docker
systemctl enable docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb

# Install PostgreSQL client
apt-get install -y postgresql-client

# Create application directory
mkdir -p /opt/app
cd /opt/app

# Create environment file
cat > .env << EOF
DB_HOST=${DB_HOST}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
ENVIRONMENT=production
EOF

# Log startup
echo "EC2 instance initialized at $(date)" >> /var/log/startup.log
