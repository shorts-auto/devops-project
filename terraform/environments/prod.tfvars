aws_region               = "ap-south-1"
environment              = "prod"
app_name                 = "myapp"
instance_type            = "t3.small"
db_instance_class        = "db.t3.small"
db_allocated_storage     = 50
db_name                  = "appdb"
db_username              = "admin"
db_password              = "CHANGE_ME_IN_AWS_SECRETS_MANAGER"  # Use AWS Secrets Manager in production
enable_backup            = true
backup_retention_days    = 0
enable_deletion_protection = true

tags = {
  Project     = "MyProject"
  ManagedBy   = "Terraform"
  Environment = "prod"
  CostCenter  = "Engineering"
}
