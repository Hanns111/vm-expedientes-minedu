# ========================================
# MINEDU RAG Production Infrastructure
# Complete production-ready deployment on AWS
# ========================================

terraform {
  required_version = ">= 1.6"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    bucket         = "minedu-rag-terraform-state-prod"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "minedu-rag-terraform-locks-prod"
  }
}

# ==================== PROVIDERS ====================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project      = "MINEDU-RAG"
      Environment  = "production"
      Owner        = "Infrastructure Team"
      ManagedBy    = "Terraform"
      CostCenter   = "IT-Infrastructure"
      Compliance   = "ISO27001"
      Backup       = "Required"
      CreatedDate  = timestamp()
    }
  }
}

# ==================== DATA SOURCES ====================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ==================== LOCAL VALUES ====================

locals {
  name_prefix = "minedu-rag-prod"
  environment = "production"
  
  # Common tags
  common_tags = {
    Project     = "MINEDU-RAG"
    Environment = local.environment
    Terraform   = "true"
  }

  # Application configuration
  app_config = {
    name         = "minedu-rag"
    version      = var.image_tag
    port         = 8000
    health_path  = "/health"
    cpu          = 1024
    memory       = 2048
    min_capacity = 2
    max_capacity = 10
  }

  # Database configuration
  db_config = {
    instance_class        = "db.r6g.large"
    allocated_storage     = 100
    max_allocated_storage = 1000
    backup_retention      = 30
    multi_az              = true
    deletion_protection   = true
  }
}

# ==================== VPC MODULE ====================

module "vpc" {
  source = "../../modules/vpc"

  name_prefix  = local.name_prefix
  environment  = local.environment
  vpc_cidr     = "10.0.0.0/16"

  public_subnet_cidrs   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnet_cidrs  = ["10.0.10.0/24", "10.0.20.0/24", "10.0.30.0/24"]
  database_subnet_cidrs = ["10.0.40.0/24", "10.0.50.0/24", "10.0.60.0/24"]

  enable_nat_gateway    = true
  enable_vpc_endpoints  = true
  enable_flow_logs      = true
  flow_logs_retention_days = 90

  tags = local.common_tags
}

# ==================== SECURITY GROUPS ====================

# Application Load Balancer Security Group
resource "aws_security_group" "alb" {
  name_prefix = "${local.name_prefix}-alb-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for Application Load Balancer"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-alb-sg"
    Component = "load-balancer"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# ECS Service Security Group
resource "aws_security_group" "ecs_service" {
  name_prefix = "${local.name_prefix}-ecs-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for ECS service"

  ingress {
    from_port       = local.app_config.port
    to_port         = local.app_config.port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "HTTP from ALB"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-ecs-sg"
    Component = "compute"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name_prefix = "${local.name_prefix}-rds-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for RDS PostgreSQL"

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_service.id]
    description     = "PostgreSQL from ECS"
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-rds-sg"
    Component = "database"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Redis Security Group
resource "aws_security_group" "redis" {
  name_prefix = "${local.name_prefix}-redis-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for ElastiCache Redis"

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_service.id]
    description     = "Redis from ECS"
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-redis-sg"
    Component = "cache"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# ==================== APPLICATION LOAD BALANCER ====================

resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnet_ids

  enable_deletion_protection = true
  enable_http2              = true
  idle_timeout              = 60

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "access-logs"
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-alb"
    Component = "load-balancer"
  })
}

# Target Group
resource "aws_lb_target_group" "app" {
  name     = "${local.name_prefix}-app-tg"
  port     = local.app_config.port
  protocol = "HTTP"
  vpc_id   = module.vpc.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
    path                = local.app_config.health_path
    matcher             = "200"
    protocol            = "HTTP"
    port                = "traffic-port"
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-app-tg"
    Component = "load-balancer"
  })
}

# HTTPS Listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate_validation.main.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-https-listener"
    Component = "load-balancer"
  })
}

# HTTP Listener (redirect to HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-http-listener"
    Component = "load-balancer"
  })
}

# ==================== SSL CERTIFICATE ====================

resource "aws_acm_certificate" "main" {
  domain_name               = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-ssl-cert"
    Component = "security"
  })
}

resource "aws_acm_certificate_validation" "main" {
  certificate_arn = aws_acm_certificate.main.arn
  validation_record_fqdns = [
    for record in aws_route53_record.cert_validation : record.fqdn
  ]

  timeouts {
    create = "5m"
  }
}

# ==================== ROUTE 53 ====================

data "aws_route53_zone" "main" {
  name         = var.domain_name
  private_zone = false
}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.main.zone_id
}

resource "aws_route53_record" "main" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# ==================== S3 BUCKETS ====================

# ALB Access Logs Bucket
resource "aws_s3_bucket" "alb_logs" {
  bucket        = "${local.name_prefix}-alb-logs-${random_string.bucket_suffix.result}"
  force_destroy = false

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-alb-logs"
    Component = "logging"
  })
}

resource "aws_s3_bucket_versioning" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  rule {
    id     = "alb_logs_lifecycle"
    status = "Enabled"

    expiration {
      days = 365
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# Application Data Bucket
resource "aws_s3_bucket" "app_data" {
  bucket        = "${local.name_prefix}-app-data-${random_string.bucket_suffix.result}"
  force_destroy = false

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-app-data"
    Component = "storage"
  })
}

resource "aws_s3_bucket_versioning" "app_data" {
  bucket = aws_s3_bucket.app_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "app_data" {
  bucket = aws_s3_bucket.app_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.main.arn
    }
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# ==================== KMS ====================

resource "aws_kms_key" "main" {
  description             = "KMS key for MINEDU RAG encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-kms-key"
    Component = "security"
  })
}

resource "aws_kms_alias" "main" {
  name          = "alias/${local.name_prefix}-key"
  target_key_id = aws_kms_key.main.key_id
}

# ==================== Continue in next part... ====================