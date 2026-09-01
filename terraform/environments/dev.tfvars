aws_region               = "ap-south-1"
environment              = "dev"
app_name                 = "myapp"
instance_type            = "t3.micro"
db_instance_class        = "db.t3.micro"
db_allocated_storage     = 20
db_name                  = "appdb"
db_username              = "db_admin"
db_password              = "DevPassword123!"  # Change this in production
enable_backup            = true
backup_retention_days    = 0
enable_deletion_protection = false

tags = {
  Project     = "MyProject"
  ManagedBy   = "Terraform"
  Environment = "dev"
  CostCenter  = "Engineering"
}
