# ========================================
# Production Environment Variables
# ========================================

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
  validation {
    condition = contains([
      "us-east-1", "us-east-2", "us-west-1", "us-west-2",
      "eu-west-1", "eu-west-2", "eu-central-1",
      "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
    ], var.aws_region)
    error_message = "AWS region must be a valid region."
  }
}

variable "domain_name" {
  description = "Primary domain name for the application"
  type        = string
  default     = "minedu-rag.com"
  validation {
    condition     = can(regex("^[a-z0-9.-]+\\.[a-z]{2,}$", var.domain_name))
    error_message = "Domain name must be a valid domain format."
  }
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
  validation {
    condition     = length(var.image_tag) > 0
    error_message = "Image tag cannot be empty."
  }
}

variable "enable_read_replica" {
  description = "Enable RDS read replica for better performance"
  type        = bool
  default     = true
}

variable "alert_email_addresses" {
  description = "List of email addresses for alerts"
  type        = list(string)
  default     = []
  validation {
    condition = alltrue([
      for email in var.alert_email_addresses : can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", email))
    ])
    error_message = "All email addresses must be valid."
  }
}

variable "enable_waf" {
  description = "Enable AWS WAF for additional security"
  type        = bool
  default     = true
}

variable "enable_cloudfront" {
  description = "Enable CloudFront CDN"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
  validation {
    condition     = var.backup_retention_days >= 7 && var.backup_retention_days <= 35
    error_message = "Backup retention days must be between 7 and 35."
  }
}

# ==================== OAUTH2 CONFIGURATION ====================

variable "google_oauth_client_id" {
  description = "Google OAuth2 client ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "google_oauth_client_secret" {
  description = "Google OAuth2 client secret"
  type        = string
  default     = ""
  sensitive   = true
}

variable "microsoft_oauth_client_id" {
  description = "Microsoft OAuth2 client ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "microsoft_oauth_client_secret" {
  description = "Microsoft OAuth2 client secret"
  type        = string
  default     = ""
  sensitive   = true
}

variable "microsoft_tenant_id" {
  description = "Microsoft Azure tenant ID"
  type        = string
  default     = "common"
}

# ==================== APPLICATION CONFIGURATION ====================

variable "jwt_secret_key" {
  description = "JWT secret key for token signing"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.jwt_secret_key) >= 32
    error_message = "JWT secret key must be at least 32 characters long."
  }
}

variable "openai_api_key" {
  description = "OpenAI API key for LLM integration"
  type        = string
  default     = ""
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API key for Claude integration"
  type        = string
  default     = ""
  sensitive   = true
}

# ==================== SCALING CONFIGURATION ====================

variable "min_capacity" {
  description = "Minimum number of ECS tasks"
  type        = number
  default     = 2
  validation {
    condition     = var.min_capacity >= 1
    error_message = "Minimum capacity must be at least 1."
  }
}

variable "max_capacity" {
  description = "Maximum number of ECS tasks"
  type        = number
  default     = 10
  validation {
    condition     = var.max_capacity >= var.min_capacity
    error_message = "Maximum capacity must be greater than or equal to minimum capacity."
  }
}

variable "target_cpu_utilization" {
  description = "Target CPU utilization percentage for auto scaling"
  type        = number
  default     = 70
  validation {
    condition     = var.target_cpu_utilization >= 20 && var.target_cpu_utilization <= 90
    error_message = "Target CPU utilization must be between 20 and 90 percent."
  }
}

variable "target_memory_utilization" {
  description = "Target memory utilization percentage for auto scaling"
  type        = number
  default     = 80
  validation {
    condition     = var.target_memory_utilization >= 20 && var.target_memory_utilization <= 90
    error_message = "Target memory utilization must be between 20 and 90 percent."
  }
}

# ==================== DATABASE CONFIGURATION ====================

variable "database_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
  validation {
    condition = contains([
      "db.r6g.large", "db.r6g.xlarge", "db.r6g.2xlarge", "db.r6g.4xlarge",
      "db.r5.large", "db.r5.xlarge", "db.r5.2xlarge", "db.r5.4xlarge"
    ], var.database_instance_class)
    error_message = "Database instance class must be a valid RDS instance type."
  }
}

variable "database_allocated_storage" {
  description = "Initial allocated storage for RDS in GB"
  type        = number
  default     = 100
  validation {
    condition     = var.database_allocated_storage >= 20
    error_message = "Database allocated storage must be at least 20 GB."
  }
}

variable "database_max_allocated_storage" {
  description = "Maximum allocated storage for RDS auto scaling in GB"
  type        = number
  default     = 1000
  validation {
    condition     = var.database_max_allocated_storage >= var.database_allocated_storage
    error_message = "Maximum allocated storage must be greater than or equal to allocated storage."
  }
}

# ==================== REDIS CONFIGURATION ====================

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.r7g.large"
  validation {
    condition = contains([
      "cache.r7g.large", "cache.r7g.xlarge", "cache.r7g.2xlarge",
      "cache.r6g.large", "cache.r6g.xlarge", "cache.r6g.2xlarge"
    ], var.redis_node_type)
    error_message = "Redis node type must be a valid ElastiCache instance type."
  }
}

variable "redis_num_cache_clusters" {
  description = "Number of cache clusters in the replication group"
  type        = number
  default     = 2
  validation {
    condition     = var.redis_num_cache_clusters >= 2 && var.redis_num_cache_clusters <= 6
    error_message = "Number of cache clusters must be between 2 and 6."
  }
}

# ==================== MONITORING CONFIGURATION ====================

variable "enable_detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch logs retention period in days"
  type        = number
  default     = 30
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch Logs retention period."
  }
}

variable "enable_xray_tracing" {
  description = "Enable AWS X-Ray tracing"
  type        = bool
  default     = true
}

# ==================== SECURITY CONFIGURATION ====================

variable "enable_deletion_protection" {
  description = "Enable deletion protection for critical resources"
  type        = bool
  default     = true
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # In production, restrict this
  validation {
    condition = alltrue([
      for cidr in var.allowed_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "All CIDR blocks must be valid IPv4 CIDR notation."
  }
}

variable "ssl_policy" {
  description = "SSL policy for load balancer"
  type        = string
  default     = "ELBSecurityPolicy-TLS-1-2-2017-01"
  validation {
    condition = contains([
      "ELBSecurityPolicy-TLS-1-2-2017-01",
      "ELBSecurityPolicy-TLS-1-2-Ext-2018-06",
      "ELBSecurityPolicy-FS-1-2-2019-08",
      "ELBSecurityPolicy-FS-1-2-Res-2020-10"
    ], var.ssl_policy)
    error_message = "SSL policy must be a valid ELB security policy."
  }
}

# ==================== COST OPTIMIZATION ====================

variable "environment_tier" {
  description = "Environment tier for cost optimization"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment_tier)
    error_message = "Environment tier must be development, staging, or production."
  }
}

variable "enable_cost_optimization" {
  description = "Enable cost optimization features"
  type        = bool
  default     = false
}

variable "schedule_downtime" {
  description = "Schedule for automatic downtime (development/staging only)"
  type = object({
    enabled    = bool
    start_time = string  # HH:MM format
    end_time   = string  # HH:MM format
    timezone   = string  # e.g., "America/New_York"
    days       = list(string)  # e.g., ["Saturday", "Sunday"]
  })
  default = {
    enabled    = false
    start_time = "22:00"
    end_time   = "06:00"
    timezone   = "UTC"
    days       = ["Saturday", "Sunday"]
  }
}

# ==================== DISASTER RECOVERY ====================

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup for disaster recovery"
  type        = bool
  default     = true
}

variable "backup_region" {
  description = "AWS region for cross-region backups"
  type        = string
  default     = "us-west-2"
  validation {
    condition = contains([
      "us-east-1", "us-east-2", "us-west-1", "us-west-2",
      "eu-west-1", "eu-west-2", "eu-central-1"
    ], var.backup_region)
    error_message = "Backup region must be a valid AWS region."
  }
}

variable "rpo_hours" {
  description = "Recovery Point Objective in hours"
  type        = number
  default     = 4
  validation {
    condition     = var.rpo_hours >= 1 && var.rpo_hours <= 24
    error_message = "RPO must be between 1 and 24 hours."
  }
}

variable "rto_hours" {
  description = "Recovery Time Objective in hours"
  type        = number
  default     = 2
  validation {
    condition     = var.rto_hours >= 1 && var.rto_hours <= 8
    error_message = "RTO must be between 1 and 8 hours."
  }
}

# ==================== COMPLIANCE ====================

variable "compliance_framework" {
  description = "Compliance framework to adhere to"
  type        = string
  default     = "ISO27001"
  validation {
    condition     = contains(["ISO27001", "SOC2", "GDPR", "HIPAA", "PCI-DSS"], var.compliance_framework)
    error_message = "Compliance framework must be one of the supported standards."
  }
}

variable "enable_audit_logging" {
  description = "Enable comprehensive audit logging"
  type        = bool
  default     = true
}

variable "data_residency_region" {
  description = "Region where data must reside for compliance"
  type        = string
  default     = "us-east-1"
}

# ==================== ADDITIONAL TAGS ====================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "cost_center" {
  description = "Cost center for billing allocation"
  type        = string
  default     = "IT-Infrastructure"
}

variable "project_code" {
  description = "Project code for resource organization"
  type        = string
  default     = "MINEDU-RAG-001"
}