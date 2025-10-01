# Configuration Examples

This directory contains example configurations for common deployment scenarios.

## Quick Reference

| Example | Description | Use Case |
|---------|-------------|----------|
| [minimal.yaml](minimal.yaml) | Minimal configuration | Getting started, testing |
| [production-aws.yaml](production-aws.yaml) | Production AWS EKS setup | Production AWS deployments |
| [production-azure.yaml](production-azure.yaml) | Production Azure AKS setup | Production Azure deployments |
| [development.yaml](development.yaml) | Development environment | Dev/staging environments |
| [external-prometheus.yaml](external-prometheus.yaml) | Using existing Prometheus | Integration with existing monitoring |
| [datadog-integration.yaml](datadog-integration.yaml) | Datadog monitoring | Datadog users |
| [high-availability.yaml](high-availability.yaml) | HA configuration | Mission-critical workloads |
| [resource-constrained.yaml](resource-constrained.yaml) | Low resource usage | Small clusters, cost optimization |

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
- **Monitoring Integration**: Connect to existing monitoring systems
- **Security Settings**: Configure RBAC and secrets