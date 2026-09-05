aws_region               = "ap-south-1"
environment              = "prod"
app_name                 = "myapp"
instance_type            = "t3.small"
db_instance_class        = "db.t4g.micro"
db_allocated_storage     = 50
db_name                  = "appdb"
db_username              = "db_admin"
db_secret_name           = "myapp/db-password"
enable_backup            = true
backup_retention_days    = 0
enable_deletion_protection = true

tags = {
  Project     = "MyProject"
  ManagedBy   = "Terraform"
  Environment = "prod"
  CostCenter  = "Engineering"
}
