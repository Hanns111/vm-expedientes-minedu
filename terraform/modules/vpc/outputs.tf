# ========================================
# VPC Module Outputs
# ========================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

# ==================== SUBNET OUTPUTS ====================

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = aws_subnet.database[*].id
}

output "public_subnet_cidrs" {
  description = "CIDR blocks of the public subnets"
  value       = aws_subnet.public[*].cidr_block
}

output "private_subnet_cidrs" {
  description = "CIDR blocks of the private subnets"
  value       = aws_subnet.private[*].cidr_block
}

output "database_subnet_cidrs" {
  description = "CIDR blocks of the database subnets"
  value       = aws_subnet.database[*].cidr_block
}

# ==================== ROUTE TABLE OUTPUTS ====================

output "public_route_table_id" {
  description = "ID of the public route table"
  value       = aws_route_table.public.id
}

output "private_route_table_ids" {
  description = "IDs of the private route tables"
  value       = aws_route_table.private[*].id
}

output "database_route_table_id" {
  description = "ID of the database route table"
  value       = aws_route_table.database.id
}

# ==================== NAT GATEWAY OUTPUTS ====================

output "nat_gateway_ids" {
  description = "IDs of the NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

output "nat_gateway_public_ips" {
  description = "Public IPs of the NAT Gateways"
  value       = aws_eip.nat[*].public_ip
}

# ==================== DATABASE OUTPUTS ====================

output "database_subnet_group_name" {
  description = "Name of the database subnet group"
  value       = length(aws_db_subnet_group.main) > 0 ? aws_db_subnet_group.main[0].name : null
}

output "database_subnet_group_id" {
  description = "ID of the database subnet group"
  value       = length(aws_db_subnet_group.main) > 0 ? aws_db_subnet_group.main[0].id : null
}

# ==================== VPC ENDPOINT OUTPUTS ====================

output "vpc_endpoint_s3_id" {
  description = "ID of the S3 VPC endpoint"
  value       = length(aws_vpc_endpoint.s3) > 0 ? aws_vpc_endpoint.s3[0].id : null
}

output "vpc_endpoint_ecr_dkr_id" {
  description = "ID of the ECR DKR VPC endpoint"
  value       = length(aws_vpc_endpoint.ecr_dkr) > 0 ? aws_vpc_endpoint.ecr_dkr[0].id : null
}

output "vpc_endpoint_ecr_api_id" {
  description = "ID of the ECR API VPC endpoint"
  value       = length(aws_vpc_endpoint.ecr_api) > 0 ? aws_vpc_endpoint.ecr_api[0].id : null
}

# ==================== AVAILABILITY ZONES ====================

output "availability_zones" {
  description = "List of availability zones used"
  value       = data.aws_availability_zones.available.names
}

# ==================== SECURITY GROUP OUTPUTS ====================

output "vpc_endpoints_security_group_id" {
  description = "ID of the VPC endpoints security group"
  value       = length(aws_security_group.vpc_endpoints) > 0 ? aws_security_group.vpc_endpoints[0].id : null
}

# ==================== FLOW LOGS OUTPUTS ====================

output "flow_logs_log_group_name" {
  description = "Name of the VPC Flow Logs CloudWatch log group"
  value       = length(aws_cloudwatch_log_group.vpc_flow_log) > 0 ? aws_cloudwatch_log_group.vpc_flow_log[0].name : null
}

output "flow_logs_iam_role_arn" {
  description = "ARN of the VPC Flow Logs IAM role"
  value       = length(aws_iam_role.flow_log) > 0 ? aws_iam_role.flow_log[0].arn : null
}

# ==================== METADATA OUTPUTS ====================

output "vpc_info" {
  description = "Complete VPC information"
  value = {
    vpc_id                = aws_vpc.main.id
    vpc_cidr              = aws_vpc.main.cidr_block
    environment           = var.environment
    name_prefix           = var.name_prefix
    public_subnets_count  = length(aws_subnet.public)
    private_subnets_count = length(aws_subnet.private)
    database_subnets_count = length(aws_subnet.database)
    nat_gateways_enabled  = var.enable_nat_gateway
    vpc_endpoints_enabled = var.enable_vpc_endpoints
    flow_logs_enabled     = var.enable_flow_logs
  }
}