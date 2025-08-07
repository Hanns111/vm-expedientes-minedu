# ========================================
# RDS PostgreSQL Database Configuration
# Production-ready with Multi-AZ, encryption, backups
# ========================================

# ==================== RDS SUBNET GROUP ====================
# Note: This is already created in the VPC module, but we reference it here

# ==================== RDS PARAMETER GROUP ====================

resource "aws_db_parameter_group" "main" {
  family = "postgres15"
  name   = "${local.name_prefix}-postgres-params"

  # Performance and security optimizations
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "log_statement"
    value = "mod"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log queries taking more than 1 second
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_lock_waits"
    value = "1"
  }

  parameter {
    name  = "log_temp_files"
    value = "0"
  }

  parameter {
    name  = "checkpoint_completion_target"
    value = "0.9"
  }

  parameter {
    name  = "wal_buffers"
    value = "16MB"
  }

  parameter {
    name  = "default_statistics_target"
    value = "100"
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-postgres-params"
    Component = "database"
  })
}

# ==================== RDS OPTION GROUP ====================

resource "aws_db_option_group" "main" {
  name                     = "${local.name_prefix}-postgres-options"
  option_group_description = "Option group for PostgreSQL"
  engine_name              = "postgres"
  major_engine_version     = "15"

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-postgres-options"
    Component = "database"
  })
}

# ==================== RANDOM PASSWORD ====================

resource "random_password" "db_password" {
  length  = 32
  special = true
}

# ==================== SECRETS MANAGER ====================

resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "${local.name_prefix}-db-credentials"
  description             = "Database credentials for MINEDU RAG"
  recovery_window_in_days = 7
  kms_key_id             = aws_kms_key.main.arn

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-db-credentials"
    Component = "database"
  })
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = "minedu_admin"
    password = random_password.db_password.result
    engine   = "postgres"
    host     = aws_db_instance.main.endpoint
    port     = aws_db_instance.main.port
    dbname   = aws_db_instance.main.db_name
  })
}

# ==================== RDS INSTANCE ====================

resource "aws_db_instance" "main" {
  # Basic configuration
  identifier     = "${local.name_prefix}-postgres"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = local.db_config.instance_class

  # Database configuration
  db_name  = "minedu_rag"
  username = "minedu_admin"
  password = random_password.db_password.result
  port     = 5432

  # Storage configuration
  allocated_storage     = local.db_config.allocated_storage
  max_allocated_storage = local.db_config.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.main.arn

  # High availability and backup
  multi_az               = local.db_config.multi_az
  backup_retention_period = local.db_config.backup_retention
  backup_window          = "03:00-04:00"  # UTC
  maintenance_window     = "Sun:04:00-Sun:05:00"  # UTC
  auto_minor_version_upgrade = false
  deletion_protection    = local.db_config.deletion_protection

  # Network and security
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Parameter and option groups
  parameter_group_name = aws_db_parameter_group.main.name
  option_group_name    = aws_db_option_group.main.name

  # Performance Insights
  performance_insights_enabled = true
  performance_insights_kms_key_id = aws_kms_key.main.arn
  performance_insights_retention_period = 7

  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  # Logs
  enabled_cloudwatch_logs_exports = ["postgresql"]

  # Snapshot configuration
  final_snapshot_identifier = "${local.name_prefix}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  skip_final_snapshot       = false
  copy_tags_to_snapshot     = true

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-postgres"
    Component = "database"
  })

  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      password,  # Managed by secrets manager rotation
      latest_restorable_time
    ]
  }
}

# ==================== RDS MONITORING ROLE ====================

resource "aws_iam_role" "rds_monitoring" {
  name_prefix = "${local.name_prefix}-rds-monitoring-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-rds-monitoring-role"
    Component = "iam"
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# ==================== READ REPLICA (Optional) ====================

resource "aws_db_instance" "read_replica" {
  count = var.enable_read_replica ? 1 : 0

  identifier             = "${local.name_prefix}-postgres-read-replica"
  replicate_source_db    = aws_db_instance.main.id
  instance_class         = "db.r6g.large"  # Can be different from primary
  publicly_accessible    = false
  auto_minor_version_upgrade = false

  # Performance Insights
  performance_insights_enabled = true
  performance_insights_kms_key_id = aws_kms_key.main.arn
  performance_insights_retention_period = 7

  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-postgres-read-replica"
    Component = "database"
    Type      = "read-replica"
  })
}

# ==================== CLOUDWATCH ALARMS ====================

# CPU Utilization
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  alarm_name          = "${local.name_prefix}-database-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions         = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-database-cpu-alarm"
    Component = "monitoring"
  })
}

# Database Connections
resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "${local.name_prefix}-database-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS connection count"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-database-connections-alarm"
    Component = "monitoring"
  })
}

# Free Storage Space
resource "aws_cloudwatch_metric_alarm" "database_free_storage" {
  alarm_name          = "${local.name_prefix}-database-free-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "2000000000"  # 2GB in bytes
  alarm_description   = "This metric monitors RDS free storage space"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-database-storage-alarm"
    Component = "monitoring"
  })
}

# ==================== SNS TOPIC FOR ALERTS ====================

resource "aws_sns_topic" "alerts" {
  name              = "${local.name_prefix}-alerts"
  kms_master_key_id = aws_kms_key.main.arn

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-alerts"
    Component = "monitoring"
  })
}

resource "aws_sns_topic_subscription" "email_alerts" {
  count = length(var.alert_email_addresses)

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email_addresses[count.index]
}

# ==================== ELASTICACHE REDIS ====================

resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.name_prefix}-redis-subnet-group"
  subnet_ids = module.vpc.private_subnet_ids

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-redis-subnet-group"
    Component = "cache"
  })
}

resource "aws_elasticache_parameter_group" "main" {
  family = "redis7.x"
  name   = "${local.name_prefix}-redis-params"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-redis-params"
    Component = "cache"
  })
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${local.name_prefix}-redis"
  description                = "Redis cluster for MINEDU RAG"
  
  node_type                  = "cache.r7g.large"
  port                       = 6379
  parameter_group_name       = aws_elasticache_parameter_group.main.name
  
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_auth_token.result
  kms_key_id                = aws_kms_key.main.arn
  
  # Backup configuration
  snapshot_retention_limit = 7
  snapshot_window         = "03:00-05:00"
  
  # Maintenance
  maintenance_window = "sun:05:00-sun:07:00"
  
  # Logging
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow_log.name
    destination_type = "cloudwatch-logs"
    log_format       = "text"
    log_type         = "slow-log"
  }

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-redis"
    Component = "cache"
  })
}

resource "random_password" "redis_auth_token" {
  length  = 64
  special = false
}

resource "aws_cloudwatch_log_group" "redis_slow_log" {
  name              = "/aws/elasticache/redis/${local.name_prefix}/slow-log"
  retention_in_days = 30
  kms_key_id       = aws_kms_key.main.arn

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-redis-slow-log"
    Component = "logging"
  })
}

# ==================== SECRETS FOR REDIS ====================

resource "aws_secretsmanager_secret" "redis_credentials" {
  name                    = "${local.name_prefix}-redis-credentials"
  description             = "Redis credentials for MINEDU RAG"
  recovery_window_in_days = 7
  kms_key_id             = aws_kms_key.main.arn

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-redis-credentials"
    Component = "cache"
  })
}

resource "aws_secretsmanager_secret_version" "redis_credentials" {
  secret_id = aws_secretsmanager_secret.redis_credentials.id
  secret_string = jsonencode({
    auth_token = random_password.redis_auth_token.result
    host       = aws_elasticache_replication_group.main.configuration_endpoint_address
    port       = aws_elasticache_replication_group.main.port
  })
}