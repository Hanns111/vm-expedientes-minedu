# ========================================
# VPC Module for MINEDU RAG Infrastructure
# Creates secure, multi-AZ VPC with public/private subnets
# ========================================

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ==================== DATA SOURCES ====================

data "aws_availability_zones" "available" {
  state = "available"
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ==================== VPC ====================

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-vpc"
    Environment = var.environment
    Component   = "networking"
  })
}

# ==================== INTERNET GATEWAY ====================

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-igw"
    Environment = var.environment
    Component   = "networking"
  })
}

# ==================== PUBLIC SUBNETS ====================

resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-public-subnet-${count.index + 1}"
    Environment = var.environment
    Type        = "public"
    Component   = "networking"
    AZ          = data.aws_availability_zones.available.names[count.index]
  })
}

# ==================== PRIVATE SUBNETS ====================

resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidrs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-private-subnet-${count.index + 1}"
    Environment = var.environment
    Type        = "private"
    Component   = "networking"
    AZ          = data.aws_availability_zones.available.names[count.index]
  })
}

# ==================== DATABASE SUBNETS ====================

resource "aws_subnet" "database" {
  count = length(var.database_subnet_cidrs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.database_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-database-subnet-${count.index + 1}"
    Environment = var.environment
    Type        = "database"
    Component   = "networking"
    AZ          = data.aws_availability_zones.available.names[count.index]
  })
}

# ==================== NAT GATEWAYS ====================

resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? length(var.public_subnet_cidrs) : 0

  domain = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-nat-eip-${count.index + 1}"
    Environment = var.environment
    Component   = "networking"
  })
}

resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? length(var.public_subnet_cidrs) : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  depends_on    = [aws_internet_gateway.main]

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-nat-gateway-${count.index + 1}"
    Environment = var.environment
    Component   = "networking"
  })
}

# ==================== ROUTE TABLES ====================

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-public-rt"
    Environment = var.environment
    Type        = "public"
    Component   = "networking"
  })
}

# Private Route Tables
resource "aws_route_table" "private" {
  count = var.enable_nat_gateway ? length(var.private_subnet_cidrs) : 1

  vpc_id = aws_vpc.main.id

  dynamic "route" {
    for_each = var.enable_nat_gateway ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.main[count.index].id
    }
  }

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-private-rt-${count.index + 1}"
    Environment = var.environment
    Type        = "private"
    Component   = "networking"
  })
}

# Database Route Table
resource "aws_route_table" "database" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-database-rt"
    Environment = var.environment
    Type        = "database"
    Component   = "networking"
  })
}

# ==================== ROUTE TABLE ASSOCIATIONS ====================

resource "aws_route_table_association" "public" {
  count = length(var.public_subnet_cidrs)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = length(var.private_subnet_cidrs)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = var.enable_nat_gateway ? aws_route_table.private[count.index].id : aws_route_table.private[0].id
}

resource "aws_route_table_association" "database" {
  count = length(var.database_subnet_cidrs)

  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database.id
}

# ==================== DATABASE SUBNET GROUP ====================

resource "aws_db_subnet_group" "main" {
  count = length(var.database_subnet_cidrs) > 0 ? 1 : 0

  name       = "${var.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.database[*].id

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-db-subnet-group"
    Environment = var.environment
    Component   = "database"
  })
}

# ==================== VPC ENDPOINTS ====================

# S3 VPC Endpoint
resource "aws_vpc_endpoint" "s3" {
  count = var.enable_vpc_endpoints ? 1 : 0

  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = concat([aws_route_table.public.id], aws_route_table.private[*].id)

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-s3-endpoint"
    Environment = var.environment
    Component   = "networking"
  })
}

# ECR VPC Endpoints
resource "aws_vpc_endpoint" "ecr_dkr" {
  count = var.enable_vpc_endpoints ? 1 : 0

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-ecr-dkr-endpoint"
    Environment = var.environment
    Component   = "networking"
  })
}

resource "aws_vpc_endpoint" "ecr_api" {
  count = var.enable_vpc_endpoints ? 1 : 0

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-ecr-api-endpoint"
    Environment = var.environment
    Component   = "networking"
  })
}

# ==================== SECURITY GROUPS ====================

resource "aws_security_group" "vpc_endpoints" {
  count = var.enable_vpc_endpoints ? 1 : 0

  name_prefix = "${var.name_prefix}-vpc-endpoints-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for VPC endpoints"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "HTTPS from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-vpc-endpoints-sg"
    Environment = var.environment
    Component   = "networking"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# ==================== VPC FLOW LOGS ====================

resource "aws_flow_log" "vpc_flow_log" {
  count = var.enable_flow_logs ? 1 : 0

  iam_role_arn    = aws_iam_role.flow_log[0].arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_log[0].arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id
}

resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  count = var.enable_flow_logs ? 1 : 0

  name              = "/aws/vpc/flowlogs/${var.name_prefix}"
  retention_in_days = var.flow_logs_retention_days

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-vpc-flow-logs"
    Environment = var.environment
    Component   = "logging"
  })
}

resource "aws_iam_role" "flow_log" {
  count = var.enable_flow_logs ? 1 : 0

  name_prefix = "${var.name_prefix}-flow-log-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-flow-log-role"
    Environment = var.environment
    Component   = "iam"
  })
}

resource "aws_iam_role_policy" "flow_log" {
  count = var.enable_flow_logs ? 1 : 0

  name_prefix = "${var.name_prefix}-flow-log-"
  role        = aws_iam_role.flow_log[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}