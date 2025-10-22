#!/bin/bash
set -e

echo "🚀 Deploying InfiniProxy to K8s cluster..."

# Check if kubectl is connected
if ! kubectl get ns weixu &>/dev/null; then
    echo "❌ Error: Cannot connect to K8s cluster or namespace 'weixu' doesn't exist"
    echo "Make sure SSH tunnel is running:"
    echo "  ssh -i ~/.ssh/iiis_ai -N -L 6444:api.ai.iiis.co:6443 ailab@js.ai.iiis.co -p 9022"
    exit 1
fi

echo "✅ Connected to K8s cluster"

# Apply secrets
echo "📦 Creating secrets..."
kubectl apply -f secrets.yaml

# Apply ConfigMap
echo "⚙️  Creating ConfigMap..."
kubectl apply -f deployment.yaml

# Apply Deployment and Service
echo "🚀 Deploying application..."
kubectl apply -f deployment.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/infiniproxy -n weixu

# Apply cert-manager ClusterIssuer (if not exists)
echo "🔐 Setting up cert-manager issuer..."
if ! kubectl get clusterissuer letsencrypt-dns-cloudflare &>/dev/null; then
    kubectl apply -f cert-issuer.yaml
else
    echo "  ℹ️  ClusterIssuer already exists"
fi

# Apply Ingress
echo "🌐 Creating Ingress..."
kubectl apply -f ingress.yaml

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Status:"
kubectl get pods -n weixu -l app=infiniproxy
echo ""
kubectl get svc -n weixu infiniproxy
echo ""
kubectl get ingress -n weixu infiniproxy
echo ""
echo "🔍 Check certificate status:"
echo "  kubectl get certificate -n weixu infiniproxy-tls"
echo ""
echo "📝 View logs:"
echo "  kubectl logs -n weixu -l app=infiniproxy -f"
echo ""
echo "🌐 Access:"
echo "  https://aiapi.iiis.co:9443"
echo ""
