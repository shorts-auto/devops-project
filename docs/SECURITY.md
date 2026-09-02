# Security Documentation

## Security Overview

This document outlines the security measures implemented in the infrastructure and best practices for maintaining security.

## Security Layers

```
┌─────────────────────────────────────────────────────┐
│ 1. Identity & Access Management (IAM)              │
├─────────────────────────────────────────────────────┤
│ 2. Network Security (VPC, Security Groups)         │
├─────────────────────────────────────────────────────┤
│ 3. Data Encryption (TLS, KMS)                      │
├─────────────────────────────────────────────────────┤
│ 4. Application Security (Scanning, Testing)        │
├─────────────────────────────────────────────────────┤
│ 5. Monitoring & Threat Detection                   │
├─────────────────────────────────────────────────────┤
│ 6. Compliance & Audit Logging                      │
└─────────────────────────────────────────────────────┘
```

## 1. Identity & Access Management

### IAM Principles

- **Least Privilege**: Grant minimum necessary permissions
- **Separation of Concerns**: Different roles for different functions
- **Regular Audits**: Review permissions quarterly

### IAM Roles for EC2

```hcl
# Application Role
resource "aws_iam_role" "ec2_role" {
  # Permissions:
  # - CloudWatch Metrics Publishing
  # - CloudWatch Logs Management
  # - Secrets Manager Access
  # - Parameter Store Access
  # - EC2 Describe Operations
}
```

### Permission Scope

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:myapp-*"
    }
  ]
}
```

## 2. Network Security

### Security Group Strategy

#### ALB Security Group
```
INBOUND:
- Port 80 (HTTP) from 0.0.0.0/0
- Port 443 (HTTPS) from 0.0.0.0/0
- Port 8000 from 0.0.0.0/0 (for testing)

OUTBOUND:
- All traffic allowed
```

#### Application Security Group
```
INBOUND:
- Port 80 from ALB SG only
- Port 443 from ALB SG only
- Port 8000 from ALB SG only

OUTBOUND:
- All traffic (for system updates, external APIs)
```

#### RDS Security Group
```
INBOUND:
- Port 5432 from Application SG only
- NO public access

OUTBOUND:
- All traffic allowed
```

### Network Access Pattern

```
Public Internet
    ↓
[ALLOWED] → ALB (Security Group: 80, 443)
    ↓ [Restricted to ALB SG]
Application (Security Group: 8000 from ALB only)
    ↓ [Restricted to App SG]
Database (Security Group: 5432 from App only)
    ↗
NO direct internet access
```

### VPC Flow Logs

Enable VPC Flow Logs for traffic analysis:

```bash
# Enable VPC Flow Logs
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-xxxxx \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flowlogs/myapp
```

## 3. Data Encryption

### Encryption at Rest

#### RDS Database
- **Method**: AWS KMS (Key Management Service)
- **Key Rotation**: Enabled (automatic annual rotation)
- **Coverage**: Database files, snapshots, backups

```hcl
resource "aws_db_instance" "main" {
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn
}
```

#### EBS Volumes
- **Method**: KMS encryption
- **Default**: Enabled in default encryption settings

### Encryption in Transit

#### Database Connections
- **Protocol**: PostgreSQL SSL connections
- **Configuration**: Require SSL for connections

#### Application Traffic
- **HTTP**: Upgrade to HTTPS in production
- **TLS Version**: TLS 1.2 minimum

#### AWS API Calls
- **Protocol**: HTTPS/TLS 1.2+
- **Automatic**: All AWS API calls encrypted

### Certificate Management

```bash
# Use AWS Certificate Manager (ACM) for SSL certificates
aws acm request-certificate \
  --domain-name myapp.example.com \
  --validation-method DNS

# Attach to ALB listener
aws elbv2 modify-listener \
  --listener-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --certificates CertificateArn=arn:aws:acm:...
```

## 4. Secrets Management

### Storing Secrets

#### AWS Secrets Manager

```bash
# Create database password secret
aws secretsmanager create-secret \
  --name myapp/db-password \
  --secret-string "your-secure-password-here" \
  --tags Key=Environment,Value=prod Key=Application,Value=myapp

# Create API key secret
aws secretsmanager create-secret \
  --name myapp/api-keys \
  --secret-string '{
    "telegram_bot_token": "your-telegram-bot-token",
    "telegram_chat_id": "your-telegram-chat-id",
    "docker_registry_token": "..."
  }'
```

#### Environment Variables (EC2)

```bash
# In user data script
aws secretsmanager get-secret-value \
  --secret-id myapp/db-password \
  --query SecretString \
  --output text > /opt/app/.db_password

# Set permissions
chmod 600 /opt/app/.db_password
chown appuser:appuser /opt/app/.db_password

# Source in application
export DB_PASSWORD=$(cat /opt/app/.db_password)
```

#### GitHub Secrets

```yaml
# .github/workflows/ci-cd.yml
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
```

### Secret Rotation

```bash
# Manual rotation
aws secretsmanager update-secret \
  --secret-id myapp/db-password \
  --secret-string "new-password-here"

# Update RDS password
aws rds modify-db-instance \
  --db-instance-identifier myapp-db \
  --master-user-password "new-password-here" \
  --apply-immediately
```

## 5. Application Security

### Container Security

#### Dockerfile Best Practices

```dockerfile
# Use specific version tags
FROM python:3.11-slim

# Run as non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Minimize layers
RUN apt-get update && \
    apt-get install -y required-packages && \
    rm -rf /var/lib/apt/lists/*

# Use read-only file systems where possible
USER appuser:appuser
```

### Image Scanning

#### Trivy Scanning

```bash
# Scan local image
trivy image myregistry/myapp:latest

# Generate SARIF report
trivy image --format sarif --output report.sarif myregistry/myapp:latest

# In CI/CD pipeline (GitHub Actions)
- name: Scan Docker image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ steps.build.outputs.image }}
    format: 'sarif'
    output: 'trivy-results.sarif'
```

### Dependency Scanning

#### Safety (Python)

```bash
# Check for vulnerable dependencies
safety check --json

# In CI/CD
- name: Check dependencies
  run: |
    pip install safety
    safety check --json || true
```

#### Snyk

```bash
# Scan project
snyk test

# Monitor for vulnerabilities
snyk monitor
```

## 6. Application Code Security

### SAST (Static Application Security Testing)

#### Bandit (Python)

```bash
# Run security checks
bandit -r app/ -f json -o bandit-report.json

# In CI/CD
- name: Run Bandit
  run: |
    pip install bandit
    bandit -r app/ -f json
```

### Code Quality

#### SonarQube Integration

```yaml
# .github/workflows/sonarqube.yml
- name: SonarQube Scan
  uses: SonarSource/sonarcloud-github-action@master
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

## 7. Monitoring & Logging

### CloudWatch Alarms

```hcl
# Alarm for unauthorized API calls
resource "aws_cloudwatch_metric_alarm" "unauthorized_calls" {
  alarm_name = "unauthorized-api-calls"
  # Alert on multiple failed login attempts
}

# Alarm for security group changes
resource "aws_cloudwatch_metric_alarm" "sg_changes" {
  alarm_name = "security-group-modified"
  # Alert on changes to security groups
}
```

### Log Aggregation

```bash
# CloudWatch Logs Groups
/aws/rds/instance/myapp/postgresql      # Database logs
/aws/ec2/myapp                          # Application logs
/aws/alb/myapp                          # Load balancer logs
/aws/lambda/myapp                       # Lambda logs

# Set retention policies
aws logs put-retention-policy \
  --log-group-name /aws/rds/instance/myapp/postgresql \
  --retention-in-days 30
```

### AWS CloudTrail

```bash
# Enable CloudTrail for auditing
aws cloudtrail create-trail \
  --name myapp-trail \
  --s3-bucket-name myapp-cloudtrail-logs

# Start logging
aws cloudtrail start-logging --trail-name myapp-trail
```

## 8. Incident Response

### Incident Response Plan

1. **Detection**: CloudWatch Alarms, GuardDuty alerts
2. **Response**: Automated (kill compromised instances) or Manual
3. **Recovery**: Restore from backups
4. **Post-Incident**: Review and improve

### Automated Response Examples

```hcl
# Auto-terminate compromised instances
resource "aws_autoscaling_notification" "security_alert" {
  group_names = [aws_autoscaling_group.app.name]
  notifications = [
    "autoscaling:EC2_INSTANCE_LAUNCH_ERROR",
    "autoscaling:EC2_INSTANCE_TERMINATE_ERROR"
  ]
  topic_arn = aws_sns_topic.security_alerts.arn
}
```

## 9. Compliance & Audit

### AWS Config

Enable AWS Config to track configuration changes:

```bash
aws configservice put-config-recorder \
  --config-recorder name=default,roleARN=arn:aws:iam::...
```

### Audit Logging

- **CloudTrail**: API-level audit logs
- **VPC Flow Logs**: Network-level audit logs
- **Application Logs**: Application-level audit logs

### Compliance Checklist

- [ ] Encryption enabled for all data at rest
- [ ] TLS 1.2+ for all data in transit
- [ ] Secrets stored in Secrets Manager
- [ ] IAM policies follow least privilege
- [ ] VPC Flow Logs enabled
- [ ] CloudTrail enabled
- [ ] CloudWatch Logs with retention policies
- [ ] Regular security assessments
- [ ] Incident response plan documented
- [ ] Backup and disaster recovery tested

## 10. Security Best Practices Summary

### General Practices

1. **Keep Systems Updated**
   - Regular OS and library updates
   - Security patches immediately
   - Container base images updated

2. **Monitor and Alert**
   - Real-time security monitoring
   - Alert on suspicious activities
   - Regular log review

3. **Limit Exposure**
   - Minimal public access
   - Private databases
   - Security groups with least privilege

4. **Secure Secrets**
   - Never commit secrets to git
   - Use Secrets Manager/Parameter Store
   - Rotate regularly

5. **Defense in Depth**
   - Multiple security layers
   - Network segmentation
   - Application-level security

6. **Regular Testing**
   - Penetration testing (quarterly)
   - Vulnerability scanning (continuous)
   - Security audits (bi-annual)

## Security References

- [AWS Security Best Practices](https://docs.aws.amazon.com/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)

## Security Contact

For security issues, please report them to the security team.
