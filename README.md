# Cloud Infrastructure DevOps Assignment

A comprehensive DevOps infrastructure project demonstrating end-to-end cloud deployment, CI/CD automation, monitoring, and best practices.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Infrastructure Setup](#infrastructure-setup)
- [Local Development](#local-development)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring and Logging](#monitoring-and-logging)
- [Security Considerations](#security-considerations)
- [Cost Optimization](#cost-optimization)
- [Backup and Disaster Recovery](#backup-and-disaster-recovery)
- [Troubleshooting](#troubleshooting)

## 🎯 Project Overview

This project demonstrates a production-ready DevOps setup including:

- **Infrastructure as Code (IaC)**: Terraform configuration for AWS infrastructure
- **Containerization**: Docker and Docker Compose for application deployment
- **CI/CD Automation**: GitHub Actions pipeline with testing, building, and deployment
- **Monitoring & Logging**: Prometheus, Grafana, and CloudWatch integration
- **Security**: Security group management, encryption, vulnerability scanning
- **Scalability**: Auto Scaling Groups with load balancing
- **High Availability**: Multi-AZ deployment with RDS replication
- **Best Practices**: Secrets management, backup strategies, documentation

## 🏗️ Architecture

### Infrastructure Components

```
AWS Account
├── VPC (10.0.0.0/16)
│   ├── Public Subnets (2)
│   │   ├── Internet Gateway
│   │   └── NAT Gateway
│   ├── Private Subnets (2)
│   │   ├── Auto Scaling Group (EC2)
│   │   │   └── Application (Flask)
│   │   └── RDS PostgreSQL
│   └── Application Load Balancer
│       └── Target Groups
└── CloudWatch (Monitoring)
    ├── Metrics
    └── Logs
```

### Technology Stack

| Component | Technology |
|-----------|-----------|
| Infrastructure | Terraform |
| Cloud Provider | AWS |
| Compute | EC2 (Auto Scaling) |
| Database | RDS PostgreSQL |
| Load Balancing | ALB |
| Container Runtime | Docker |
| CI/CD | GitHub Actions |
| Monitoring | CloudWatch + Prometheus |
| Visualization | Grafana |
| Application | Python Flask |

## 📋 Prerequisites

### Required Tools

- **AWS Account** with appropriate permissions
- **Terraform** >= 1.0
- **AWS CLI** v2
- **Docker** and **Docker Compose**
- **Python** 3.11+
- **Git**
- **Node.js/npm** (for certain tools)

### AWS Permissions Required

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
        "ecr:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## 📁 Project Structure

```
.
├── terraform/
│   ├── provider.tf              # AWS provider configuration
│   ├── variables.tf             # Input variables
│   ├── vpc.tf                   # VPC and networking
│   ├── security_groups.tf       # Security group definitions
│   ├── ec2.tf                   # EC2 and Auto Scaling
│   ├── rds.tf                   # RDS database setup
│   ├── outputs.tf               # Output values
│   ├── user_data.sh             # EC2 initialization script
│   ├── environments/
│   │   ├── dev.tfvars           # Development environment variables
│   │   └── prod.tfvars          # Production environment variables
│   └── terraform.tfvars         # Default variables
├── app/
│   ├── app.py                   # Flask application
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Container image definition
│   └── tests/
│       └── test_app.py          # Unit tests
├── docker-compose.yml           # Local development stack
├── monitoring/
│   ├── prometheus.yml           # Prometheus configuration
│   └── grafana/                 # Grafana dashboards and provisioning
├── .github/
│   └── workflows/
│       └── ci-cd.yml            # GitHub Actions CI/CD pipeline
├── docs/
│   ├── ARCHITECTURE.md          # Detailed architecture documentation
│   ├── DEPLOYMENT.md            # Deployment procedures
│   ├── SECURITY.md              # Security considerations
│   └── TROUBLESHOOTING.md       # Common issues and solutions
└── README.md                    # This file
```

## 🚀 Infrastructure Setup

### 1. Configure AWS Credentials

```bash
# Using AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="ap-south-1"
```

### 2. Initialize Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive
```

### 3. Plan Infrastructure

```bash
# For development environment
terraform plan -var-file=environments/dev.tfvars -out=tfplan

# For production environment
terraform plan -var-file=environments/prod.tfvars -out=tfplan
```

### 4. Apply Infrastructure

```bash
# Apply the plan
terraform apply tfplan

# Save outputs for reference
terraform output -json > outputs.json
```

### 5. Verify Deployment

```bash
# Check RDS instance status
aws rds describe-db-instances --query 'DBInstances[0].DBInstanceStatus'

# Get ALB DNS name
terraform output alb_dns_name
```

## 🐳 Local Development

### Using Docker Compose

```bash
# Start all services (PostgreSQL, Flask app, Prometheus, Grafana)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild images
docker-compose up -d --build
```

### Accessing Services Locally

- **Application**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **PostgreSQL**: localhost:5432

### Development Commands

```bash
# Install dependencies
pip install -r app/requirements.txt

# Run tests
pytest app/tests/ -v

# Run linting
flake8 app/

# Build Docker image
docker build -t myapp:latest -f app/Dockerfile app/

# Run application locally
flask --app app.py run --host=0.0.0.0 --port=8000
```

## 🔄 CI/CD Pipeline

### Pipeline Stages

1. **Test Stage**
   - Run unit tests
   - Code coverage analysis
   - Linting and code quality checks

2. **Security Scanning Stage**
   - Trivy vulnerability scanning
   - Dependency vulnerability checks
   - SAST (Static Application Security Testing)

3. **Build Stage**
   - Build Docker image
   - Push to AWS ECR
   - Scan image for vulnerabilities

4. **Staging Deployment**
   - Triggered on `develop` branch
   - Deploy to staging environment
   - Run smoke tests

5. **Production Deployment**
   - Triggered on `main` branch
   - Requires manual approval
   - Blue-green deployment
   - Smoke tests

### Triggering Deployments

```bash
# Push to develop branch for staging deployment
git push origin develop

# Create pull request to main
git pull-request

# After approval, merge to main for production deployment
git merge develop
git push origin main
```

### GitHub Secrets Required

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
TELEGRAM_BOT_TOKEN     # Optional, for notifications
TELEGRAM_CHAT_ID       # Optional, for notifications
DOCKER_REGISTRY_URL
```

## 📊 Monitoring and Logging

### CloudWatch Metrics

- **Infrastructure Metrics**
  - CPU Utilization
  - Memory Utilization
  - Disk I/O
  - Network Traffic

- **Application Metrics**
  - Request Rate
  - Error Rate
  - Response Latency
  - Custom Business Metrics

### Prometheus Metrics

```
# Access Prometheus
curl http://localhost:9090

# Query metrics
curl 'http://localhost:9090/api/v1/query?query=application_info'
```

### Grafana Dashboards

Pre-configured dashboards:
1. **Application Performance Dashboard**
   - Request rate, error rate, latency
   - CPU and memory usage
   - Database connections

2. **Infrastructure Dashboard**
   - EC2 instance metrics
   - RDS performance
   - ALB metrics

3. **Database Dashboard**
   - Query performance
   - Replication lag
   - Storage usage

### Accessing Logs

```bash
# CloudWatch Logs
aws logs tail /aws/rds/instance/myapp-db/postgresql --follow

# Application logs
aws logs tail /aws/ec2/myapp --follow

# ALB access logs
aws logs tail /aws/alb/myapp --follow
```

## 🔒 Security Considerations

### Security Best Practices Implemented

1. **Network Segmentation**
   - Public subnets for load balancers
   - Private subnets for application and database
   - Security groups with least privilege

2. **Encryption**
   - RDS encryption at rest (KMS)
   - Secrets Manager for sensitive data
   - TLS/SSL for data in transit

3. **Access Control**
   - IAM roles for EC2 instances
   - Database credentials in AWS Secrets Manager
   - VPC endpoints for private access

4. **Vulnerability Scanning**
   - Trivy container image scanning
   - Dependency scanning with Safety
   - SAST in CI/CD pipeline

5. **Monitoring and Logging**
   - CloudWatch Logs for all services
   - VPC Flow Logs
   - CloudTrail for API auditing

### Secrets Management

```bash
# Store database password in AWS Secrets Manager
aws secretsmanager create-secret \
  --name myapp/db-password \
  --secret-string "your-secure-password"

# Retrieve secret
aws secretsmanager get-secret-value --secret-id myapp/db-password
```

### Security Checklist

- [ ] Use AWS Secrets Manager for all credentials
- [ ] Enable VPC Flow Logs
- [ ] Enable CloudTrail
- [ ] Implement WAF rules on ALB
- [ ] Use SSL/TLS certificates (ACM)
- [ ] Regular security audits
- [ ] Implement DDoS protection (AWS Shield)
- [ ] Enable GuardDuty for threat detection

## 💰 Cost Optimization

### Cost-Saving Measures

1. **Right-Sizing**
   - Using t3.micro for development
   - Using t3.small for production
   - Monitor CloudWatch metrics for optimization

2. **Reserved Instances**
   - Purchase RIs for production databases
   - Use Savings Plans for compute

3. **Data Transfer**
   - Use VPC endpoints to avoid NAT gateway charges
   - Optimize CloudWatch log retention

4. **Storage**
   - Use gp3 volumes instead of gp2
   - Implement S3 lifecycle policies

5. **Autoscaling**
   - Scale down during off-peak hours
   - Use On-Demand instances only when needed

### Cost Estimation

```bash
# Use AWS Pricing Calculator
# Estimated monthly cost (dev): ~$50-100
# Estimated monthly cost (prod): ~$200-300

# Monitor actual costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

## 🔄 Backup and Disaster Recovery

### Automated Backups

```bash
# RDS automated backups
- Retention period: 7 days (dev), 30 days (prod)
- Backup window: 03:00-04:00 UTC
- Automatic failover: Multi-AZ enabled

# Manual snapshots
aws rds create-db-snapshot \
  --db-instance-identifier myapp-db-prod \
  --db-snapshot-identifier myapp-db-prod-$(date +%Y%m%d)
```

### Disaster Recovery Plan

1. **Recovery Time Objective (RTO)**: 30 minutes
2. **Recovery Point Objective (RPO)**: 5 minutes

3. **Steps**:
   - Restore from latest snapshot
   - Update DNS to point to new ALB
   - Verify application health
   - Run smoke tests

### Backup Verification

```bash
# Test restore from backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier myapp-db-restore \
  --db-snapshot-identifier myapp-db-prod-20240101

# Verify data
psql -h <restored-rds-endpoint> -U admin -d appdb
```

## 🔧 Troubleshooting

### Common Issues

**Issue: Terraform state lock**
```bash
# Force unlock if stuck
terraform force-unlock <LOCK_ID>
```

**Issue: EC2 instances not starting**
```bash
# Check user data logs
aws ec2 get-console-output --instance-id <instance-id>

# Check Auto Scaling events
aws autoscaling describe-scaling-activities --auto-scaling-group-name myapp-asg-dev
```

**Issue: Database connection failures**
```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids <sg-id>

# Test connectivity from EC2
telnet <rds-endpoint> 5432
```

**Issue: ALB not routing traffic**
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn <tg-arn>

# Check ALB listener rules
aws elbv2 describe-listeners --load-balancer-arn <alb-arn>
```

### Debug Commands

```bash
# SSH into EC2 instance
aws ssm start-session --target <instance-id>

# View logs
tail -f /var/log/cloud-init-output.log

# Check Docker status
docker ps
docker logs <container-id>
```

## 📚 Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Security Best Practices](https://docs.aws.amazon.com/security/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)

## 📝 License

This project is provided as-is for educational purposes.

## ✅ Deployment Checklist

- [ ] AWS credentials configured
- [ ] Terraform initialized and validated
- [ ] Infrastructure deployed
- [ ] Application deployed and healthy
- [ ] Monitoring configured
- [ ] Logging enabled
- [ ] Backups verified
- [ ] CI/CD pipeline tested
- [ ] Security scan passed
- [ ] Documentation reviewed
- [ ] Team trained on procedures

## 🤝 Support

For issues or questions, please refer to the documentation in the `docs/` folder or contact the DevOps team.
