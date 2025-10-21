# Docker Deployment Guide

This guide explains how to deploy InfiniProxy using Docker for easy, production-ready deployment.

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd infiniproxy
   ```

2. **Create environment file** (optional - can use docker-compose.yml defaults):
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the service**:
   ```bash
   docker-compose up -d
   ```

4. **Check logs**:
   ```bash
   docker-compose logs -f
   ```

5. **Access the admin panel**:
   - Open http://localhost:8000/admin/login-page
   - Default credentials: admin / changeme (⚠️ **Change these!**)

### Using Docker CLI

1. **Build the image**:
   ```bash
   docker build -t infiniproxy:latest .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     --name infiniproxy \
     -p 8000:8000 \
     -e OPENAI_BASE_URL=https://api.openai.com/v1/chat/completions \
     -e OPENAI_API_KEY=your-api-key-here \
     -e OPENAI_MODEL=gpt-4 \
     -e ADMIN_USERNAME=admin \
     -e ADMIN_PASSWORD=your-secure-password \
     -v $(pwd)/data:/app/data \
     infiniproxy:latest
   ```

## Configuration

### Environment Variables

#### Required
- `OPENAI_BASE_URL` - Backend OpenAI-compatible API endpoint
- `OPENAI_API_KEY` - API key for the backend service

#### Optional
- `OPENAI_MODEL` - Default model to use (default: `gpt-4`)
- `PROXY_HOST` - Host to bind to (default: `0.0.0.0`)
- `PROXY_PORT` - Port to listen on (default: `8000`)
- `MAX_INPUT_TOKENS` - Maximum input tokens (default: `200000`)
- `MAX_OUTPUT_TOKENS` - Maximum output tokens (default: `200000`)
- `TIMEOUT` - Request timeout in seconds (default: `120`)
- `DEBUG` - Enable debug mode (default: `false`)

#### Admin Authentication
- `ADMIN_USERNAME` - Admin panel username (default: `admin`)
- `ADMIN_PASSWORD` - Admin panel password (default: `changeme`)

⚠️ **Security**: Always change the default admin credentials in production!

### Persistent Data

The container stores the SQLite database in `/app/data`. Mount this as a volume to persist user and API key data:

```bash
-v $(pwd)/data:/app/data
```

Or in docker-compose.yml:
```yaml
volumes:
  - ./data:/app/data
```

## Production Deployment

### Using docker-compose.yml

1. **Edit environment variables** in `docker-compose.yml` or create `.env` file:
   ```bash
   # .env file
   OPENAI_BASE_URL=https://your-backend-api.com/v1/chat/completions
   OPENAI_API_KEY=your-secret-api-key
   OPENAI_MODEL=gpt-4
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-very-secure-password-here
   ```

2. **Deploy**:
   ```bash
   docker-compose up -d
   ```

### Behind a Reverse Proxy (Nginx/Traefik)

#### Nginx Example

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # For WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### Traefik Example

```yaml
services:
  infiniproxy:
    build: .
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.infiniproxy.rule=Host(`api.example.com`)"
      - "traefik.http.routers.infiniproxy.entrypoints=websecure"
      - "traefik.http.routers.infiniproxy.tls.certresolver=letsencrypt"
      - "traefik.http.services.infiniproxy.loadbalancer.server.port=8000"
```

## Health Checks

The container includes built-in health checks:

```bash
# Check container health
docker ps

# Manual health check
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "pid": 1,
  "openai_backend": "https://api.openai.com/v1/chat/completions",
  "openai_model": "gpt-4"
}
```

## Monitoring

### View Logs

```bash
# Docker Compose
docker-compose logs -f

# Docker CLI
docker logs -f infiniproxy
```

### Resource Usage

```bash
# Docker Compose
docker-compose stats

# Docker CLI
docker stats infiniproxy
```

## Backup and Restore

### Backup Database

```bash
# Copy database file from container
docker cp infiniproxy:/app/data/proxy_users.db ./backup_$(date +%Y%m%d).db

# Or if using volume mount
cp ./data/proxy_users.db ./backup_$(date +%Y%m%d).db
```

### Restore Database

```bash
# Stop container
docker-compose down

# Restore database file
cp ./backup_20241021.db ./data/proxy_users.db

# Start container
docker-compose up -d
```

## Troubleshooting

### Container Won't Start

Check logs:
```bash
docker-compose logs infiniproxy
```

Common issues:
- Missing required environment variables (`OPENAI_API_KEY`)
- Port 8000 already in use
- Permissions on data directory

### Database Issues

Reset database (⚠️ **This deletes all users and API keys**):
```bash
docker-compose down
rm ./data/proxy_users.db
docker-compose up -d
```

### Health Check Failing

```bash
# Check if service is responding
curl http://localhost:8000/health

# Check container logs
docker-compose logs infiniproxy
```

## Scaling

### Multiple Instances

For high availability, run multiple instances behind a load balancer:

```yaml
version: '3.8'
services:
  infiniproxy:
    build: .
    deploy:
      replicas: 3
    # ... rest of configuration
```

Note: All instances should share the same database volume or use an external database.

## Security Best Practices

1. **Change default credentials** immediately
2. **Use strong passwords** for admin account
3. **Keep API keys secret** - use environment variables, not hardcoded
4. **Use HTTPS** in production (reverse proxy with SSL/TLS)
5. **Regular backups** of the database
6. **Update regularly** - pull latest image for security updates
7. **Firewall** - restrict access to port 8000 if using reverse proxy

## Updating

### Pull Latest Changes

```bash
git pull origin main
docker-compose build
docker-compose up -d
```

### Check for Updates

```bash
docker-compose pull
docker-compose up -d
```

## Support

For issues and questions:
- Check logs: `docker-compose logs`
- Review health endpoint: `curl http://localhost:8000/health`
- Open an issue on the repository
