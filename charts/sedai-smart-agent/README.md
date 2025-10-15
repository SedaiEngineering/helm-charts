# Sedai Smart Agent Helm Chart

The Sedai Smart Agent Helm Chart deploys the complete Sedai platform components for Kubernetes cluster monitoring, optimization, and autonomous operations.

## Quick Start

```bash
# Add the Sedai Helm repository (if available)
helm repo add sedai https://sedaiengineering.github.io/helm-charts/
helm repo update

# Install with minimal configuration
helm install sedai-smart-agent sedai/sedai-smart-agent \
  --set sedaiIntegrationSettings.clusterName="my-cluster" \
  --set sedaiIntegrationSettings.sedaiApiToken="your-api-token"
```

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Cluster admin permissions for RBAC setup
- Valid Sedai API token

## Configuration

### Required Configuration

The following values must be configured for the chart to work:

```yaml
sedaiIntegrationSettings:
  clusterName: "my-production-cluster"     # Unique name for your cluster
  sedaiApiToken: "your-api-token"         # Your Sedai API token
  sedaiBaseUrl: "https://app.sedai.io"    # Sedai platform URL
```

### Basic Installation

Create a `values.yaml` file with your configuration:

```yaml
# Basic configuration
sedaiIntegrationSettings:
  nickName: "Production EKS Cluster"
  clusterName: "prod-eks-us-west-2"
  clusterProvider: "AWS"  # AWS, AZURE, GCP, SELF_MANAGED
  sedaiBaseUrl: "https://app.sedai.io"
  sedaiApiToken: "your-api-token-here"

# Enable components as needed
sedaiPrometheus:
  enabled: true

sedaiKSM:
  enabled: true
```

Install the chart:

```bash
helm install sedai-smart-agent . -f values.yaml
```

## Component Configuration

### Smart Agent (Core Component)

The Smart Agent is always enabled and connects your cluster to Sedai:

```yaml
workload:
  smartAgent:
    replicaCount: 1
    nodeSelector: {}
    tolerations: []

resources:
  smartAgent:
    cpu:
      requests: "500m"
      limits: "500m"
    memory:
      requests: "1024Mi"
      limits: "1024Mi"
```

### Monitoring Components

#### Sedai-Managed Prometheus

```yaml
sedaiPrometheus:
  enabled: true
  server:
    retention: '6h'  # Metric retention period
  nodeSelector: {}
  tolerations: []

resources:
  prometheus:
    cpu:
      requests: "1000m"
      limits: "1000m"
    memory:
      requests: "4096Mi"
      limits: "4096Mi"
    storage: "60Gi"
```

#### Kube State Metrics

```yaml
sedaiKSM:
  enabled: true
  nodeSelector: {}
  tolerations: []
```

#### Node Exporter

```yaml
sedaiNodeExporter:
  enabled: true
  nodeSelector: {}
  tolerations: []
```

#### Victoria Metrics (Alternative to Prometheus)

```yaml
sedaiVictoriaMetrics:
  enabled: true
  retentionPeriod: "1d"
  nodeSelector: {}
  tolerations: []

resources:
  victoriaMetrics:
    storage: "30Gi"
```

### Optimization Components

#### Sedai Sync (Auto-Optimization)

```yaml
sedaiSync:
  enabled: true
  logLevel: "error"  # trace, debug, info, warn, error
  nodeSelector: {}
  tolerations: []
```

#### Application Performance Monitoring

```yaml
# Beyla for eBPF-based monitoring
sedaiBeyla:
  enabled: true
  nodeSelector: {}
  tolerations: []

# Grafana Alloy for telemetry collection
sedaiGrafanaAlloy:
  enabled: true
  nodeSelector: {}
  tolerations: []
```

## Global Labels and Annotations

Apply consistent metadata across all resources:

```yaml
# Global labels applied to all resources
globalLabels:
  environment: production
  team: platform
  cost-center: engineering
  project: sedai-monitoring

# Global annotations applied to all resources
globalAnnotations:
  company.io/owner: platform-team
  company.io/project: sedai-smart-agent
  compliance.io/required: "true"
  backup.io/enabled: "true"
```

## External Monitoring Integration

### Using Existing Prometheus

```yaml
monitoringProvider:
  prometheus:
    enabled: true
    serverUrl: "http://prometheus-server.monitoring.svc.cluster.local"
    credentialsProvider: "BASIC_AUTH"  # BASIC_AUTH, FEDERATEDPROMETHEUS_JWT, NO_AUTH
    prometheusUsername: "admin"
    prometheusPassword: "password"
```

### Using Datadog

```yaml
monitoringProvider:
  datadog:
    enabled: true
    datadogEndpoint: "https://api.datadoghq.com"
    datadogApiKey: "your-api-key"
    datadogApplicationKey: "your-app-key"
    datadogEnvDimensions: "env:production"
```

### Using Amazon Managed Prometheus (AMP)

```yaml
monitoringProvider:
  amp:
    enabled: true
    amp_query_endpoint: "https://aps-workspaces.us-west-2.amazonaws.com/workspaces/ws-xxx/api/v1/query"
    amp_iam_role: "arn:aws:iam::123456789012:role/SedaiAMPRole"
```

## Network Configuration

### Proxy Settings

For clusters behind corporate proxies:

```yaml
proxySettings:
  enabled: true
  proxyHost: "proxy.company.com"
  proxyPort: 3128
  proxyUsername: "proxy-user"
  proxyPassword: "proxy-password"
```

### Image Pull Secrets

For private registries:

```yaml
imagePullSecret:
  enabled: true
  secretName: "sedai-registry-secret"
```

## Advanced Configuration

### Resource Limits and Requests

Customize resource allocation for each component:

```yaml
resources:
  smartAgent:
    cpu:
      requests: "500m"
      limits: "1000m"
    memory:
      requests: "1024Mi"
      limits: "2048Mi"
  
  prometheus:
    cpu:
      requests: "2000m"
      limits: "4000m"
    memory:
      requests: "8192Mi"
      limits: "16384Mi"
    storage: "100Gi"
```

### Node Placement

Control where components are scheduled:

```yaml
workload:
  smartAgent:
    nodeSelector:
      node-type: monitoring
    tolerations:
    - key: "monitoring"
      operator: "Equal"
      value: "true"
      effect: "NoSchedule"
```

### Debug Logging

Enable detailed logging for troubleshooting:

```yaml
enableAgentDebugLogs:
  enabled: true
  agentLogLevel: "DEBUG"
```

## Security Configuration

### RBAC Settings

```yaml
sedaiIntegrationSettings:
  rbacReadOnly: false  # Set to true for read-only Datapilot mode
```

### Using Kubernetes Secrets

Store sensitive data in Kubernetes secrets:

```yaml
sedaiIntegrationSettings:
  sedaiApiTokenSecret: "sedai-api-secret"
  sedaiApiTokenSecretKey: "api-token"
```

Create the secret:

```bash
kubectl create secret generic sedai-api-secret \
  --from-literal=api-token="your-api-token"
```

## Installation Examples

### Production AWS EKS Cluster

```yaml
# values-production.yaml
namespace: sedai-smart-agent

globalLabels:
  environment: production
  cluster: eks-prod-us-west-2

globalAnnotations:
  company.io/owner: platform-team
  compliance.io/required: "true"

sedaiIntegrationSettings:
  nickName: "Production EKS Cluster"
  clusterName: "eks-prod-us-west-2"
  clusterProvider: "AWS"
  sedaiBaseUrl: "https://app.sedai.io"
  sedaiApiTokenSecret: "sedai-api-secret"
  sedaiApiTokenSecretKey: "api-token"

# Enable full monitoring stack
sedaiPrometheus:
  enabled: true
  server:
    retention: '24h'

sedaiKSM:
  enabled: true

sedaiNodeExporter:
  enabled: true

sedaiSync:
  enabled: true

# Resource allocation for production
resources:
  smartAgent:
    cpu:
      requests: "1000m"
      limits: "2000m"
    memory:
      requests: "2048Mi"
      limits: "4096Mi"
  
  prometheus:
    cpu:
      requests: "2000m"
      limits: "4000m"
    memory:
      requests: "8192Mi"
      limits: "16384Mi"
    storage: "200Gi"
```

### Development Cluster with External Prometheus

```yaml
# values-dev.yaml
globalLabels:
  environment: development

sedaiIntegrationSettings:
  clusterName: "dev-cluster"
  sedaiApiToken: "dev-api-token"

# Use existing Prometheus
monitoringProvider:
  prometheus:
    enabled: true
    serverUrl: "http://prometheus-server.monitoring.svc.cluster.local"
    credentialsProvider: "NO_AUTH"

# Minimal resource allocation
resources:
  smartAgent:
    cpu:
      requests: "200m"
      limits: "500m"
    memory:
      requests: "512Mi"
      limits: "1024Mi"
```

## Upgrading

### Upgrade the Chart

```bash
# Update repository
helm repo update

# Upgrade with new values
helm upgrade sedai-smart-agent sedai/sedai-smart-agent -f values.yaml
```

### Migration Notes

When upgrading between major versions, check the [CHANGELOG.md](CHANGELOG.md) for breaking changes.

## Troubleshooting

### Common Issues

1. **Agent not connecting to Sedai**
   - Verify API token is correct
   - Check network connectivity and proxy settings
   - Review agent logs: `kubectl logs -l app.kubernetes.io/name=sedai-smart-agent`

2. **Prometheus not scraping metrics**
   - Ensure KSM is enabled if using Sedai-managed Prometheus
   - Check Prometheus configuration and targets

3. **Resource constraints**
   - Monitor resource usage and adjust limits
   - Check node capacity and scheduling constraints

### Debug Commands

```bash
# Check agent status
kubectl get pods -l app.kubernetes.io/name=sedai-smart-agent

# View agent logs
kubectl logs -l app.kubernetes.io/name=sedai-smart-agent -f

# Check Prometheus targets (if enabled)
kubectl port-forward svc/sedai-prometheus-server-service 9090:80
# Visit http://localhost:9090/targets

# Validate configuration
helm template . -f values.yaml --debug
```

## Support

- Documentation: [https://docs.sedai.io](https://docs.sedai.io)
- Support: [support@sedai.io](mailto:support@sedai.io)
