# InfiniProxy Kubernetes Deployment

## Deployment Status: ✅ COMPLETE

### 🎯 Production Endpoints
- **HTTPS URL**: https://aiapi.iiis.co:9443
- **Health Check**: https://aiapi.iiis.co:9443/health
- **Admin Panel**: https://aiapi.iiis.co:9443/admin
- **API Endpoint**: https://aiapi.iiis.co:9443/v1/chat/completions

### 📦 Container Image
- **Registry**: harbor.ai.iiis.co:9443
- **Image**: xuw/infiniproxy:latest
- **Architecture**: linux/amd64
- **Size**: ~208MB

### ☸️ Kubernetes Resources
**Namespace**: weixu

**Deployment**:
- Name: infiniproxy
- Replicas: 1
- Status: Running
- Pod: infiniproxy-59ccb44845-hld46

**Service**:
- Name: infiniproxy
- Type: ClusterIP
- Port: 8000
- IP: 10.233.55.247

**Ingress**:
- Name: infiniproxy
- Class: nginx
- Host: aiapi.iiis.co
- TLS: ✅ Let's Encrypt (letsencrypt-prod)
- Certificate: infiniproxy-tls (READY)

### 💾 Persistent Storage
- **Database**: pvc-nfshome-weixu → /app/data
- **Logs**: gfs-sata-pvc-weixu → /app/logs
- **Temp**: pvc-rancher-localpath-1-weixu-weixu-claude-claude-qassum9i → /tmp

### 🔐 TLS Certificate
- **Issuer**: letsencrypt-prod (ACME)
- **Status**: ✅ READY
- **Secret**: infiniproxy-tls
- **Valid for**: aiapi.iiis.co

### 🏗️ Cluster Access
**SSH Tunnel**:
```bash
ssh -i ~/.ssh/iiis_ai -N -L 6444:api.ai.iiis.co:6443 ailab@js.ai.iiis.co -p 9022
```

**Kubectl Config**:
```bash
kubectl --kubeconfig=/dev/null --server=https://localhost:6444 --insecure-skip-tls-verify
```

### 📊 Resource Limits
**Requests**:
- CPU: 250m
- Memory: 256Mi

**Limits**:
- CPU: 1000m (1 core)
- Memory: 1Gi

### 🔍 Health Checks
**Liveness Probe**:
- Path: /health
- Port: 8000
- Initial Delay: 30s

**Readiness Probe**:
- Path: /health
- Port: 8000
- Initial Delay: 10s

### 🚀 Deployment Commands

**View Pod Status**:
```bash
kubectl get pods -n weixu -l app=infiniproxy
```

**View Logs**:
```bash
kubectl logs -n weixu -l app=infiniproxy -f
```

**Check Ingress**:
```bash
kubectl get ingress -n weixu infiniproxy
```

**Check Certificate**:
```bash
kubectl get certificate -n weixu infiniproxy-tls
```

**Restart Pod**:
```bash
kubectl delete pod -n weixu -l app=infiniproxy
```

**Update Image**:
```bash
# 1. Build and push new image
docker buildx build --platform linux/amd64 --push -t harbor.ai.iiis.co:9443/xuw/infiniproxy:latest .

# 2. Restart pod to pull new image
kubectl delete pod -n weixu -l app=infiniproxy
```

### 📝 Environment Variables
Configured via ConfigMap and Secrets:
- PROXY_HOST: 0.0.0.0
- OPENAI_BASE_URL: (from secret)
- OPENAI_API_KEY: (from secret)
- ADMIN_USERNAME: (from secret)
- ADMIN_PASSWORD: (from secret)

### 🧪 Testing the Deployment

**Test Health Endpoint**:
```bash
curl -sk https://aiapi.iiis.co:9443/health
```

**Test API Endpoint**:
```bash
curl -sk https://aiapi.iiis.co:9443/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

**Test Admin Panel**:
Open in browser: https://aiapi.iiis.co:9443/admin

### 📁 Files
- `k8s/deployment.yaml` - Deployment, Service, ConfigMap
- `k8s/secrets.yaml` - Secrets (base64 encoded)
- `k8s/ingress.yaml` - Ingress with TLS
- `Dockerfile` - Container image definition
- `docker-compose.yml` - Local development

### ✅ Deployment Checklist
- [x] Build AMD64 Docker image
- [x] Push to Harbor registry
- [x] Create K8s deployment manifests
- [x] Apply deployment to weixu namespace
- [x] Create ingress with TLS
- [x] Configure cert-manager certificate (letsencrypt-prod)
- [x] Verify TLS certificate is READY
- [x] Pod running successfully
- [x] Service accessible
- [x] Ingress configured with proper hostname

### 🎉 Deployment Complete!

The InfiniProxy service is now live at https://aiapi.iiis.co:9443

Access the admin panel to:
- Create API keys
- Manage users
- View usage statistics
- Monitor proxy health
