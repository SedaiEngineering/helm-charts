# Configuration Guide

This guide explains how to configure the Sedai Smart Agent Helm chart for different environments and use cases.

## Table of Contents

- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Component Overview](#component-overview)
- [Configuration Sections](#configuration-sections)
- [Common Patterns](#common-patterns)
- [Best Practices](#best-practices)

## Quick Start

### Minimal Setup

The absolute minimum configuration requires only:

```yaml
sedaiIntegrationSettings:
  clusterName: "my-cluster"
  sedaiApiToken: "your-api-token"
```

### Recommended Setup

For production use, we recommend:

```yaml
# Global metadata for all resources
globalLabels:
  environment: production
  team: platform

globalAnnotations:
  company.io/owner: platform-team
  compliance.io/required: "true"

# Sedai integration
sedaiIntegrationSettings:
  nickName: "Production Cluster"
  clusterName: "prod-cluster"
  clusterProvider: "AWS"
  sedaiApiTokenSecret: "sedai-secret"  # Use secrets for production
  sedaiApiTokenSecretKey: "api-token"

# Enable monitoring
sedaiPrometheus:
  enabled: true

sedaiKSM:
  enabled: true

# Enable optimization
sedaiSync:
  enabled: true
```

## Core Concepts

### Components

The Sedai Smart Agent consists of several components:

1. **Smart Agent** (Required): Core component that connects to Sedai platform
2. **Monitoring Stack**: Collects metrics from your cluster
3. **Optimization Engine**: Enables autonomous optimization
4. **Performance Monitoring**: Provides application-level insights

### Deployment Modes

- **Minimal**: Only Smart Agent for basic connectivity
- **Monitoring**: Smart Agent + monitoring components
- **Full**: All components for complete autonomous operations

### Integration Patterns

- **Sedai-Managed**: Use Sedai's monitoring stack
- **External Integration**: Connect to existing monitoring systems
- **Hybrid**: Mix of Sedai and external components

## Component Overview

### Smart Agent (Always Enabled)

The core component that connects your cluster to Sedai:

```yaml
workload:
  smartAgent:
    name: sedai-smart-agent
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

#### Sedai Prometheus

Sedai-managed Prometheus for metric collection:

```yaml
sedaiPrometheus:
  enabled: true
  server:
    retention: '6h'  # Adjust based on needs
  nodeSelector: {}
  tolerations: []
```

#### Kube State Metrics (KSM)

Provides Kubernetes object metrics:

```yaml
sedaiKSM:
  enabled: true  # Required for Sedai-managed Prometheus
  nodeSelector: {}
  tolerations: []
```

#### Node Exporter

Collects node-level metrics:

```yaml
sedaiNodeExporter:
  enabled: true
  nodeSelector: {}
  tolerations: []
```

#### Victoria Metrics

Alternative to Prometheus with better performance:

```yaml
sedaiVictoriaMetrics:
  enabled: true
  retentionPeriod: "1d"
  nodeSelector: {}
  tolerations: []
```

### Optimization Components

#### Sedai Sync

Enables autonomous optimization:

```yaml
sedaiSync:
  enabled: true
  logLevel: "error"  # trace, debug, info, warn, error
  nodeSelector: {}
  tolerations: []
```

#### Application Performance Monitoring

```yaml
# eBPF-based monitoring
sedaiBeyla:
  enabled: true
  nodeSelector: {}
  tolerations: []

# Telemetry collection
sedaiGrafanaAlloy:
  enabled: true
  nodeSelector: {}
  tolerations: []
```

## Configuration Sections

### Global Metadata

Apply consistent labels and annotations to all resources:

```yaml
globalLabels:
  environment: production
  team: platform
  cost-center: engineering
  project: monitoring

globalAnnotations:
  company.io/owner: platform-team
  compliance.io/required: "true"
  backup.io/enabled: "true"
```

**Use Cases:**
- OPA Gatekeeper policy compliance
- Resource tracking and billing
- Organizational governance
- Automated tooling integration

### Sedai Integration

Core platform connection settings:

```yaml
sedaiIntegrationSettings:
  nickName: "Human-readable cluster name"
  clusterName: "unique-cluster-identifier"
  clusterProvider: "AWS"  # AWS, AZURE, GCP, SELF_MANAGED
  sedaiBaseUrl: "https://app.sedai.io"
  
  # Option 1: Direct token (not recommended for production)
  sedaiApiToken: "your-api-token"
  
  # Option 2: Kubernetes secret (recommended)
  sedaiApiTokenSecret: "sedai-secret"
  sedaiApiTokenSecretKey: "api-token"
  
  # RBAC settings
  rbacReadOnly: false  # true for read-only mode
  
  # Advanced options
  forceCreate: false
  enableDeRegisterJob: false
```

### Resource Management

Control resource allocation for each component:

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
      requests: "1000m"
      limits: "2000m"
    memory:
      requests: "4096Mi"
      limits: "8192Mi"
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

### External Monitoring

Connect to existing monitoring systems:

```yaml
monitoringProvider:
  # Existing Prometheus
  prometheus:
    enabled: true
    serverUrl: "http://prometheus-server.monitoring.svc.cluster.local"
    credentialsProvider: "BASIC_AUTH"
    prometheusUsername: "admin"
    prometheusPassword: "password"
  
  # Datadog
  datadog:
    enabled: true
    datadogEndpoint: "https://api.datadoghq.com"
    datadogApiKey: "your-api-key"
    datadogApplicationKey: "your-app-key"
  
  # Amazon Managed Prometheus
  amp:
    enabled: true
    amp_query_endpoint: "https://aps-workspaces.region.amazonaws.com/workspaces/ws-xxx/api/v1/query"
    amp_iam_role: "arn:aws:iam::account:role/SedaiAMPRole"
```

### Network Configuration

Configure proxy and image pull settings:

```yaml
# Corporate proxy
proxySettings:
  enabled: true
  proxyHost: "proxy.company.com"
  proxyPort: 3128
  proxyUsername: "user"
  proxyPassword: "password"

# Private registry
imagePullSecret:
  enabled: true
  secretName: "registry-secret"
```

## Common Patterns

### Environment-Specific Configurations

#### Production
- Use Kubernetes secrets for sensitive data
- Enable comprehensive monitoring
- Set appropriate resource limits
- Configure node placement
- Enable optimization features

#### Development
- Use direct configuration for simplicity
- Reduce resource allocation
- Enable debug logging
- Shorter retention periods

#### Staging
- Mirror production configuration
- Reduced resource allocation
- Enable all features for testing

### Monitoring Strategies

#### Sedai-Managed Stack
```yaml
sedaiPrometheus:
  enabled: true
sedaiKSM:
  enabled: true
sedaiNodeExporter:
  enabled: true
```

#### External Integration
```yaml
sedaiPrometheus:
  enabled: false
monitoringProvider:
  prometheus:
    enabled: true
    serverUrl: "http://existing-prometheus"
```

#### Hybrid Approach
```yaml
sedaiPrometheus:
  enabled: true  # For Sedai-specific metrics
monitoringProvider:
  datadog:
    enabled: true  # For application metrics
```

### Resource Sizing

#### Small Clusters (< 50 nodes)
```yaml
resources:
  smartAgent:
    cpu: { requests: "200m", limits: "500m" }
    memory: { requests: "512Mi", limits: "1024Mi" }
  prometheus:
    cpu: { requests: "500m", limits: "1000m" }
    memory: { requests: "2048Mi", limits: "4096Mi" }
    storage: "20Gi"
```

#### Medium Clusters (50-200 nodes)
```yaml
resources:
  smartAgent:
    cpu: { requests: "500m", limits: "1000m" }
    memory: { requests: "1024Mi", limits: "2048Mi" }
  prometheus:
    cpu: { requests: "1000m", limits: "2000m" }
    memory: { requests: "4096Mi", limits: "8192Mi" }
    storage: "100Gi"
```

#### Large Clusters (200+ nodes)
```yaml
resources:
  smartAgent:
    cpu: { requests: "1000m", limits: "2000m" }
    memory: { requests: "2048Mi", limits: "4096Mi" }
  prometheus:
    cpu: { requests: "2000m", limits: "4000m" }
    memory: { requests: "8192Mi", limits: "16384Mi" }
    storage: "500Gi"
```

## Best Practices

### Security

1. **Use Kubernetes Secrets** for sensitive data:
   ```bash
   kubectl create secret generic sedai-secret \
     --from-literal=api-token="your-token"
   ```

2. **Configure RBAC** appropriately:
   ```yaml
   sedaiIntegrationSettings:
     rbacReadOnly: true  # For read-only access
   ```

3. **Use least privilege** node selectors and tolerations

### Performance

1. **Size resources** based on cluster size and workload
2. **Use node selectors** to place monitoring components on dedicated nodes
3. **Configure retention** based on storage capacity and requirements
4. **Monitor resource usage** and adjust limits accordingly

### Reliability

1. **Set appropriate resource limits** to prevent resource starvation
2. **Configure tolerations** for critical components
3. **Use multiple replicas** for high availability (where supported)
4. **Monitor component health** and set up alerting

### Cost Optimization

1. **Disable unused components** to reduce resource consumption
2. **Adjust retention periods** based on actual needs
3. **Use external monitoring** if already available
4. **Size resources** appropriately for your cluster

### Maintenance

1. **Use version pinning** for production deployments
2. **Test upgrades** in non-production environments first
3. **Monitor logs** for errors and warnings
4. **Keep configurations** in version control
5. **Document customizations** and rationale

## Troubleshooting

### Common Issues

1. **Connection Issues**
   - Verify API token and base URL
   - Check network connectivity and proxy settings
   - Review firewall rules

2. **Resource Issues**
   - Monitor resource usage with `kubectl top`
   - Check for resource constraints in events
   - Adjust limits based on actual usage

3. **Monitoring Issues**
   - Verify Prometheus targets are healthy
   - Check KSM deployment if using Sedai-managed Prometheus
   - Validate external monitoring connectivity

### Debug Commands

```bash
# Check component status
kubectl get pods -n sedai-smart-agent

# View logs
kubectl logs -l app.kubernetes.io/name=sedai-smart-agent -f

# Check resource usage
kubectl top pods -n sedai-smart-agent

# Validate configuration
helm template . -f values.yaml --debug

# Test connectivity
kubectl exec -it deployment/sedai-smart-agent -- curl -I https://app.sedai.io
```