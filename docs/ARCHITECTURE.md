# Architecture Documentation

## System Architecture Overview

This document provides a detailed overview of the cloud infrastructure architecture.

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Account                                  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ VPC (10.0.0.0/16)                                           │   │
│  │                                                              │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ Internet Gateway                                    │   │   │
│  │  │ ↓                                                   │   │   │
│  │  │ ┌─────────────┐  ┌──────────────┐                 │   │   │
│  │  │ │Public Subnet│  │Public Subnet2│  (ALB)          │   │   │
│  │  │ │ 10.0.1.0/24 │  │ 10.0.2.0/24  │                 │   │   │
│  │  │ └─────────────┘  └──────────────┘                 │   │   │
│  │  │      ↓                  ↓                           │   │   │
│  │  │   NAT Gateway       NAT Gateway                     │   │   │
│  │  │                                                     │   │   │
│  │  │ ┌─────────────┐  ┌──────────────┐                 │   │   │
│  │  │ │Private Subnet   │Private Subnet2  (EC2/ASG)     │   │   │
│  │  │ │ 10.0.10.0/24│  │ 10.0.11.0/24 │                 │   │   │
│  │  │ └─────────────┘  └──────────────┘                 │   │   │
│  │  │      ↓                  ↓                           │   │   │
│  │  │   ┌─────────────────────────────────────┐         │   │   │
│  │  │   │ RDS PostgreSQL (Multi-AZ)         │         │   │   │
│  │  │   │ - Primary & Standby                │         │   │   │
│  │  │   │ - Automated Backups                │         │   │   │
│  │  │   │ - Encryption at rest               │         │   │   │
│  │  │   └─────────────────────────────────────┘         │   │   │
│  │  │                                                     │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Monitoring & Logging                                        │   │
│  │ ├─ CloudWatch Metrics                                       │   │
│  │ ├─ CloudWatch Logs                                          │   │
│  │ ├─ Prometheus (optional local)                              │   │
│  │ └─ Grafana (optional local)                                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Architecture

### 1. VPC and Networking

#### Design Decisions

- **CIDR Block**: 10.0.0.0/16 (Flexible for future expansion)
- **Subnets**: 4 subnets across 2 Availability Zones
  - 2 Public subnets for ALB and NAT Gateway
  - 2 Private subnets for application and database

#### Rationale

- **High Availability**: Multi-AZ deployment ensures service continuity
- **Fault Isolation**: Separate subnets reduce blast radius
- **Cost Efficiency**: NAT Gateway in public subnet reduces data transfer costs
- **Security**: Private subnets protect application and database from direct internet access

#### Network Flow

```
Internet → IGW → ALB (Public) → Security Group (ALB) 
       → ASG Instances (Private) → Security Group (App) 
       → Database (Private) → Security Group (RDS)
```

### 2. Load Balancing

#### Application Load Balancer (ALB)

```
Frontend Traffic
    ↓
ALB (Layer 7)
- SSL Termination (HTTPS in production)
- Host-based routing
- Path-based routing
    ↓
Target Group
- Health checks every 30s
- Deregistration delay: 30s
    ↓
EC2 Instances (Port 8000)
```

#### Health Check Configuration

- **Protocol**: HTTP
- **Path**: /
- **Port**: 8000
- **Interval**: 30 seconds
- **Timeout**: 5 seconds
- **Healthy Threshold**: 2 checks
- **Unhealthy Threshold**: 2 checks

### 3. Compute (EC2 & Auto Scaling)

#### Auto Scaling Configuration

| Environment | Min | Desired | Max | Scale Up Trigger | Scale Down Trigger |
|-------------|-----|---------|-----|-----------------|--------------------|
| Dev | 1 | 1 | 2 | CPU > 70% | CPU < 30% |
| Prod | 2 | 2 | 6 | CPU > 70% | CPU < 30% |

#### Instance Lifecycle

```
User Terraform Apply
    ↓
Launch Template Created
    ↓
Auto Scaling Group Created
    ↓
EC2 Instances Launched
    ↓
User Data Script Executes
- Install Docker
- Install Docker Compose
- Install CloudWatch Agent
- Install DB Client
    ↓
Instance Passes Health Checks
    ↓
Instance Registered with ALB Target Group
    ↓
Traffic Routed to Instance
```

### 4. Database (RDS PostgreSQL)

#### RDS Configuration

| Aspect | Dev | Prod |
|--------|-----|------|
| Multi-AZ | No | Yes |
| Backup Retention | 7 days | 30 days |
| Storage Type | gp3 | gp3 |
| Allocated Storage | 20 GB | 100 GB |
| Instance Class | db.t3.micro | db.t3.small |
| Encryption | KMS | KMS |
| Enhanced Monitoring | No | Yes |

#### Backup Strategy

```
Daily Automated Backups
    ↓
7-day Retention (Dev) / 30-day Retention (Prod)
    ↓
Manual Snapshots (Before Major Changes)
    ↓
Cross-Region Snapshots (Prod - Monthly)
    ↓
Point-in-Time Recovery Available (Last 7/30 days)
```

#### High Availability (Production)

```
Primary RDS Instance (AZ-1)
    ↓ Synchronous Replication
Standby RDS Instance (AZ-2)
    ↓
Automatic Failover (< 2 minutes)
    ↓
Application Reconnects (via RDS endpoint)
```

### 5. Security Architecture

#### Security Group Rules

**ALB Security Group**
```
Inbound:
- 80/tcp from 0.0.0.0/0 (HTTP)
- 443/tcp from 0.0.0.0/0 (HTTPS)

Outbound:
- All traffic to 0.0.0.0/0
```

**Application Security Group**
```
Inbound:
- 80/tcp from ALB SG
- 443/tcp from ALB SG
- 8000/tcp from ALB SG

Outbound:
- All traffic to 0.0.0.0/0
```

**RDS Security Group**
```
Inbound:
- 5432/tcp from App SG only

Outbound:
- All traffic to 0.0.0.0/0
```

#### Encryption Strategy

1. **Data at Rest**
   - RDS: KMS encryption
   - Snapshots: Encrypted

2. **Data in Transit**
   - Production: TLS 1.2+
   - All API calls: HTTPS

3. **Secrets Management**
   - Database passwords: AWS Secrets Manager
   - Application secrets: Environment variables
   - CI/CD secrets: GitHub Secrets

### 6. Monitoring & Logging Architecture

```
EC2 Instances + RDS
    ↓
CloudWatch Agent (Metrics & Logs)
    ↓
CloudWatch Metrics (10s intervals)
    ↓
┌─────────────────────────────────────┐
│ Dashboards & Alarms                  │
├─────────────────────────────────────┤
│ - Infrastructure Dashboard            │
│ - Application Performance Dashboard   │
│ - Database Dashboard                  │
│ - Custom Business Metrics             │
└─────────────────────────────────────┘
    ↓
Notifications (SNS)
    ↓
Slack / Email / Pagerduty
```

#### Metrics Collection

- **Infrastructure Metrics**
  - CPU Utilization
  - Memory Utilization
  - Disk I/O
  - Network Traffic
  - Connection Count

- **Application Metrics**
  - HTTP Request Rate
  - Error Rate (4xx, 5xx)
  - Response Time (p50, p95, p99)
  - Active Connections
  - Request Size/Response Size

- **Database Metrics**
  - Connections
  - Read Latency
  - Write Latency
  - Disk Usage
  - Query Performance

### 7. CI/CD Pipeline Architecture

```
┌──────────────────────────────────────────────────────┐
│ GitHub Repository                                     │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ Git Events (Push, PR)                                │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ GitHub Actions CI/CD Pipeline                        │
├──────────────────────────────────────────────────────┤
│ 1. Test Stage                                         │
│    - Run unit tests                                  │
│    - Code coverage                                   │
│    - Lint checks                                     │
│                                                      │
│ 2. Security Scan Stage                              │
│    - Trivy container scanning                       │
│    - Dependency vulnerabilities                     │
│    - SAST analysis                                  │
│                                                      │
│ 3. Build Stage (main/develop)                       │
│    - Build Docker image                             │
│    - Push to ECR                                    │
│    - Scan image                                     │
│                                                      │
│ 4. Deploy Staging (develop branch)                  │
│    - Update ECS tasks                               │
│    - Run smoke tests                                │
│                                                      │
│ 5. Deploy Production (main branch)                  │
│    - Manual approval required                       │
│    - Blue-green deployment                          │
│    - Health checks                                  │
│    - Smoke tests                                    │
└──────────────────────────────────────────────────────┘
```

## Data Flow

### Application Request Flow

```
1. User Request
   ↓
2. DNS Resolution (Route 53)
   ↓
3. ALB receives request (Port 80/443)
   ↓
4. ALB Routes to Target Group
   ↓
5. EC2 Instance receives request (Port 8000)
   ↓
6. Flask Application processes request
   ↓
7. Query to PostgreSQL database
   ↓
8. Database processes and returns data
   ↓
9. Application formats response
   ↓
10. Response sent through ALB
   ↓
11. User receives response
```

### Monitoring Data Flow

```
Application/Infrastructure
    ↓
CloudWatch Metrics
    ↓
Metrics Stream
    ↓
┌────────────┐  ┌─────────────┐  ┌──────────┐
│ Dashboards │  │  Alarms     │  │   Logs   │
└────────────┘  └─────────────┘  └──────────┘
                      ↓
              Alarm Actions Triggered
                      ↓
              SNS Topics
                      ↓
         ┌─────────┬────────┬─────────┐
         ↓         ↓        ↓         ↓
       Email    Slack  PagerDuty   Lambda
```

## Scalability Considerations

### Horizontal Scaling

- **Auto Scaling Groups**: Automatic instance scaling based on metrics
- **Load Balancer**: Distributes traffic across instances
- **Multi-AZ**: Instances spread across availability zones

### Vertical Scaling

- **Database**: Scale RDS instance class
- **Compute**: Modify instance type

### Database Scaling

- Read Replicas for read-heavy workloads
- Connection pooling
- Query optimization

## Disaster Recovery Architecture

```
Primary Infrastructure (Active)
    ↓
Continuous Backup Process
    ↓
┌─────────────────────────────────────┐
│ Backup Storage                       │
├─────────────────────────────────────┤
│ - Daily snapshots                   │
│ - Point-in-time recovery            │
│ - Cross-region replication          │
│ - Data retention policy             │
└─────────────────────────────────────┘
    ↓
Recovery Procedures
    ↓
RTO: 30 minutes
RPO: 5 minutes
```

## Cost Optimization Architecture

### Cost Centers

1. **Compute**: EC2 instances, Auto Scaling
2. **Database**: RDS instance + backup storage
3. **Networking**: NAT Gateway, ALB, data transfer
4. **Storage**: EBS volumes, snapshots
5. **Monitoring**: CloudWatch

### Optimization Strategies

- Right-sizing instances based on metrics
- Using Reserved Instances for predictable workloads
- Scheduled scaling for known patterns
- Efficient log retention policies
- VPC endpoints to reduce NAT costs

## Conclusion

This architecture provides a robust, scalable, and secure foundation for modern cloud applications. It balances high availability, security, and cost-efficiency while following AWS best practices.
