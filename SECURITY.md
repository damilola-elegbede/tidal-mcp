# Security Policy

## 🚨 Emergency Security Response

This document is part of our emergency security response protocol. All users and contributors must follow these security guidelines immediately.

## 📋 Table of Contents

- [Reporting Security Vulnerabilities](#reporting-security-vulnerabilities)
- [Credential Security Requirements](#credential-security-requirements)
- [Session Management Guidelines](#session-management-guidelines)
- [Secure Development Practices](#secure-development-practices)
- [Production Deployment Security](#production-deployment-security)
- [Security Monitoring](#security-monitoring)
- [Incident Response](#incident-response)

## 🔐 Reporting Security Vulnerabilities

### Immediate Reporting

If you discover a security vulnerability, **DO NOT** create a public GitHub issue. Instead:

1. **Email**: Send details to `security@tidal-mcp.dev` (if available)
2. **Encrypted Communication**: Use PGP encryption when possible
3. **Response Time**: We will acknowledge receipt within 24 hours
4. **Disclosure Timeline**: We aim to address critical vulnerabilities within 72 hours

### What to Include

When reporting a vulnerability, please include:

- **Description**: Clear description of the vulnerability
- **Impact**: Potential impact and attack scenarios
- **Reproduction**: Step-by-step instructions to reproduce
- **Environment**: Version numbers, OS, and configuration details
- **Suggested Fix**: If you have a potential solution

### Responsible Disclosure

- We follow a 90-day disclosure timeline
- Security researchers are credited in our security advisories
- We do not pursue legal action against security researchers who follow responsible disclosure

## 🛡️ Credential Security Requirements

### CRITICAL: Never Commit Credentials

**ABSOLUTE PROHIBITION**: The following must NEVER be committed to version control:

```bash
# Prohibited files and patterns
.env
.env.*
*.env
*_credentials.json
*_secrets.yaml
*.session
auth_token*
tidal_token*
client_secret*
```

### Environment Variable Management

#### Local Development

1. **Use .env Files**:
   ```bash
   # .env (never commit this file)
   TIDAL_CLIENT_ID=your_client_id_here
   TIDAL_CLIENT_SECRET=your_very_secret_key_here
   TIDAL_TOKEN_CACHE_PATH=/secure/path/to/tokens
   ```

2. **Set Secure Permissions**:
   ```bash
   chmod 600 .env
   chmod 700 /secure/path/to/tokens
   ```

3. **Validate .gitignore**:
   ```bash
   # Add these patterns to .gitignore
   .env
   .env.*
   *.session
   tokens/
   .tidal_cache/
   auth_cache/
   credentials/
   secrets/
   ```

#### Production Environments

1. **Use Platform Secret Management**:
   - **AWS**: AWS Secrets Manager, Parameter Store
   - **Azure**: Azure Key Vault
   - **Google Cloud**: Secret Manager
   - **Kubernetes**: Secrets with RBAC
   - **Docker**: Docker Secrets

2. **Environment Variables Only**:
   ```bash
   # Production deployment (no .env files)
   export TIDAL_CLIENT_ID="${VAULT_TIDAL_CLIENT_ID}"
   export TIDAL_CLIENT_SECRET="${VAULT_TIDAL_CLIENT_SECRET}"
   ```

3. **Implement Credential Rotation**:
   - Rotate client secrets every 90 days
   - Implement automated rotation where possible
   - Monitor for credential expiration

## 🔑 Session Management Guidelines

### Authentication Security

1. **OAuth2 Best Practices**:
   - Use secure redirect URIs only
   - Implement PKCE (Proof Key for Code Exchange)
   - Validate state parameters
   - Handle token refresh securely

2. **Token Storage**:
   ```python
   # Secure token storage configuration
   TIDAL_TOKEN_CACHE_PATH = "/secure/tokens/"

   # Set restrictive permissions
   import os
   import stat

   token_dir = os.path.dirname(TIDAL_TOKEN_CACHE_PATH)
   os.chmod(token_dir, stat.S_IRWXU)  # 700 permissions
   ```

3. **Session Expiration**:
   - Tokens expire automatically for security
   - Implement proper token refresh logic
   - Handle authentication failures gracefully

### Token Security

1. **Storage Requirements**:
   - Store tokens in secure, encrypted storage
   - Never log or print token values
   - Use memory-only storage when possible

2. **Transmission Security**:
   - Always use HTTPS for token transmission
   - Implement certificate pinning where applicable
   - Validate SSL/TLS certificates

3. **Token Validation**:
   ```python
   # Example secure token validation
   async def validate_token(token):
       if not token or len(token) < 32:
           raise SecurityError("Invalid token format")

       # Validate token signature
       # Check token expiration
       # Verify token scope
   ```

## 👩‍💻 Secure Development Practices

### Code Security Standards

1. **Input Validation**:
   ```python
   # Always validate and sanitize inputs
   def validate_playlist_name(name: str) -> str:
       if not name or len(name.strip()) == 0:
           raise ValueError("Playlist name cannot be empty")

       if len(name) > 255:
           raise ValueError("Playlist name too long")

       # Remove potentially dangerous characters
       return name.strip()
   ```

2. **Error Handling**:
   ```python
   # Never expose sensitive information in errors
   try:
       result = await tidal_api_call()
   except AuthenticationError:
       logger.warning("Authentication failed", extra={"user_id": user_id})
       raise AuthenticationError("Authentication required")
   except Exception as e:
       logger.error("API call failed", extra={"error_type": type(e).__name__})
       raise APIError("Request failed")
   ```

3. **Logging Security**:
   ```python
   # Secure logging practices
   import logging

   # Never log sensitive data
   logger.info("User authenticated", extra={
       "user_id": user_id,  # OK to log
       # "access_token": token,  # NEVER log tokens
       "timestamp": datetime.utcnow()
   })
   ```

### Dependency Security

1. **Regular Security Audits**:
   ```bash
   # Run security audits regularly
   pip audit
   safety check
   bandit -r src/
   ```

2. **Dependency Management**:
   ```bash
   # Pin dependency versions
   pip install --upgrade pip
   pip install -r requirements.txt --no-deps
   ```

3. **Vulnerability Monitoring**:
   - Use GitHub Dependabot or similar tools
   - Monitor CVE databases for dependency vulnerabilities
   - Update dependencies promptly when security patches are available

### Pre-commit Security Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key
      - id: check-yaml

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-x', 'tests/']
```

## 🏭 Production Deployment Security

### Infrastructure Security

1. **Network Security**:
   - Use VPCs and security groups
   - Implement least-privilege network access
   - Enable WAF for web-facing components

2. **Container Security**:
   ```dockerfile
   # Secure Dockerfile practices
   FROM python:3.11-slim

   # Create non-root user
   RUN useradd --create-home --shell /bin/bash tidal
   USER tidal

   # Set secure working directory
   WORKDIR /app

   # Copy requirements and install dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy application code
   COPY . .

   # Set secure permissions
   RUN chmod 755 /app
   ```

3. **Secrets Management**:
   ```yaml
   # Kubernetes deployment with secrets
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: tidal-mcp
   spec:
     template:
       spec:
         containers:
         - name: tidal-mcp
           env:
           - name: TIDAL_CLIENT_ID
             valueFrom:
               secretKeyRef:
                 name: tidal-secrets
                 key: client-id
           - name: TIDAL_CLIENT_SECRET
             valueFrom:
               secretKeyRef:
                 name: tidal-secrets
                 key: client-secret
   ```

### Monitoring and Alerting

1. **Security Monitoring**:
   ```python
   # Security event logging
   import structlog

   security_logger = structlog.get_logger("security")

   async def log_authentication_event(user_id: str, success: bool, ip: str):
       security_logger.info(
           "authentication_attempt",
           user_id=user_id,
           success=success,
           source_ip=ip,
           timestamp=datetime.utcnow().isoformat()
       )
   ```

2. **Alert Configuration**:
   - Failed authentication attempts (>5 in 10 minutes)
   - Unusual API usage patterns
   - Token refresh failures
   - Credential rotation due dates

## 📊 Security Monitoring

### Metrics to Monitor

1. **Authentication Metrics**:
   - Failed login attempts
   - Token refresh frequency
   - Session duration anomalies
   - Unusual access patterns

2. **API Security Metrics**:
   - Rate limiting violations
   - Invalid request patterns
   - Error rate spikes
   - Unauthorized access attempts

3. **Infrastructure Metrics**:
   - Certificate expiration dates
   - Security group changes
   - Network traffic anomalies
   - Resource access violations

### Security Dashboards

```python
# Example security metrics collection
class SecurityMetrics:
    def __init__(self):
        self.failed_auth_counter = Counter()
        self.api_error_counter = Counter()

    def record_failed_auth(self, user_id: str, reason: str):
        self.failed_auth_counter.inc({
            "user_id": user_id,
            "reason": reason,
            "timestamp": time.time()
        })

    def record_api_error(self, endpoint: str, error_type: str):
        self.api_error_counter.inc({
            "endpoint": endpoint,
            "error_type": error_type,
            "timestamp": time.time()
        })
```

## 🚨 Incident Response

### Security Incident Classification

1. **Critical (P0)**:
   - Credential compromise
   - Data breach
   - Service-wide authentication bypass

2. **High (P1)**:
   - Individual account compromise
   - API abuse
   - Unauthorized data access

3. **Medium (P2)**:
   - Suspicious activity patterns
   - Failed security controls
   - Configuration vulnerabilities

4. **Low (P3)**:
   - Security policy violations
   - Non-critical misconfigurations

### Response Procedures

1. **Immediate Response (0-1 hour)**:
   - Identify and contain the incident
   - Assess impact and scope
   - Notify security team
   - Begin incident documentation

2. **Short-term Response (1-24 hours)**:
   - Implement containment measures
   - Collect and preserve evidence
   - Notify affected users if required
   - Begin remediation activities

3. **Long-term Response (24+ hours)**:
   - Conduct thorough investigation
   - Implement permanent fixes
   - Update security policies
   - Conduct post-incident review

### Communication Plan

```markdown
# Security Incident Communication Template

## Incident Summary
- **Incident ID**: SEC-YYYY-MM-DD-001
- **Discovery Time**: [UTC timestamp]
- **Impact**: [Brief description]
- **Status**: [Investigating/Contained/Resolved]

## Technical Details
- **Affected Systems**: [List systems]
- **Attack Vector**: [How the incident occurred]
- **Scope**: [What data/users affected]

## Actions Taken
- [List containment actions]
- [List remediation steps]
- [List preventive measures]

## User Action Required
- [Any actions users need to take]
- [Timeline for user actions]
```

## 🔄 Security Policy Updates

This security policy is a living document and will be updated as:

- New threats are identified
- Security practices evolve
- Technology changes require updates
- Incident learnings are incorporated

**Last Updated**: 2025-09-20
**Next Review**: 2025-12-20
**Policy Version**: 1.0

## 📞 Contact Information

- **Security Team**: security@tidal-mcp.dev
- **Emergency Contact**: +1-XXX-XXX-XXXX
- **PGP Key**: [Security team PGP key]

---

**Remember**: Security is everyone's responsibility. When in doubt, err on the side of caution and consult the security team.
