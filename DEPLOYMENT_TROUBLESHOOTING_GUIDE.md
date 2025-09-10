# Telegive Giveaway Management Service - Deployment Troubleshooting Guide

This document contains all deployment and build errors encountered during the development and deployment of the Giveaway Management Service, along with their solutions.

## Table of Contents

1. [Build Errors](#build-errors)
2. [Deployment Configuration Conflicts](#deployment-configuration-conflicts)
3. [Port and Networking Issues](#port-and-networking-issues)
4. [Database Connection Errors](#database-connection-errors)
5. [Environment Configuration Issues](#environment-configuration-issues)
6. [Prevention Best Practices](#prevention-best-practices)

---

## Build Errors

### 1. Missing Dependencies

**Error:**
```
ERROR: Could not find a version that satisfies the requirement http-status==0.2.1
```

**Root Cause:**
- Invalid package version specified in requirements.txt
- Package version doesn't exist on PyPI

**Solution:**
```bash
# Remove invalid package versions from requirements.txt
# Verify all packages exist on PyPI before adding
pip install -r requirements.txt  # Test locally first
```

**Prevention:**
- Always test requirements.txt locally before deployment
- Use `pip freeze` to generate exact working versions
- Verify package versions exist on PyPI

---

## Deployment Configuration Conflicts

### 1. Procfile and railway.json Conflict

**Error:**
```
Error: '$PORT' is not a valid port number.
```

**Root Cause:**
- Having both Procfile and railway.json with nixpacks builder creates conflicting deployment configurations
- Railway tries to use both deployment methods simultaneously
- The `$PORT` variable expansion fails in this conflicted state

**Solution:**

**Option A: Use railway.json only (Recommended)**
```bash
# Remove Procfile completely
rm Procfile

# Keep railway.json with nixpacks builder
{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "startCommand": "python app.py"
  }
}

# Ensure app.py handles PORT correctly
port = int(os.getenv('PORT', app.config['SERVICE_PORT']))
app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)
```

**Option B: Use Procfile only**
```bash
# Remove railway.json
rm railway.json

# Keep Procfile with proper gunicorn command
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

**Prevention:**
- Choose ONE deployment method: either Procfile OR railway.json
- Never use both simultaneously
- Document your chosen deployment method in README

### 2. Incorrect PORT Variable Format

**Error:**
```
Invalid PORT value: '$PORT', using default 8003
```

**Root Cause:**
- PORT environment variable not properly resolved
- Literal string '$PORT' instead of actual port number

**Solution:**
```python
# Use this pattern in app.py (matches working services)
if __name__ == '__main__':
    # Get configuration from environment
    port = int(os.getenv('PORT', app.config['SERVICE_PORT']))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Giveaway Management Service on port {port}")
    
    # Run the application
    app.run(
        host='0.0.0.0',  # Listen on all interfaces for deployment
        port=port,
        debug=debug,
        threaded=True
    )
```

**Environment Variables:**
```bash
# In Railway, set these variables:
SERVICE_NAME="giveaway-service"
SERVICE_PORT="8003"
# PORT is automatically set by Railway - do not define manually
```

---

## Port and Networking Issues

### 1. Port Mismatch

**Error:**
```
502 Bad Gateway - Application failed to respond
```

**Root Cause:**
- Railway domain configured for different port than application
- Application not listening on Railway's assigned PORT

**Solution:**
```bash
# Check what port your app is running on (from logs)
[INFO] Starting Giveaway Management Service on port 8003

# Ensure app uses Railway's PORT variable
port = int(os.getenv('PORT', app.config['SERVICE_PORT']))

# If still failing, delete current domain and create new one
```

### 2. Host Binding Issues

**Error:**
```
Connection refused
```

**Root Cause:**
- Application binding to localhost instead of 0.0.0.0
- Railway cannot route traffic to localhost-bound services

**Solution:**
```python
# Always bind to 0.0.0.0 for Railway deployment
app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)
```

---

## Database Connection Errors

### 1. Invalid DATABASE_URL Format

**Error:**
```
Invalid DATABASE_URL format
```

**Common Issues:**
```bash
# Wrong - has quotes
DATABASE_URL="${{Postgres.DATABASE_PUBLIC_URL}}"

# Correct - no quotes
DATABASE_URL=${{Postgres.DATABASE_PUBLIC_URL}}
```

**Solution:**
```bash
# Use environment variables with defaults
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/telegive_db')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

# Validate required variables
required_vars = ['DATABASE_URL', 'SECRET_KEY', 'TELEGIVE_AUTH_URL']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise Exception(f"Missing required environment variables: {missing_vars}")
```

---

## Environment Configuration Issues

### 1. Environment Variable Not Updated

**Root Cause:**
- Service not restarted after variable change
- Variable cached in application

**Solution:**
1. Update variable in Railway dashboard
2. Wait for automatic restart (1-2 minutes)
3. Or manually restart service
4. Verify with health check

### 2. Missing Required Variables

**Error:**
```
KeyError: 'REQUIRED_ENV_VAR'
```

**Solution:**
```python
# Use environment variables with defaults
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/telegive_db')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

# Validate required variables
required_vars = ['DATABASE_URL', 'SECRET_KEY', 'TELEGIVE_AUTH_URL']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise Exception(f"Missing required environment variables: {missing_vars}")
```

---

## Prevention Best Practices

### 1. Deployment Configuration

- **Choose one deployment method**: Either Procfile OR railway.json, never both
- **Test locally first**: Always test your deployment configuration locally
- **Use consistent patterns**: Follow the same PORT handling pattern across all services
- **Document your choice**: Clearly document which deployment method you're using

### 2. Environment Variables

- **Use defaults**: Always provide fallback values for environment variables
- **Validate on startup**: Check for required variables at application startup
- **Use consistent naming**: Follow the same naming convention across services
- **Document all variables**: Maintain a .env.example file with all required variables

### 3. Port Configuration

- **Always bind to 0.0.0.0**: Never bind to localhost in production
- **Use Railway's PORT**: Always read the PORT environment variable
- **Provide fallbacks**: Have a default port for local development
- **Log the port**: Always log which port the service is starting on

### 4. Testing

- **Test requirements.txt**: Always test your dependencies locally
- **Test environment variables**: Verify all required variables are set
- **Test health endpoints**: Ensure health checks work before deployment
- **Monitor logs**: Watch deployment logs for any errors

### 5. Documentation

- **Update troubleshooting guides**: Document any new issues and solutions
- **Maintain README**: Keep deployment instructions up to date
- **Share knowledge**: Update team documentation with lessons learned

---

## Quick Debugging Checklist

When deployment fails, check these in order:

1. **Check Railway logs** for specific error messages
2. **Verify environment variables** are set correctly
3. **Confirm deployment method** (Procfile vs railway.json)
4. **Test requirements.txt** locally
5. **Verify PORT handling** in your application
6. **Check database connection** if applicable
7. **Compare with working service** configuration
8. **Review recent changes** that might have caused the issue

---

## Getting Help

If you encounter an issue not covered in this guide:

1. Check Railway deployment logs for specific error messages
2. Compare your configuration with a working service
3. Test the problematic component locally
4. Document the issue and solution for future reference
5. Update this troubleshooting guide with your findings

Remember: Every deployment issue is a learning opportunity that can help prevent future problems!

