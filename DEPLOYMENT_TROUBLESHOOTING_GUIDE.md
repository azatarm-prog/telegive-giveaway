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




### 2. Database Tables Not Created

**Error:**
```
(psycopg2.errors.UndefinedTable) relation "giveaways" does not exist
```

**Root Cause:**
- The database was created, but the tables were not initialized.
- The `db.create_all()` command was not executed after the database connection was established.

**Solution:**
- Create an admin endpoint to initialize the database tables from within the running service.
- This ensures that the tables are created with the correct database connection.

**Example Admin Endpoint:**
```python
@admin_bp.route('/admin/init-db', methods=['POST'])
def init_database():
    try:
        db.create_all()
        return jsonify({'success': True, 'message': 'Database tables created successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

**Usage:**
```bash
curl -X POST https://your-service-url/admin/init-db
```

**Prevention:**
- Ensure that your deployment process includes a step to initialize the database tables.
- Consider using a database migration tool like Alembic to manage schema changes.




---

## Database Initialization Issues

### 1. Database Tables Not Created After Deployment

**Error:**
```
(psycopg2.errors.UndefinedTable) relation "giveaways" does not exist
LINE 1: SELECT COUNT(*) FROM giveaways
```

**Root Cause:**
- Database connection established but tables not initialized
- `db.create_all()` not executed during deployment
- No automatic database migration process

**Solution:**
Create admin endpoints for remote database initialization:

```python
# routes/admin.py
@admin_bp.route('/admin/init-db', methods=['POST'])
def init_database():
    try:
        # Create tables using raw SQL for better control
        create_tables_sql = [
            """CREATE TABLE IF NOT EXISTS giveaways (
                id BIGSERIAL PRIMARY KEY,
                account_id BIGINT NOT NULL,
                title VARCHAR(255) NOT NULL,
                main_body TEXT NOT NULL,
                winner_count INTEGER DEFAULT 1,
                -- ... other fields
            );""",
            # Add other table creation statements
        ]
        
        for sql in create_tables_sql:
            db.session.execute(text(sql))
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Database tables created'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

**Usage:**
```bash
# Initialize database after deployment
curl -X POST https://your-service-url/admin/init-db
```

**Prevention:**
- Include database initialization in deployment pipeline
- Use database migration tools like Alembic
- Add health checks that verify table existence

### 2. Database Connection Timeout During Initialization

**Error:**
```
psycopg2.OperationalError: connection to server terminated unexpectedly
```

**Root Cause:**
- Railway database connection limits
- Long-running initialization queries
- Network connectivity issues

**Solution:**
```python
# Use connection pooling and retry logic
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600    # Recycle connections every hour
)
```

---

## Circular Import and Model Factory Issues

### 1. Circular Import with SQLAlchemy Models

**Error:**
```
ImportError: cannot import name 'Giveaway' from 'models'
```

**Root Cause:**
- Direct model imports in __init__.py
- Models trying to import db before it's initialized
- Circular dependency between app.py and models

**Solution:**
Use factory pattern for model creation:

```python
# models/__init__.py
from .giveaway import create_giveaway_model
from .giveaway_stats import create_giveaway_stats_model

# Models will be created by factory functions
Giveaway = None
GiveawayStats = None

# app.py
from models import create_giveaway_model, create_giveaway_stats_model

# Create models after db is initialized
Giveaway = create_giveaway_model(db)
GiveawayStats = create_giveaway_stats_model(db)

# Set models in routes to avoid circular imports
routes.giveaways.Giveaway = Giveaway
routes.health.Giveaway = Giveaway
```

**Model Factory Example:**
```python
# models/giveaway.py
def create_giveaway_model(db):
    class Giveaway(db.Model):
        __tablename__ = 'giveaways'
        id = db.Column(db.BigInteger, primary_key=True)
        # ... other fields
    return Giveaway
```

### 2. Module Import Order Issues

**Error:**
```
AttributeError: module 'routes.giveaways' has no attribute 'db'
```

**Root Cause:**
- Dependencies set before modules are imported
- Incorrect import order in app.py

**Solution:**
```python
# app.py - Correct order
# 1. Import route modules first
import routes.giveaways
import routes.health

# 2. Set dependencies after import
routes.giveaways.db = db
routes.giveaways.Giveaway = Giveaway

# 3. Import blueprints last
from routes.giveaways import giveaways_bp
from routes.health import health_bp
```

---

## Railway Platform Specific Issues

### 1. Environment Variable Resolution

**Error:**
```
Invalid PORT value: '$PORT', using default 8003
```

**Root Cause:**
- Railway's PORT variable not properly resolved
- Conflicting deployment configurations

**Solution:**
```python
# Always use os.getenv for Railway variables
import os

port = int(os.getenv('PORT', app.config.get('SERVICE_PORT', 8000)))

# Never hardcode Railway variables in railway.json
# Let Railway set PORT automatically
```

### 2. Database URL Format Issues

**Error:**
```
sqlalchemy.exc.ArgumentError: Invalid DATABASE_URL format
```

**Common Railway Issues:**
```bash
# Wrong - has quotes around variable
DATABASE_URL="${{Postgres.DATABASE_PUBLIC_URL}}"

# Correct - no quotes
DATABASE_URL=${{Postgres.DATABASE_PUBLIC_URL}}

# Wrong - using private URL for external connections
DATABASE_URL=${{Postgres.DATABASE_PRIVATE_URL}}

# Correct - use public URL for Railway deployments
DATABASE_URL=${{Postgres.DATABASE_PUBLIC_URL}}
```

### 3. Service Discovery and Health Checks

**Error:**
```
requests.exceptions.ConnectionError: HTTPSConnectionPool
```

**Root Cause:**
- Services trying to connect before other services are deployed
- Hardcoded localhost URLs in service calls

**Solution:**
```python
# services/base_service.py
class BaseService:
    @staticmethod
    def is_service_healthy():
        try:
            service_url = os.getenv('SERVICE_URL', 'http://localhost:8000')
            response = requests.get(f"{service_url}/health/live", timeout=5)
            return response.status_code == 200
        except:
            return False

# Use environment variables for service URLs
AUTH_SERVICE_URL = os.getenv('TELEGIVE_AUTH_URL', 'http://localhost:8001')
CHANNEL_SERVICE_URL = os.getenv('TELEGIVE_CHANNEL_URL', 'http://localhost:8002')
```

---

## Flask Application Configuration Issues

### 1. CORS Configuration for Microservices

**Error:**
```
Access to fetch at 'https://service.railway.app' from origin 'https://frontend.com' has been blocked by CORS policy
```

**Solution:**
```python
from flask_cors import CORS

# Configure CORS for microservice architecture
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://telegive-frontend.vercel.app", "http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    },
    r"/health/*": {
        "origins": "*",  # Health checks can be accessed from anywhere
        "methods": ["GET"]
    }
})
```

### 2. Rate Limiting Configuration Warnings

**Warning:**
```
Using the in-memory storage for tracking rate limits as no storage was explicitly specified
```

**Solution:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

# For production, use Redis for rate limiting
redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

limiter = Limiter(
    app,
    key_func=get_remote_address,
    storage_uri=os.getenv('REDIS_URL', 'memory://'),  # Fallback to memory for dev
    default_limits=["1000 per day", "100 per hour"]
)
```

---

## Testing and Validation Issues

### 1. Health Check Endpoint Failures

**Error:**
```
{"status": "unhealthy", "database": "disconnected"}
```

**Root Cause:**
- Health checks running before database is ready
- Incorrect SQL syntax in health checks

**Solution:**
```python
@health_bp.route('/health/database', methods=['GET'])
def database_health():
    try:
        # Use simple query that works across PostgreSQL versions
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        
        # Test table access if tables exist
        try:
            giveaway_count = Giveaway.query.count()
        except Exception:
            giveaway_count = "tables_not_initialized"
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'giveaway_count': giveaway_count
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 503
```

### 2. API Endpoint Testing Issues

**Error:**
```
{"error": "Account validation failed: 404", "error_code": "ACCOUNT_VALIDATION_FAILED"}
```

**Root Cause:**
- Testing with non-existent account IDs
- Auth service not available during testing

**Testing Strategy:**
```bash
# Test endpoints that don't require external services first
curl -X GET https://service.railway.app/health/live

# Test validation logic with proper error handling
curl -X GET https://service.railway.app/api/giveaways/by-token/12345678901234567890123456789012

# Test CORS configuration
curl -X OPTIONS https://service.railway.app/api/giveaways/create -H "Origin: https://example.com" -v
```

---

## Deployment Pipeline Best Practices

### 1. Pre-Deployment Checklist

Before deploying any microservice:

```bash
# 1. Test requirements locally
pip install -r requirements.txt

# 2. Verify environment variables
python -c "import os; print('DATABASE_URL:', bool(os.getenv('DATABASE_URL')))"

# 3. Test database connection
python -c "from app import db; db.create_all(); print('Database OK')"

# 4. Run health checks locally
python -c "from app import app; app.test_client().get('/health')"

# 5. Verify all imports work
python -c "from app import app; print('Imports OK')"
```

### 2. Post-Deployment Verification

After deployment:

```bash
# 1. Check service is alive
curl https://service.railway.app/health/live

# 2. Initialize database if needed
curl -X POST https://service.railway.app/admin/init-db

# 3. Verify database health
curl https://service.railway.app/health/database

# 4. Test main functionality
curl https://service.railway.app/health

# 5. Check logs for errors
# (Check Railway dashboard logs)
```

### 3. Environment Variables Template

Create `.env.example` for each service:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Service Configuration
SERVICE_NAME=telegive-giveaway
SERVICE_PORT=8003
SECRET_KEY=your-secret-key

# External Services (update after deployment)
TELEGIVE_AUTH_URL=https://telegive-auth-production.up.railway.app
TELEGIVE_CHANNEL_URL=https://telegive-channel-production.up.railway.app
TELEGIVE_BOT_URL=https://telegive-bot-production.up.railway.app
TELEGIVE_PARTICIPANT_URL=https://telegive-participant-production.up.railway.app
TELEGIVE_MEDIA_URL=https://telegive-media-production.up.railway.app

# Optional
REDIS_URL=redis://localhost:6379
FLASK_DEBUG=False
```

---

## Quick Debugging Commands

When deployment fails, run these commands in order:

```bash
# 1. Check service status
curl -s https://service.railway.app/health/live | jq .

# 2. Check database connectivity
curl -s https://service.railway.app/health/database | jq .

# 3. Check external service dependencies
curl -s https://service.railway.app/health/services | jq .

# 4. Initialize database if needed
curl -X POST https://service.railway.app/admin/init-db | jq .

# 5. Test main API endpoints
curl -s https://service.railway.app/api/endpoint | jq .

# 6. Check CORS configuration
curl -X OPTIONS https://service.railway.app/api/endpoint -H "Origin: https://example.com" -v
```

Remember: Document every new issue and solution you encounter to help future deployments!

