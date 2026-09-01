# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-db-subnet-group-${var.environment}"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "${var.app_name}-db-subnet-group-${var.environment}"
  }
}

# RDS Instances
resource "aws_db_instance" "main" {
  identifier            = "${var.app_name}-db-${var.environment}"
  engine                = "postgres"
  engine_version        = "15.3"
  instance_class        = var.db_instance_class
  allocated_storage     = var.db_allocated_storage
  db_name               = var.db_name
  username              = var.db_username
  password              = var.db_password
  db_subnet_group_name  = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  # Backup and maintenance
  backup_retention_period = var.backup_retention_days
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"
  
  # High availability
  multi_az = var.environment == "prod" ? true : false
  
  # Deletion protection
  deletion_protection = var.enable_deletion_protection
  
  # Storage encryption
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn
  
  # Performance insights
  performance_insights_enabled = var.environment == "prod" ? true : false
  
  # Logging
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  skip_final_snapshot       = var.environment == "dev" ? true : false
  final_snapshot_identifier = var.environment == "dev" ? null : "${var.app_name}-db-final-snapshot-${var.environment}-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  tags = {
    Name = "${var.app_name}-db-${var.environment}"
  }

  depends_on = [aws_security_group.rds]
}

# KMS Key for RDS Encryption
resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name = "${var.app_name}-kms-rds-${var.environment}"
  }
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${var.app_name}-rds-${var.environment}"
  target_key_id = aws_kms_key.rds.key_id
}
