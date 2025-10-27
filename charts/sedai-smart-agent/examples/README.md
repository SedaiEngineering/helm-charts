# Configuration Examples

This directory contains example configurations for common deployment scenarios.

## Quick Reference

| Example | Description | Use Case |
|---------|-------------|----------|
| [minimal.yaml](minimal.yaml) | Minimal configuration with ARM support | Getting started, testing |
| [production-aws.yaml](production-aws.yaml) | Production AWS EKS setup with ARM support | Production AWS deployments |
| [development.yaml](development.yaml) | Development environment with ARM support | Dev/staging environments |
| [external-prometheus.yaml](external-prometheus.yaml) | Using existing Prometheus with ARM support | Integration with existing monitoring |
| [datadog-integration.yaml](datadog-integration.yaml) | Datadog monitoring with ARM support | Datadog users |

## GCP Monitoring Examples

| Example | Description | Use Case |
|---------|-------------|----------|
| [gcp-monitoring-service-account-secret.yaml](gcp-monitoring-service-account-secret.yaml) | GCP monitoring with service account key via secret | Production GCP deployments |
| [gcp-monitoring-service-account-values.yaml](gcp-monitoring-service-account-values.yaml) | GCP monitoring with service account key in values | Development/testing (not recommended for production) |

## Other Examples

| Example | Description | Use Case |
|---------|-------------|----------|
| [priority-class.yaml](priority-class.yaml) | Priority class configuration | Resource-constrained clusters |
| [global-tolerations.yaml](global-tolerations.yaml) | Global tolerations example | Tainted nodes, specialized scheduling |
| [priority-and-tolerations.yaml](priority-and-tolerations.yaml) | Combined priority and tolerations | Enterprise environments |

## Usage

1. Copy the example that best matches your use case
2. Modify the values according to your environment
3. Install using the example:

```bash
helm install sedai-smart-agent . -f examples/production-aws.yaml
```

## Customization

All examples can be combined and customized. Common customizations include:

- **Global Labels/Annotations**: Add organizational metadata
- **Resource Limits**: Adjust based on cluster capacity
- **Node Placement**: Control scheduling with nodeSelector/tolerations
- **ARM Node Support**: Examples include tolerations for ARM64 nodes (AWS Graviton, etc.)
- **Priority Classes**: Configure pod priorities for better scheduling
- **Global Tolerations**: Apply tolerations to all Sedai components
- **Monitoring Integration**: Connect to existing monitoring systems
- **Security Settings**: Configure RBAC and secrets

## ARM Node Support

Most examples include global tolerations for ARM-based nodes (arm64 architecture) to support:
- AWS Graviton instances (m6g, c6g, r6g series)
- Azure ARM-based VMs
- Cost optimization through mixed architecture deployments

```yaml
globalTolerations:
  - key: "kubernetes.io/arch"
    operator: "Equal"
    value: "arm64"
    effect: "NoSchedule"
```

## Priority Class Support

All examples include priority class configurations for better pod scheduling:

```yaml
# Create priority classes first
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: sedai-high-priority
value: 1000
description: "High priority for critical Sedai components"

# Then configure components
smartAgentEnroll:
  priorityClassName: "sedai-high-priority"

workload:
  smartAgent:
    priorityClassName: "sedai-high-priority"
```

Common priority class values:
- **2000+**: System critical (use built-in `system-cluster-critical`)
- **1000-1999**: High priority (critical business components)
- **500-999**: Medium priority (standard components)
- **100-499**: Low priority (development/testing)
- **0-99**: Best effort (background tasks)

## GCP Monitoring Authentication

The Smart Agent supports two authentication methods for GCP monitoring:

### 1. Workload Identity (Default - Recommended for GKE)
```yaml
monitoringProvider:
  gcpMonitoring:
    enabled: true
    projectID: "my-gcp-project"
    # No additional configuration needed - uses workload identity by default
```

### 2. Service Account Key (Alternative Method)

#### Option A: Via Kubernetes Secret (Recommended for Production)
```yaml
monitoringProvider:
  gcpMonitoring:
    enabled: true
    projectID: "my-gcp-project"
    gcpSecret: "gcp-service-account-secret"
    gcpServiceAccountKeySecretKey: "key.json"  # Optional, defaults to "key.json"
```

Create the secret beforehand:
```bash
kubectl create secret generic gcp-service-account-secret \
  --from-file=key.json=path/to/service-account-key.json \
  --namespace=sedai-smart-agent
```

#### Option B: Direct in Values (NOT Recommended for Production)
```yaml
monitoringProvider:
  gcpMonitoring:
    enabled: true
    projectID: "my-gcp-project"
    serviceAccountKeyJson: |
      {
        "type": "service_account",
        "project_id": "...",
        ...
      }
```

**Authentication Priority:**
1. If `GCP_SERVICE_ACCOUNT_KEY_JSON` environment variable is set (from secret or values), use service account key
2. Otherwise, use workload identity (default behavior)

This maintains backward compatibility - existing workload identity setups continue to work unchanged.