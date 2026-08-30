output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_1_id" {
  description = "Public Subnet 1 ID"
  value       = aws_subnet.public_1.id
}

output "public_subnet_2_id" {
  description = "Public Subnet 2 ID"
  value       = aws_subnet.public_2.id
}

output "private_subnet_1_id" {
  description = "Private Subnet 1 ID"
  value       = aws_subnet.private_1.id
}

output "private_subnet_2_id" {
  description = "Private Subnet 2 ID"
  value       = aws_subnet.private_2.id
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.app.dns_name
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.app.arn
}

output "rds_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_address" {
  description = "RDS database address"
  value       = aws_db_instance.main.address
  sensitive   = true
}

output "rds_port" {
  description = "RDS database port"
  value       = aws_db_instance.main.port
}

output "rds_identifier" {
  description = "RDS database identifier"
  value       = aws_db_instance.main.identifier
}

output "autoscaling_group_name" {
  description = "Auto Scaling Group name"
  value       = aws_autoscaling_group.app.name
}

output "autoscaling_group_arn" {
  description = "Auto Scaling Group ARN"
  value       = aws_autoscaling_group.app.arn
}

output "target_group_arn" {
  description = "Target Group ARN"
  value       = aws_lb_target_group.app.arn
}

output "security_group_alb_id" {
  description = "Security Group ID for ALB"
  value       = aws_security_group.alb.id
}

output "security_group_app_id" {
  description = "Security Group ID for Application"
  value       = aws_security_group.app.id
}

output "security_group_rds_id" {
  description = "Security Group ID for RDS"
  value       = aws_security_group.rds.id
}

output "nat_gateway_ip" {
  description = "NAT Gateway Elastic IP"
  value       = aws_eip.nat.public_ip
}

output "deployment_command" {
  description = "Command to deploy infrastructure"
  value       = "terraform apply -var-file=environments/${var.environment}.tfvars"
}
