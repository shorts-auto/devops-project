# Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the cloud infrastructure to AWS.

## Prerequisites

### Software Requirements

```bash
# Verify installations
terraform -version        # >= 1.0
aws --version            # >= 2.0
docker --version         # >= 20.0
git --version            # >= 2.30
python --version         # >= 3.11
```

### AWS Account Setup

1. Create AWS account
2. Create IAM user with required permissions
3. Generate access keys
4. Save credentials securely

### Required Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "rds:*",
        "elasticloadbalancing:*",
        "autoscaling:*",
        "cloudwatch:*",
        "logs:*",
        "kms:*",
        "iam:*",
        "ecr:*",
        "secretsmanager:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Pre-Deployment Checklist

- [ ] AWS credentials configured
- [ ] Terraform installed and validated
- [ ] Docker installed
- [ ] Git repository initialized
- [ ] GitHub repository created
- [ ] AWS region selected
- [ ] Domain name available (for production)
- [ ] SSL certificate prepared (for production)

## Step 1: Infrastructure Setup (Terraform)

### 1.1 Configure AWS Credentials

```bash
# Option 1: Interactive configuration
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="ap-south-1"

# Option 3: AWS credentials file
cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = your-access-key
aws_secret_access_key = your-secret-key
EOF
```

### 1.2 Initialize Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Show current state
terraform state list
```

### 1.3 Plan Infrastructure Deployment

```bash
# For development environment
terraform plan -var-file=environments/dev.tfvars -out=tfplan_dev

# For production environment
terraform plan -var-file=environments/prod.tfvars -out=tfplan_prod
```

### 1.4 Review Plan

```bash
# Show plan details
terraform show tfplan_dev

# Key resources to verify:
# - VPC and subnets
# - Security groups
# - RDS instance
# - Auto Scaling Group
# - Load Balancer
```

### 1.5 Apply Infrastructure

```bash
# Deploy development environment
terraform apply tfplan_dev

# Output terraform outputs
terraform output -json > outputs_dev.json

# Note: This will take 10-15 minutes
```

### 1.6 Verify Deployment

```bash
# Get ALB DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)
echo "ALB DNS: $ALB_DNS"

# Get RDS endpoint
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
echo "RDS Endpoint: $RDS_ENDPOINT"

# Test ALB connectivity
curl http://$ALB_DNS/

# Verify RDS connectivity
psql -h $RDS_ENDPOINT -U admin -d appdb -c "SELECT version();"
```

## Step 2: Application Deployment

### 2.1 Build Docker Image

```bash
# Navigate to app directory
cd app

# Build image
docker build -t myapp:latest .

# Tag for ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <your-ecr-uri>
docker tag myapp:latest <your-ecr-uri>/myapp:latest
docker push <your-ecr-uri>/myapp:latest
```

### 2.2 Deploy to EC2 (Manual Process for Now)

```bash
# SSH into EC2 instance via Systems Manager Session Manager
aws ssm start-session --target <instance-id>

# Inside EC2 instance
cd /opt/app

# Pull Docker image
docker pull <your-ecr-uri>/myapp:latest

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.9'
services:
  app:
    image: <your-ecr-uri>/myapp:latest
    ports:
      - "8000:8000"
    environment:
      DB_HOST: <rds-endpoint>
      DB_NAME: appdb
      DB_USER: admin
      DB_PASSWORD: <password>
    restart: always
EOF

# Start application
docker-compose up -d

# Verify application
docker-compose logs -f app
```

### 2.3 Verify Application Health

```bash
# Test health endpoint
curl http://localhost:8000/

# Test readiness probe
curl http://localhost:8000/health/ready

# Check application logs
docker-compose logs app
```

## Step 3: Database Initialization

### 3.1 Connect to Database

```bash
# From EC2 instance or local machine
psql -h <rds-endpoint> -U admin -d appdb

# Alternative using AWS RDS Proxy
psql -h <rds-proxy-endpoint> -U admin -d appdb
```

### 3.2 Initialize Database

```bash
# From application
curl http://<alb-dns>/api/init-db

# This will create:
# - users table
# - default indexes
# - sample data (optional)
```

### 3.3 Verify Database

```sql
-- Connect to database
psql -h <rds-endpoint> -U admin -d appdb

-- List tables
\dt

-- Check table structure
\d users

-- Verify data
SELECT * FROM users LIMIT 5;
```

## Step 4: Load Balancer Configuration

### 4.1 Verify ALB Configuration

```bash
# Check ALB
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?LoadBalancerName==`myapp-alb-dev`]'

# Check target groups
aws elbv2 describe-target-groups \
  --load-balancer-arn <alb-arn>

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <tg-arn>
```

### 4.2 Configure HTTPS (Production)

```bash
# Request certificate (if not already done)
aws acm request-certificate \
  --domain-name myapp.example.com \
  --validation-method DNS

# Modify ALB listener to use HTTPS
aws elbv2 modify-listener \
  --listener-arn <listener-arn> \
  --protocol HTTPS \
  --certificates CertificateArn=<cert-arn>

# Add HTTP to HTTPS redirect
aws elbv2 modify-listener \
  --listener-arn <http-listener-arn> \
  --default-actions Type=redirect,RedirectConfig='{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}'
```

### 4.3 Update DNS

```bash
# Create Route 53 record (if using Route 53)
aws route53 change-resource-record-sets \
  --hosted-zone-id <zone-id> \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "myapp.example.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z35SXDOTRQ7X7K",
          "DNSName": "<alb-dns>",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }'
```

## Step 5: CI/CD Pipeline Setup

### 5.1 Push Repository to GitHub

```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit: cloud infrastructure"

# Add GitHub remote
git remote add origin https://github.com/your-username/myapp.git

# Push to GitHub
git push -u origin main
```

### 5.2 Configure GitHub Secrets

```bash
# Create secrets in GitHub repository settings
GitHub Settings → Secrets and Variables → Actions

Required secrets:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- SLACK_WEBHOOK (optional)
- DOCKER_REGISTRY_URL (optional)
- SONAR_TOKEN (optional)
```

### 5.3 Create Protected Branch Rules

```
Settings → Branches → Branch Protection Rules

main branch:
- [ ] Require pull request reviews before merging (1 review)
- [ ] Require status checks to pass before merging
  - CI/CD pipeline must pass
  - Tests must pass
  - Security scans must pass
- [ ] Require branches to be up to date before merging
- [ ] Require code quality checks
```

### 5.4 Test CI/CD Pipeline

```bash
# Create a test feature branch
git checkout -b test/ci-pipeline

# Make a change
echo "# Test" >> README.md

# Push branch
git push origin test/ci-pipeline

# Create pull request on GitHub
# Watch GitHub Actions pipeline run

# Verify:
# - Tests pass
# - Security scans pass
# - Docker image builds successfully
```

## Step 6: Monitoring & Logging Setup

### 6.1 Configure CloudWatch

```bash
# Create log groups
aws logs create-log-group --log-group-name /aws/myapp/application
aws logs create-log-group --log-group-name /aws/myapp/system
aws logs create-log-group --log-group-name /aws/myapp/alb

# Set retention policies
aws logs put-retention-policy \
  --log-group-name /aws/myapp/application \
  --retention-in-days 30
```

### 6.2 Create CloudWatch Dashboards

```bash
# Use AWS Console or CLI to create dashboards
aws cloudwatch put-dashboard \
  --dashboard-name myapp-dashboard \
  --dashboard-body file://dashboards/application.json
```

### 6.3 Set Up Alarms

```bash
# Create alarms for critical metrics
aws cloudwatch put-metric-alarm \
  --alarm-name myapp-high-cpu \
  --alarm-description "Alert when CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

## Step 7: Backup & Disaster Recovery

### 7.1 Verify Automated Backups

```bash
# Check RDS backups
aws rds describe-db-instances \
  --db-instance-identifier myapp-db-dev \
  --query 'DBInstances[0].[BackupRetentionPeriod,PreferredBackupWindow]'

# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier myapp-db-dev \
  --db-snapshot-identifier myapp-db-dev-manual-$(date +%Y%m%d)
```

### 7.2 Test Recovery Process

```bash
# List available snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier myapp-db-dev

# Restore from snapshot (to test)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier myapp-db-restore-test \
  --db-snapshot-identifier <snapshot-id>

# After testing, delete test instance
aws rds delete-db-instance \
  --db-instance-identifier myapp-db-restore-test \
  --skip-final-snapshot
```

## Step 8: Post-Deployment Testing

### 8.1 Smoke Tests

```bash
# Test application endpoints
curl -I http://<alb-dns>/
curl -I http://<alb-dns>/health/ready
curl -I http://<alb-dns>/api/status
curl -I http://<alb-dns>/metrics

# Expected status codes: 200
```

### 8.2 Load Testing

```bash
# Install Apache Bench
apt-get install apache2-utils

# Run load test
ab -n 1000 -c 10 http://<alb-dns>/

# Monitor metrics during test
watch -n 1 'aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=myapp-asg-dev \
  --start-time $(date -u -d "5 minutes ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average'
```

### 8.3 Failover Testing

```bash
# For RDS multi-AZ
# Manually trigger failover to test
aws rds reboot-db-instance \
  --db-instance-identifier myapp-db-prod \
  --force-failover

# Application should remain available
# Monitor application logs and metrics
```

## Step 9: Documentation & Handover

### 9.1 Create Operational Runbooks

- Application deployment runbook
- Incident response procedures
- Scaling procedures
- Backup/recovery procedures

### 9.2 Team Training

- Infrastructure overview
- Monitoring and alerting
- Deployment procedures
- Incident response
- Troubleshooting common issues

### 9.3 Documentation

- Architecture diagrams
- Network diagrams
- Security documentation
- Cost analysis

## Troubleshooting Deployment Issues

### Terraform Issues

```bash
# Show detailed error
terraform apply -var-file=environments/dev.tfvars -no-color 2>&1 | tee terraform.log

# Refresh state if diverged
terraform refresh -var-file=environments/dev.tfvars

# Show resources
terraform state list
terraform state show aws_lb.app
```

### EC2 Instance Issues

```bash
# Check instance status
aws ec2 describe-instances --instance-ids <instance-id>

# View user data execution logs
aws ec2 get-console-output --instance-id <instance-id>

# Connect via Systems Manager
aws ssm start-session --target <instance-id>
```

### RDS Connectivity Issues

```bash
# Check security group
aws ec2 describe-security-groups --group-ids <sg-id>

# Test connection from EC2
telnet <rds-endpoint> 5432

# Check RDS logs
aws rds describe-db-log-files --db-instance-identifier myapp-db-dev
```

## Deployment Checklist

- [ ] AWS credentials configured
- [ ] Terraform initialized and validated
- [ ] Infrastructure deployed
- [ ] Docker image built and pushed to ECR
- [ ] Application deployed to EC2
- [ ] Database initialized
- [ ] ALB configured and verified
- [ ] CI/CD pipeline configured
- [ ] Monitoring and logging set up
- [ ] Backups verified
- [ ] Smoke tests passed
- [ ] Team trained
- [ ] Documentation completed
- [ ] Runbooks created

## Next Steps

1. Monitor application performance
2. Optimize based on metrics
3. Implement additional features
4. Plan capacity upgrades
5. Schedule regular reviews
