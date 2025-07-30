# Security Guide - My Video Editor

## 🔐 API Key Management

### ⚠️ IMPORTANT SECURITY NOTICE
This project has been updated to use environment variables for all API keys. **Never commit API keys to version control.**

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Copy from .env.example and fill in your actual API keys
OPENAI_API_KEY=your_openai_api_key_here
GROK_API_KEY=your_grok_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MEMORIES_AI_KEY=your_memories_ai_key_here
```

### Git History Cleanup

This repository has undergone security remediation:

1. **Historical API keys removed**: Used `git filter-branch` to remove hardcoded API keys from git history
2. **Secure configuration**: All API keys now loaded from environment variables
3. **Protected files**: `.env` files are in `.gitignore` to prevent accidental commits

### Production Deployment Security

#### Environment Variables Setup
```bash
# Production environment
export ENV=prod
export OPENAI_API_KEY="your_production_openai_key"
export GROK_API_KEY="your_production_grok_key"
# ... other keys
```

#### Docker Deployment
```dockerfile
# Use environment variables, never hardcode
ENV OPENAI_API_KEY=""
ENV GROK_API_KEY=""
# Pass via docker run -e or docker-compose.yml
```

#### Docker Compose Example
```yaml
services:
  video-editor:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GROK_API_KEY=${GROK_API_KEY}
      - ENV=prod
```

### Security Best Practices

1. **Never commit secrets**:
   ```bash
   # Always check before committing
   git diff --cached
   # Look for API keys, passwords, tokens
   ```

2. **Use strong keys**:
   - Generate unique API keys for each environment
   - Rotate keys regularly
   - Use different keys for dev/staging/prod

3. **Environment isolation**:
   ```bash
   # Development
   ENV=dev
   MOCK_MODE=true
   
   # Production  
   ENV=prod
   MOCK_MODE=false
   ```

4. **Access control**:
   - Limit API key permissions where possible
   - Monitor API usage and costs
   - Use service accounts for production

### Troubleshooting

#### If you accidentally commit an API key:

1. **Immediately revoke the key** in your API provider dashboard
2. **Generate a new key**
3. **Update your environment variables**
4. **Consider git history cleanup** (contact maintainers)

#### GitHub Secret Scanning

GitHub automatically scans for secrets. If detected:
1. Revoke the exposed key immediately
2. Generate a new key
3. Update your local environment
4. The repository may be temporarily blocked from pushes

### Recovery from Security Issues

If you encounter the error:
```
GITHUB PUSH PROTECTION - Push cannot contain secrets
```

1. **Revoke the API key immediately**
2. **Create a new API key** 
3. **Update your `.env` file**
4. **Verify no hardcoded keys exist**:
   ```bash
   grep -r "sk-" . --exclude-dir=.git
   grep -r "api.*key" . --exclude-dir=.git
   ```

### Monitoring and Compliance

- **Regular audits**: Check for hardcoded secrets monthly
- **API usage monitoring**: Monitor for unusual API usage
- **Cost tracking**: Set up billing alerts for API services
- **Access logging**: Log API key usage where possible

### Emergency Contacts

If you discover a security vulnerability:
1. **Do NOT create a public issue**
2. **Revoke any exposed credentials immediately** 
3. **Contact repository maintainers privately**
4. **Follow responsible disclosure practices**

---

**Remember**: Security is everyone's responsibility. When in doubt, err on the side of caution and ask for help.
