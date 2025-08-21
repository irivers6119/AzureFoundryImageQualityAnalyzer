# 🔒 SECURITY GUIDE

## Overview
This document outlines security best practices for the Image Quality Analyzer project to prevent secrets leakage and ensure secure deployment.

## 🚨 Critical Security Checklist

### ✅ Environment Variables
- [ ] `.env` file contains only placeholder values
- [ ] `.env.example` template is provided for reference
- [ ] All sensitive values use environment variables
- [ ] No hardcoded API keys, endpoints, or secrets in source code

### ✅ Git Security
- [ ] `.env` is listed in `.gitignore`
- [ ] `.env` is not tracked in version control
- [ ] No secrets committed to repository history
- [ ] Repository is set to private (if applicable)

### ✅ Azure Resource Security
- [ ] API keys are regenerated if compromised
- [ ] Least-privilege access policies applied
- [ ] Resource access restrictions configured
- [ ] Monitoring and alerting enabled

## 🔐 Secret Management

### Environment Variables Used
| Variable | Purpose | Example |
|----------|---------|---------|
| `AOAI_ENDPOINT` | Azure OpenAI endpoint URL | `https://your-resource.openai.azure.com/...` |
| `AOAI_KEY` | Azure OpenAI API key | `your-32-char-key` |
| `AZURE_COMPUTER_VISION_ENDPOINT` | Computer Vision endpoint | `https://your-resource.cognitiveservices.azure.com/` |
| `AZURE_COMPUTER_VISION_KEY` | Computer Vision API key | `your-32-char-key` |

### Local Development Setup
1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Update with your values:**
   ```bash
   # Edit .env with your actual Azure credentials
   nano .env
   ```

3. **Verify git exclusion:**
   ```bash
   # Ensure .env is not tracked
   git status --ignored
   ```

### Production Deployment

#### Option 1: Environment Variables (Recommended)
```bash
# Set environment variables in your deployment system
export AZURE_COMPUTER_VISION_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
export AZURE_COMPUTER_VISION_KEY="your-actual-key"
```

#### Option 2: Azure Key Vault (Enterprise)
```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://your-vault.vault.azure.net/", credential=credential)

# Retrieve secrets from Key Vault
endpoint = client.get_secret("computer-vision-endpoint").value
key = client.get_secret("computer-vision-key").value
```

#### Option 3: Docker Secrets
```bash
# Using Docker secrets for container deployment
echo "your-key" | docker secret create cv_key -
docker service create --secret cv_key your-image
```

## 🛡️ Security Best Practices

### 1. Key Rotation
- Rotate Azure API keys monthly
- Use multiple keys for zero-downtime rotation
- Update environment variables after rotation

### 2. Access Control
- Use Azure RBAC for resource access
- Implement least-privilege principle
- Regular access reviews

### 3. Monitoring
- Enable Azure Monitor for API usage
- Set up alerts for unusual activity
- Log access patterns

### 4. Code Security
```python
# ✅ GOOD: Use environment variables
import os
endpoint = os.getenv('AZURE_COMPUTER_VISION_ENDPOINT')
key = os.getenv('AZURE_COMPUTER_VISION_KEY')

# ❌ BAD: Hardcoded secrets
endpoint = "https://myresource.cognitiveservices.azure.com/"
key = "my-secret-key-12345"
```

### 5. Container Security
```dockerfile
# ✅ GOOD: Runtime secrets
ENV AZURE_COMPUTER_VISION_ENDPOINT=""
ENV AZURE_COMPUTER_VISION_KEY=""

# ❌ BAD: Build-time secrets
ENV AZURE_COMPUTER_VISION_KEY="my-secret-key"
```

## 🚨 Incident Response

### If Secrets Are Compromised:
1. **Immediate Actions:**
   - Regenerate compromised API keys
   - Update all applications with new keys
   - Review access logs for unauthorized usage

2. **Investigation:**
   - Check git history for committed secrets
   - Review container images for embedded secrets
   - Audit deployment configurations

3. **Prevention:**
   - Implement secret scanning tools
   - Add pre-commit hooks
   - Regular security audits

### Emergency Commands:
```bash
# Remove secrets from git history (if accidentally committed)
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch .env' \
--prune-empty --tag-name-filter cat -- --all

# Force push to remove from remote (DANGEROUS)
git push origin --force --all
```

## 📋 Security Audit Checklist

### Pre-deployment Audit:
- [ ] Run `git log --oneline | grep -i 'env\|key\|secret'` to check history
- [ ] Verify `.env` is in `.gitignore`
- [ ] Confirm no hardcoded credentials in source code
- [ ] Test with placeholder values in CI/CD
- [ ] Validate environment variable injection works

### Regular Security Reviews:
- [ ] Monthly key rotation
- [ ] Quarterly access review
- [ ] Annual security audit
- [ ] Penetration testing (if applicable)

## 🔗 Resources
- [Azure Security Best Practices](https://docs.microsoft.com/en-us/azure/security/)
- [Azure Key Vault Documentation](https://docs.microsoft.com/en-us/azure/key-vault/)
- [Git Secrets Tool](https://github.com/awslabs/git-secrets)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)

---
**⚠️ Remember: Security is everyone's responsibility. When in doubt, ask the security team!**
