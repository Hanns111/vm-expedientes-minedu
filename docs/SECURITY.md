# SECURITY DOCUMENTATION - MINEDU RAG SYSTEM v1.4.0

## 🛡️ SECURITY OVERVIEW

El sistema RAG MINEDU implementa seguridad de nivel gubernamental con múltiples capas de protección, cumpliendo con estándares ISO27001 y NIST Cybersecurity Framework.

## 🔐 AUTHENTICATION & AUTHORIZATION

### JWT Authentication System
```python
# JWT Configuration
JWT_SECRET_KEY: Clave secreta para firma de tokens
JWT_ALGORITHM: HS256 (HMAC with SHA-256)
JWT_EXPIRATION_HOURS: 24 horas por defecto
```

**Features:**
- **Token-based Authentication**: Stateless, scalable
- **Role-based Access Control**: admin, user, demo roles
- **Automatic Expiration**: Tokens con tiempo de vida limitado
- **Secure Token Storage**: HTTP-only cookies recomendado

### OAuth2 Integration
```python
# Supported Providers
- Google OAuth2 with PKCE
- Microsoft OAuth2 with PKCE
- PKCE (Proof Key for Code Exchange) for enhanced security
```

**Security Features:**
- **PKCE Implementation**: Protección contra authorization code interception
- **State Validation**: Prevención de CSRF attacks
- **Secure Redirects**: Whitelist de URLs permitidas
- **Token Refresh**: Renovación automática de tokens

### Password Security
```python
# bcrypt Configuration
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12  # High work factor
)
```

## 🔒 INPUT VALIDATION & SANITIZATION

### Query Sanitization
```python
class InputValidator:
    @staticmethod
    def sanitize_query(query: str) -> str:
        # 1. Length validation (max 500 chars)
        # 2. Dangerous pattern detection
        # 3. Character filtering (preserve Spanish)
        # 4. HTML escaping
        # 5. Multiple space normalization
```

**Protected Against:**
- **SQL Injection**: Pattern detection and parameterized queries
- **NoSQL Injection**: MongoDB-style injection prevention
- **LLM Prompt Injection**: Malicious prompt detection
- **XSS Attacks**: HTML escaping and character filtering
- **Path Traversal**: File path validation
- **Command Injection**: System command prevention

### Dangerous Pattern Detection
```python
DANGEROUS_PATTERNS = [
    "ignore previous instructions",
    "forget all previous",
    "you are now", 
    "act as if",
    "roleplay as",
    "pretend to be",
    "__import__",
    "eval(",
    "exec(",
    "<script",
    "javascript:",
    "data:text/html"
]

SQL_INJECTION_PATTERNS = [
    "union select",
    "drop table", 
    "delete from",
    "insert into",
    "update set",
    "alter table",
    "create table",
    "grant all",
    "revoke all"
]
```

## 🚨 RATE LIMITING

### Multi-Level Rate Limiting
```python
class RateLimiter:
    def __init__(self):
        self.limits = {
            "per_minute": 30,    # 30 requests per minute
            "per_hour": 500,     # 500 requests per hour  
            "per_day": 2000      # 2000 requests per day
        }
```

**Implementation:**
- **Redis-based Storage**: Distributed rate limiting
- **User-specific Limits**: Por user ID o IP address
- **Sliding Window**: Más preciso que fixed window
- **Graceful Degradation**: Respuestas HTTP 429 con Retry-After

### Rate Limit Headers
```http
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

## 🔍 PRIVACY PROTECTION

### PII Detection & Anonymization
```python
class PrivacyProtector:
    def __init__(self):
        self.pii_patterns = {
            "dni": r"\b\d{8}\b",
            "phone": r"(\+51|51)?[\s\-]?9\d{8}",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "ruc": r"\b[12]\d{10}\b",
            "address": r"(av\.|jr\.|calle|jirón)\s+[\w\s]+\d+"
        }
```

**Anonymization Methods:**
- **Hash-based**: SHA-256 para identificadores únicos
- **Masking**: Reemplazo con asteriscos (DNI: ***45678)
- **Generalization**: Categorización en lugar de valores específicos
- **Pseudonymization**: Reemplazo con identificadores ficticios

## 📊 AUDIT LOGGING & MONITORING

### Comprehensive Audit Trail
```python
class ComplianceLogger:
    def log_action(self, 
        user_id: str,
        action: str,
        resource: str,
        ip_address: str,
        user_agent: str,
        details: Dict[str, Any]
    ):
        # Complete audit log entry
```

**Logged Events:**
- **Authentication**: Login, logout, failed attempts
- **Authorization**: Permission denials, role changes
- **Data Access**: Query submissions, document retrievals
- **Administrative Actions**: User management, system configuration
- **Security Events**: Suspicious patterns, rate limit violations
- **System Changes**: Configuration updates, deployments

### Security Monitoring
```python
class SecurityMonitor:
    def __init__(self):
        self.suspicious_patterns = [
            "multiple_failed_logins",
            "unusual_query_patterns", 
            "high_request_frequency",
            "invalid_token_usage",
            "privilege_escalation_attempts"
        ]
```

**Alerting System:**
- **Real-time Detection**: Immediate suspicious activity alerts
- **Threshold-based**: Configurable limits para diferentes eventos
- **Integration Ready**: Webhook support para Slack, email, SIEM
- **False Positive Reduction**: Machine learning-based pattern recognition

## 🔐 DATA PROTECTION

### Encryption Standards
```python
# Data at Rest
- Database: PostgreSQL with TDE (Transparent Data Encryption)
- Vectorstores: AES-256 encryption for pickle files
- Configuration: Encrypted environment variables

# Data in Transit  
- HTTPS/TLS 1.3: All API communications
- Database Connections: SSL/TLS encrypted
- Internal Services: mTLS between components
```

### Secrets Management
```python
class SecretsManager:
    def __init__(self):
        self.providers = {
            "aws": AWSSecretsProvider(),
            "azure": AzureKeyVaultProvider(), 
            "env": EnvironmentProvider()
        }
```

**Secret Types:**
- **API Keys**: OpenAI, Anthropic, third-party services
- **Database Credentials**: PostgreSQL, Redis passwords
- **Encryption Keys**: JWT signing, data encryption
- **OAuth Secrets**: Client secrets for OAuth providers

### Safe File Operations
```python
class SafePickleLoader:
    ALLOWED_MODULES = {
        'numpy', 'pandas', 'scipy', 'sklearn',
        'torch', 'transformers', 'sentence_transformers'
    }
    
    def safe_load(self, file_path: str):
        # Validate file path
        # Check file integrity
        # Restricted unpickling
        # Virus scanning integration ready
```

## 🌐 NETWORK SECURITY

### API Security
```python
# CORS Configuration
CORS_ORIGINS = [
    "https://minedu.gob.pe",
    "https://rag.minedu.gob.pe",
    "http://localhost:3000"  # Development only
]

# Security Headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", 
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'"
}
```

### IP Filtering & Geolocation
```python
# Government Network Whitelist
ALLOWED_IP_RANGES = [
    "200.48.0.0/16",      # MINEDU network range
    "190.117.0.0/16",     # Government network  
    "10.0.0.0/8",         # Internal networks
    "192.168.0.0/16"      # Local development
]
```

## 🏛️ COMPLIANCE & STANDARDS

### ISO27001 Alignment
- **Information Security Management System (ISMS)**
- **Risk Assessment & Treatment**
- **Access Control Management** 
- **Incident Response Procedures**
- **Business Continuity Planning**
- **Regular Security Audits**

### NIST Cybersecurity Framework
```
IDENTIFY:
- Asset inventory and risk assessment
- Governance and risk management policies

PROTECT: 
- Access control and authentication
- Data security and privacy protection
- Protective technology deployment

DETECT:
- Security monitoring and event detection
- Anomaly detection and analysis

RESPOND:
- Incident response procedures
- Communication and analysis protocols

RECOVER:
- Recovery planning and improvements
- Lessons learned integration
```

### Government Data Protection
- **Ley de Protección de Datos Personales (Perú)**
- **Secreto Profesional y Reserva**
- **Transparencia y Acceso a la Información**
- **Archivo Digital y Conservación**

## 🚨 INCIDENT RESPONSE

### Security Incident Classification
```python
class IncidentSeverity:
    CRITICAL = "critical"    # System compromise, data breach
    HIGH = "high"           # Unauthorized access, service disruption  
    MEDIUM = "medium"       # Policy violations, suspicious activity
    LOW = "low"            # Minor policy deviations, warnings
```

### Response Procedures
1. **Detection & Analysis** (0-15 minutes)
   - Automated alert generation
   - Initial impact assessment
   - Incident classification

2. **Containment** (15-60 minutes)
   - Isolate affected systems
   - Preserve evidence
   - Prevent lateral movement

3. **Eradication & Recovery** (1-24 hours)
   - Remove threat vectors
   - Restore normal operations
   - Implement additional controls

4. **Post-Incident Activities** (24-72 hours)
   - Lessons learned documentation
   - Security control updates
   - Stakeholder communication

## 🔧 SECURITY CONFIGURATION

### Environment Security
```bash
# Production Environment Variables
export JWT_SECRET_KEY="$(openssl rand -base64 32)"
export DATABASE_ENCRYPTION_KEY="$(openssl rand -base64 32)"
export RATE_LIMIT_ENABLED=true
export AUDIT_LOGGING_ENABLED=true
export PII_PROTECTION_ENABLED=true
export SECURITY_HEADERS_ENABLED=true
```

### Database Security
```sql
-- PostgreSQL Security Configuration
CREATE ROLE minedu_rag_user WITH LOGIN ENCRYPTED PASSWORD 'complex_password';
GRANT CONNECT ON DATABASE minedu_rag TO minedu_rag_user;
GRANT USAGE ON SCHEMA public TO minedu_rag_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO minedu_rag_user;

-- Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation ON users FOR ALL TO minedu_rag_user USING (id = current_user_id());
```

### Security Testing
```python
# Automated Security Tests
def test_sql_injection_protection():
    malicious_payloads = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'/**/OR/**/1=1#"
    ]
    for payload in malicious_payloads:
        assert_secure_handling(payload)

def test_rate_limiting():
    # Burst request testing
    # Sustained load testing
    # Rate limit bypass attempts
```

## 📋 SECURITY CHECKLIST

### Pre-Deployment Security Review
- [ ] All secrets removed from code
- [ ] HTTPS enforced in production
- [ ] Database connections encrypted
- [ ] Rate limiting configured
- [ ] Audit logging enabled
- [ ] Security headers implemented
- [ ] Input validation tested
- [ ] Authentication mechanisms verified
- [ ] Authorization controls tested
- [ ] Error handling reviewed (no information leakage)
- [ ] Dependency security scan completed
- [ ] Security configuration reviewed

### Ongoing Security Maintenance
- [ ] Regular security updates
- [ ] Penetration testing (quarterly)
- [ ] Security audit reviews (annually)
- [ ] Incident response drills
- [ ] Security awareness training
- [ ] Compliance verification
- [ ] Backup and recovery testing

---
*Security Documentation - MINEDU RAG System v1.4.0*
*Government-grade security implementation*