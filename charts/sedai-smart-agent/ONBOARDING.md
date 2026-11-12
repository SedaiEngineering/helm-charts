# Sedai Kubernetes Cluster Integration

Smart Agent Installation Instructions - Self Provisioning Workflow

This document provides step-by-step instructions for integrating Kubernetes with Sedai using our self-provisioning workflow. Instead of manually logging into the Sedai UI and following the standard integration process, users can deploy the Sedai Smart Agent directly into their Kubernetes cluster using an API key and our reusable Helm chart.

A custom job is included to automatically create the Kubernetes integration in Sedai and generate the necessary secret credentials within the cluster. This streamlined approach enables faster onboarding and simplifies integrating Sedai as a Kubernetes cluster add-on in your Infrastructure-as-Code (IaC) templates.

## Table of Contents

- [Sedai Smart Agent - Deployment Overview](#sedai-smart-agent---deployment-overview)
- [Sedai Smart Agent - Deployment Steps](#sedai-smart-agent---deployment-steps)
- [Sedai Smart Agent - Helm Chart](#sedai-smart-agent---helm-chart)
- [Sedai Smart Agent - Container Images](#sedai-smart-agent---container-images)
- [Sedai Smart Agent - FAQ](#sedai-smart-agent---faq)
- [Sedai Smart Agent - Help](#sedai-smart-agent---help)

## Sedai Smart Agent - Deployment Overview

This Helm chart deployment includes both the Smart Agent and the SmartAgentEnroll job.

### Sedai Smart Agent

The Smart Agent is a deployment that runs within your Kubernetes cluster, enabling secure and continuous integration with the Sedai platform. It discovers cluster resources, synchronizes metrics, and executes optimization and discovery tasks received from Sedai using the appropriate RBAC permissions.

### Sedai Pod Interceptor

The Sedai Pod Interceptor is a Kubernetes mutating admission webhook that runs inside your cluster. It applies Sedai's optimizations — CPU and memory, and optionally replica count and autoscaler bounds — at the moment Kubernetes admits an object, rather than by editing objects after the fact.

The key property is that Sedai never writes optimized values into your Deployment manifests. Your Git repository stays the source of truth for everything you have written down. Sedai supplies only the values that could not be known when the manifest was authored.

This is enabled by toggling `sedaiPodInterceptor.enabled` to `true`. We strongly recommend that this feature be enabled.

Since the Pod Interceptor (and its Postgres store) are single-replica by design, they're also protected from being evicted by Karpenter's node consolidation/expiration — see [Karpenter Disruption Protection](#karpenter-disruption-protection) below.

### Sedai Smart Scheduler

The Sedai Smart Scheduler helps scheduling and compacting the clusters based on the resource requirements of the workloads as well as the configuration of the nodes / nodepools.

This is enabled by toggling `sedaiSmartScheduler.enabled` and `sedaiSmartScheduler.compactor.enabled` to `true`. We strongly recommend that this feature be enabled.

The Smart Scheduler requires the Pod Interceptor. When the Smart Scheduler is enabled, the chart also deploys the Pod Interceptor, even if `sedaiPodInterceptor.enabled` is `false`.

### SmartAgentEnroll job

The SmartAgentEnroll job automates the onboarding process and establishes the initial secure connection with the Sedai API Server. It performs the following actions:

- Authenticates with the Sedai API Server using the provided API key.
- Registers the Kubernetes cluster as an integration within Sedai, making it available for Sedai to manage.
- Provisions Smart Agent–specific credentials, securely storing them in a Kubernetes Secret.

The Smart Agent then consumes this secret to enable authenticated and continuous communication with Sedai.

#### Workflow

1. **Authentication:** Establishes secure access to the Sedai API Server using the provided credentials.
2. **Integration Registration:** Registers the Kubernetes cluster with Sedai, including cluster-specific details.
3. **Monitoring Configuration:** Configures the monitoring provider within Sedai.
4. **Credential Retrieval:** Securely retrieves integration-specific credentials from Sedai.
5. **Secret Creation:** Creates a Kubernetes Secret containing the Smart Agent credentials and connection details.
6. **Smart Agent Initialization:** The Smart Agent starts only after successfully retrieving the credentials, enabling secure and continuous communication between the cluster and the Sedai platform.

## Sedai Smart Agent - Deployment Steps

### 1. Generate Sedai API Key

The SmartAgentEnroll job authenticates with the Sedai API Server and automates the onboarding of your Kubernetes cluster to Sedai. You can generate an API Key directly from the Sedai Dashboard, or our team can provide one for you upon request. This API Key can be reused across multiple cluster onboarding processes for seamless integration with Sedai.

Login to the Sedai Dashboard:
- Go to **Settings**
- Select **API Keys**
- Click **Create New Key**

Enter the key details and click **Generate**.

### 2. Download Helm Chart from our official repository

Please pull the latest Helm chart from our repository (repository details are shared below).

Review the `values.yaml` file carefully and prepare your cluster-specific configurations and details before proceeding with the deployment.

### 3. Create custom-values file

You can deploy this Helm chart across all Kubernetes clusters. Please use a cluster-specific custom values file to override the default settings. Below is an example snippet of some settings you may need to modify. For additional details, check the [FAQ](#sedai-smart-agent---faq) section in this document.

In your override file, make sure to explicitly enable the **Pod Interceptor** (`sedaiPodInterceptor.enabled: true`) and the **Smart Scheduler** (`sedaiSmartScheduler.enabled: true` and `sedaiSmartScheduler.compactor.enabled: true`) — both are off by default; we strongly recommend enabling Pod Interceptor for every cluster (see [Deployment Overview](#sedai-smart-agent---deployment-overview) above for what each does). All four sample files below already turn them on.

#### Sample values-override.yaml - EKS Cluster with Prometheus Monitoring Provider

```yaml
globalRegistry: "public.ecr.aws"

smartAgentEnroll:
  enabled: true
sedaiPodInterceptor:
  enabled: true
sedaiSmartScheduler:
  enabled: true
  compactor:
    enabled: true

sedaiIntegrationSettings:
  nickName: "customer-eks-demo-cluster-001"
  clusterName: "customer-eks-demo-cluster-001"
  clusterProvider: "AWS"
  sedaiBaseUrl: "https://tenant.sedai.app"
  sedaiApiToken: "INSERT-SEDAI-API-KEY-HERE"

monitoringProvider:
  prometheus:
    enabled: true
    serverUrl: "http://prometheus-server.prometheus.svc.cluster.local"
```

#### Sample values-override.yaml - AKS Cluster with Prometheus Monitoring Provider

```yaml
globalRegistry: "public.ecr.aws"

smartAgentEnroll:
  enabled: true
sedaiPodInterceptor:
  enabled: true
sedaiSmartScheduler:
  enabled: true
  compactor:
    enabled: true

sedaiIntegrationSettings:
  nickName: "customer-aks-demo-cluster-001"
  clusterName: "customer-aks-demo-cluster-001"
  clusterProvider: "AZURE"
  sedaiBaseUrl: "https://tenant.sedai.app"
  sedaiApiToken: "INSERT-SEDAI-API-KEY-HERE"

monitoringProvider:
  prometheus:
    enabled: true
    serverUrl: "http://prometheus-server.prometheus.svc.cluster.local"
```

#### Sample values-override.yaml - GKE Cluster with Prometheus Monitoring Provider

```yaml
globalRegistry: "public.ecr.aws"

smartAgentEnroll:
  enabled: true
sedaiPodInterceptor:
  enabled: true
sedaiSmartScheduler:
  enabled: true
  compactor:
    enabled: true

sedaiIntegrationSettings:
  nickName: "customer-gke-demo-cluster-001"
  clusterName: "customer-gke-demo-cluster-001"
  clusterProvider: "GCP"
  sedaiBaseUrl: "https://tenant.sedai.app"
  sedaiApiToken: "INSERT-SEDAI-API-KEY-HERE"

monitoringProvider:
  prometheus:
    enabled: true
    serverUrl: "http://prometheus-server.prometheus.svc.cluster.local"
```

#### Sample values-override.yaml - GKE Cluster with Google Cloud Monitoring

```yaml
globalRegistry: "public.ecr.aws"

smartAgentEnroll:
  enabled: true
sedaiPodInterceptor:
  enabled: true
sedaiSmartScheduler:
  enabled: true
  compactor:
    enabled: true

sedaiIntegrationSettings:
  nickName: "customer-gke-demo-cluster-001"
  clusterName: "customer-gke-demo-cluster-001"
  clusterProvider: "GCP"
  sedaiBaseUrl: "https://tenant.sedai.app"
  sedaiApiToken: "INSERT-SEDAI-API-KEY-HERE"

monitoringProvider:
  gcpMonitoring:
    enabled: true
    projectID: GKE-PROJECT-ID
    gcpSecret:                       # Name of the Kubernetes Secret that stores the GCP service account key
    gcpServiceAccountKeySecretKey:   # Secret Key for the service account key
```

To enable any of the listed integrations we can set the respective `enabled` flag of that integration to `true`. For Prometheus & Victoria Metrics it is recommended to set only one of the flags to `true` — for example, using Victoria Metrics instead of Prometheus — simply update your configuration by setting the Victoria Metrics `enabled` flag to `true` and the Prometheus `enabled` flag to `false` or vice versa. Prometheus and VictoriaMetrics are mutually exclusive.

```yaml
sedaiVictoriaMetrics:
  enabled: true
sedaiKSM:
  enabled: true
sedaiNodeExporter:
  enabled: true
sedaiBeyla:
  enabled: true
```

> Sedai recommends VictoriaMetrics — lower memory footprint and better stability under load.

> **Note:** Sedai-managed VictoriaMetrics scrapes Node Exporter and Kube State Metrics. When `sedaiVictoriaMetrics.enabled` is `true`, the chart also deploys both, even if `sedaiNodeExporter.enabled` or `sedaiKSM.enabled` is `false`.

> **Note:** `sedaiPrometheus` and `sedaiVictoriaMetrics` keys are used for monitoring tools that are fully managed and deployed by Sedai. If you prefer to connect your own self-hosted monitoring setup, use the options under `monitoringProvider` instead. Ex: `monitoringProvider.prometheus`

### 4. Additional settings to avoid disruption

Before deploying, review these settings and add whichever apply to your environment — each addresses an issue that otherwise only shows up *after* the cluster is already onboarded.

**DNS resolution — `clusterDomain`**

If a cluster's kubelet/CoreDNS domain configuration is non-standard, the Smart Agent can fail to reach the Pod Interceptor with a `Name does not resolve` error. Set this up front if you know your cluster is affected (see FAQ #14 for the full symptom):

```yaml
clusterDomain: "cluster.local"
```

**Deploying via ArgoCD — `ignoreDifferences`**

If you're deploying via ArgoCD, you **must** include `ignoreDifferences` **and** `syncOptions: [RespectIgnoreDifferences=true]` in your Application manifest — without both, dynamically generated secrets, mutated webhook configuration, and the Smart Scheduler and descheduler (compactor) ConfigMaps that the Smart Agent rewrites at runtime will cause sync loops (or, with `selfHeal` on, get reset back to a fresh value on every sync). This is not optional; see FAQ #13 for the complete block to copy into your Application manifest.

**Deploying via Flux — `driftDetection.ignore`**

If you're deploying via Flux with drift detection turned on (`spec.driftDetection.mode: enabled` in the HelmRelease), you **must** add `ignore` rules for the Smart Scheduler and descheduler (compactor) ConfigMaps. Without them, Flux treats the config the Smart Agent writes into those ConfigMaps at runtime as drift and resets it to the copy stored at the last install or upgrade. See FAQ #16 for the complete HelmRelease and step-by-step setup.

**Karpenter clusters — `disruptionProtection`**

If your cluster runs Karpenter, its node consolidation/expiration can evict the Smart Agent, Pod Interceptor (+ its DB), Smart Scheduler, or compactor as it churns nodes — which shows up as their health flapping. This is on by default, but confirm it's set for each component you've enabled (see FAQ #15 for what it does):

```yaml
workload:
  smartAgent:
    disruptionProtection: true

sedaiPodInterceptor:
  disruptionProtection: true

sedaiSmartScheduler:
  disruptionProtection: true
  compactor:
    disruptionProtection: true
```

### 5. Deploy Sedai Smart Agent

Deploy Smart Agent Helm Chart in your Kubernetes Clusters. Make sure to over-ride cluster specific details using the over-ride values file.

```bash
cd sedai-smart-agent
helm upgrade --install sedai-smart-agent -n sedai-smart-agent --create-namespace -f values.yaml -f values-override-clustername.yaml .
```

### Supported CI/CD and deployment tools

The Sedai Smart Agent Helm chart supports deployment through the Helm CLI directly, as well as through GitOps tools such as Argo CD and Flux, which handle Helm charts in a way that preserves the lifecycle behavior the chart needs. CI/CD pipelines (for example Jenkins, GitHub Actions, or GitLab CI) are also supported as long as they install the chart by running Helm itself (`helm install` / `helm upgrade`). Tools that only render the chart into static manifests and apply them outside of Helm, such as Carvel's kapp and kapp-controller, are not supported, because they skip the Helm lifecycle that the enroll and cleanup jobs depend on. For GitOps manifests, see FAQ #13 (Argo CD) and FAQ #16 (Flux).

## Sedai Smart Agent - Helm Chart

Please pull the latest Helm Chart from our repository.

```bash
helm repo add sedai https://sedaiengineering.github.io/helm-charts/
helm repo update
helm pull sedai/sedai-smart-agent --untar
```

You can also use the helm repository directly without pulling the chart. The command would be:

```bash
helm repo add sedai https://sedaiengineering.github.io/helm-charts/
helm repo update
helm install sedai-smart-agent sedai/sedai-smart-agent -n sedai-smart-agent --create-namespace -f values-override-clustername.yaml
```

You can also upgrade the helm chart using the same helm repo. The command would be:

```bash
helm upgrade --install sedai-smart-agent sedai/sedai-smart-agent -n sedai-smart-agent --create-namespace -f values-override-clustername.yaml
```

## Sedai Smart Agent - Container Images

Container images for the Sedai Smart Agent and its related components are available in our public repositories.

Please refer to the default values specified in the Helm chart for the latest supported image tags. The chart is regularly updated to include the most recent stable versions of the Smart Agent and associated components.

Our ECR and Google Artifact Registry repositories are public. If you prefer to pull images from our Azure Container Registry (ACR), our team can share the required credentials with you.

If you are running an **air-gapped cluster**, images should be pulled from your private repositories. In that case, please set up a regular image sync from any of our public repositories.

| # | Container | Image URI (ECR) |
|---|---|---|
| 1 | smartAgent | `public.ecr.aws/sedai_io/sedai-smart-agent` |
| 2 | smartAgentEnroll | `public.ecr.aws/sedai_io/sedai-smart-agent-enroll` |
| 3 | ksm | `public.ecr.aws/sedai_io/prometheus/kube-state-metrics` |
| 4 | reload | `public.ecr.aws/sedai_io/prometheus/prometheus-config-reloader` |
| 5 | prometheus | `public.ecr.aws/sedai_io/prometheus/prometheus` |
| 6 | sedaiPodInterceptor | `public.ecr.aws/sedai_io/sedai-kube-spec-controller` |
| 7 | sedaiPodInterceptorDB | `public.ecr.aws/sedai_io/postgres` |
| 8 | nodeExporter | `public.ecr.aws/sedai_io/prometheus/node-exporter` |
| 9 | grafanabeyla | `public.ecr.aws/sedai_io/grafana/beyla` |
| 10 | grafanaAlloy | `public.ecr.aws/sedai_io/grafana/alloy` |
| 11 | victoriaMetrics | `public.ecr.aws/sedai_io/victoriametrics/victoria-metrics` |

## Sedai Smart Agent - FAQ

### 1. Do I need to create a custom values.yaml file?

Yes. You can reuse the same Helm chart and API key to onboard multiple Kubernetes clusters to Sedai. For easier management, we recommend creating a custom values.yaml file for each cluster. This approach simplifies upgrades, supports GitOps-based management, and keeps cluster-specific configurations organized within each values file.

### 2. Providing the Sedai API Key via Kubernetes Secret

Instead of specifying the Sedai API key directly in your `values.yaml`, you can securely provide it using a Kubernetes Secret. Create the Secret using your preferred method and reference its name and key in the values.yaml file.

```yaml
sedaiIntegrationSettings:
  sedaiApiTokenSecret: ""     # Name of the Kubernetes Secret that stores the token
  sedaiApiTokenSecretKey: ""  # Key within the Secret that stores the token
```

### 3. What endpoints need to be whitelisted?

The Sedai Smart Agent initiates all outbound connections. It must be able to communicate securely with the Sedai API endpoint over HTTPS/WebSocket (port 443).

Additionally, the Smart Agent sends telemetry data to Sedai's centralized platform.

Please ensure the following endpoints are whitelisted for outbound access on port 443:

- `tenant.sedai.app` — Sedai API and WebSocket communication (or your BYOC Sedai Endpoint if running Sedai in an air-gapped environment).
- `gw.sedai.cloud` — Smart Agent telemetry logs

### 4. How can I disable Sedai Agent telemetry log streaming to gw.sedai.cloud?

By default, the Sedai Smart Agent streams its telemetry logs to `gw.sedai.cloud`.

If outbound (egress) access to this endpoint is restricted, or if you prefer to view logs directly in the console for debugging, you can modify the setting in your Helm chart's `values.yaml` file:

```yaml
enableAgentDebugLogs:
  enabled: true
```

### 5. Image Pull Secret

If you are pulling container images from a private registry (for example, Sedai's Azure Container Registry), you can configure an image pull secret using the following values in your values.yaml file:

```yaml
imagePullSecret:
  enabled: true
  secretName: ""
```

This requires a Kubernetes secret in the same namespace as the Smart Agent, containing the `.dockerconfigjson` with your registry credentials.

To set the imagePullSecret for sedai ACR, run:

```bash
kubectl create secret docker-registry sedai-acr-secret \
  --docker-server=sedai.azurecr.io \
  --docker-username=<ACR_USERNAME> \
  --docker-password='<ACR_PASSWORD>' \
  -n sedai-smart-agent
```

### 6. Can I deploy Smart Agent with ReadOnly Permissions for POC

Yes. By default, when you onboard a Kubernetes cluster into Sedai, it operates in Data Pilot Mode, which collects data without making any changes. To enforce read-only mode at the cluster level, Sedai provides two ClusterRole templates. You can enable read-only mode by setting the following in your values file:

```yaml
sedaiIntegrationSettings:
  rbacReadOnly: true
```

### 7. Can I add multiple monitoring providers for a cluster?

Yes. You can configure multiple monitoring providers for a single Kubernetes cluster integration. Refer to the `monitoringProvider` section in the values.yaml file for the list of supported monitoring providers available through the self-provisioning workflow.

If your preferred monitoring provider isn't listed, feel free to reach out — our team is continuously adding more providers to the self-provisioning workflow.

### 8. Can I delete the Sedai integration automatically when decommissioning the cluster?

Yes. Sedai provides a post-delete hook job that automatically removes the integration when the cluster is decommissioned. To enable this feature, set `sedaiIntegrationSettings.enableDeRegisterJob` to `true` in your values.yaml. When you uninstall or delete the Smart Agent Helm chart, the corresponding Sedai integration will be automatically deleted.

```yaml
sedaiIntegrationSettings:
  enableDeRegisterJob: true
```

### 9. Google Cloud Monitoring integration with Service Account Key

Google Cloud Monitoring can be integrated with Sedai using the configuration options available in the values.yaml file.

This integration requires a GCP Service Account with the following roles:

- Monitoring Viewer
- Compute Viewer

The Service Account Key (in JSON format) is used to authenticate and access monitoring data.

You can configure this in two ways:

1. **(Not Recommended for Production)** Add the Service Account Key JSON directly to `monitoringProvider.serviceAccountKeyJson`.
2. **(Recommended - Secure Method)** Create a Kubernetes Secret containing the Service Account Key JSON, and reference it in the Helm chart:
   - `monitoringProvider.gcpSecret` → Name of the Kubernetes Secret containing the key
   - `monitoringProvider.gcpServiceAccountKeySecretKey` → Key within the Secret that stores the JSON content

```yaml
monitoringProvider:
  gcpMonitoring:
    enabled: true
    projectID:
    serviceAccountKeyJson:
    gcpSecret:
    gcpServiceAccountKeySecretKey:
```

### 10. How to Keep my Smart Agent version up-to-date?

To ensure your Sedai Smart Agent stays current with the latest improvements, features, and security updates, you should periodically update the Helm chart to pull the latest version of the Sedai Smart Agent container images.

Run the following commands to refresh the Helm repository and retrieve the latest version of the chart:

```bash
helm repo update
helm pull sedai/sedai-smart-agent --untar
```

This will download the latest chart version from the Sedai Helm repository, which includes:

- Updated Sedai Smart Agent container images
- Helm chart enhancements and bug fixes
- Configuration improvements for easier maintenance and onboarding

You can then review the release notes or values.yaml file for any new configuration options before upgrading your deployment.

### 11. What is Sedai Managed Victoria Metrics?

Sedai Managed Victoria Metrics is a lightweight, preconfigured Victoria Metrics setup included with the Sedai Smart Agent Helm Chart. It is designed for users who don't have an existing monitoring provider or are unable to grant external access due to network or security restrictions.

This Victoria Metrics deployment is optimized with minimal scrape configurations to collect only the metrics required by Sedai, with a default data retention period of 3 hours.

Optionally, you can also deploy:

- Kube State Metrics (KSM) and Prometheus Node Exporter for cluster and node-level insights.
- Grafana Beyla for deep network observability (eBPF based) and network cost attribution.
- Grafana Alloy as a unified alternative to Node Exporter, and Beyla.

Sedai does not modify these open-source components — only their configuration is fine-tuned for efficiency and compatibility with Sedai's optimization workflows.

### 12. How to delete Sedai Kubernetes Integration

You can delete the Kubernetes integration directly from the Sedai Administration UI.

Alternatively, if you have set `sedaiIntegrationSettings.enableDeRegisterJob: true` in your Helm values and subsequently uninstall the Helm chart from your Kubernetes cluster, the integration will be automatically removed from Sedai.

Deleting the cluster integration will permanently remove all data collected so far.

If you re-add the same cluster in the future, Sedai will treat it as a new Kubernetes integration with no historical data retained.

### 13. Can I deploy the Smart Agent Helm Chart via ArgoCD

Yes. You can deploy the Sedai Smart Agent using ArgoCD or any other GitOps provider. Below is a sample ArgoCD Application manifest for deploying the Smart Agent via Helm:

> **Note:** It is critical to include `ignoreDifferences` in your ArgoCD Application manifest. This prevents sync loops caused by dynamically generated secrets, mutated webhook configurations, and the Smart Scheduler and descheduler (compactor) ConfigMaps that the Smart Agent rewrites during runtime. `ignoreDifferences` alone only suppresses the diff/OutOfSync status, though — it does **not** stop an actual sync from overwriting those fields. Pair it with `syncOptions: [RespectIgnoreDifferences=true]` (included below) so a sync never resets them back to a fresh value.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: sedai-smart-agent
  namespace: argocd
spec:
  project: sedai-integration   # Update your Project Name here
  source:
    repoURL: https://sedaiengineering.github.io/helm-charts
    chart: sedai-smart-agent
    targetRevision: 2.0.8   # Update Latest Helm Chart Version here
    helm:
      values: |
        sedaiVictoriaMetrics:
          enabled: true
        sedaiKSM:
          enabled: true
        sedaiNodeExporter:
          enabled: true
        sedaiBeyla:
          enabled: true
        sedaiPodInterceptor:
          enabled: true
        sedaiSmartScheduler:
          enabled: true
          compactor:
            enabled: true
        sedaiIntegrationSettings:
          nickName: "your-k8s-cluster-nickname"
          clusterName: "your-k8s-cluster"
          clusterProvider: "AWS"
          sedaiBaseUrl: "https://tenant.sedai.app"
          sedaiApiTokenSecret: ""
          sedaiApiTokenSecretKey: ""

  destination:
    server: https://kubernetes.default.svc
    namespace: sedai-smart-agent

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - RespectIgnoreDifferences=true

  ignoreDifferences:
    - group: ""
      kind: Secret
      name: sedai-kube-spec-controller-db
      namespace: sedai-smart-agent
      jsonPointers:
        - /data/password
    - group: ""
      kind: Secret
      name: sedai-kube-spec-controller-tls
      namespace: sedai-smart-agent
      jsonPointers:
        - /data/ca.crt
        - /data/tls.crt
        - /data/tls.key
    - group: admissionregistration.k8s.io
      kind: MutatingWebhookConfiguration
      name: sedai-kube-spec-controller-mutation-webhook-sedai-smart-agent
      jqPathExpressions:
        - '.webhooks[].clientConfig.caBundle'
    - group: ""
      kind: ConfigMap
      name: sedai-smart-scheduler-config
      namespace: sedai-smart-agent
      jsonPointers:
        - /data
    - group: ""
      kind: ConfigMap
      name: sedai-smart-compactor-config
      namespace: sedai-smart-agent
      jsonPointers:
        - /data
```

### 14. My cluster's DNS resolution is misconfigured — the Pod Interceptor can't reach its Service

The Smart Agent reaches the Pod Interceptor over the short-form Service DNS name (`<svc>.<namespace>.svc`), which relies on the pod's search-domain expansion to append the cluster's real domain (normally `cluster.local`). This works on virtually all clusters. If a cluster's kubelet/CoreDNS domain configuration has drifted apart and that expansion is failing — symptom: a Java/JVM `Name does not resolve` error on a `*.svc` address that otherwise resolves fine with the full FQDN appended — set `clusterDomain` in your values to force fully-qualified Service DNS names instead:

```yaml
clusterDomain: "cluster.local"   # -> sedai-kube-spec-controller-svc.<namespace>.svc.cluster.local
```

Leave empty (the default) unless you're hitting that specific symptom.

### 15. Karpenter Disruption Protection

If your cluster runs Karpenter, its node consolidation/expiration can evict any pod as it churns nodes — for the Smart Agent, the Pod Interceptor (+ its DB), the Smart Scheduler, and the compactor, that shows up as their health flapping. This is separate from the `sedaiKarpenter.enabled` toggle (which opts the cluster in to Sedai deploying and managing Karpenter itself) — disruption protection applies whenever Karpenter is managing your nodes, whether or not Sedai deployed it.

Each of those four components has its own `disruptionProtection` value (default `true`) that adds the `karpenter.sh/do-not-disrupt: "true"` annotation to the pod, so Karpenter skips proactively consolidating any node hosting it:

```yaml
workload:
  smartAgent:
    disruptionProtection: true

sedaiPodInterceptor:
  disruptionProtection: true

sedaiSmartScheduler:
  disruptionProtection: true
  compactor:
    disruptionProtection: true
```

Set any of these to `false` to let Karpenter churn that component's nodes freely.

### 16. Can I deploy the Smart Agent Helm Chart via Flux

Yes. Flux's helm-controller installs and upgrades the chart with Helm itself, so the enroll (`pre-install`) and de-register (`post-delete`) hook jobs run the same way they do with the Helm CLI. This requires Flux v2.3 or later (`helm.toolkit.fluxcd.io/v2` and `source.toolkit.fluxcd.io/v1`).

> **Note:** If you turn on Flux drift detection (`spec.driftDetection.mode: enabled`), you **must** include the `ignore` rules for the Smart Scheduler and descheduler (compactor) ConfigMaps shown below. Drift detection compares the cluster against the manifest Helm stored at the last install or upgrade. The Smart Agent rewrites these two ConfigMaps at runtime, so without the rules Flux sees the agent's changes as drift and resets them to the stored copy (the bootstrap config, after a fresh install), undoing the scheduler profiles and compactor policy that Sedai pushed. Drift detection is off by default in Flux; if you leave it off, you can drop the `driftDetection` block.
>
> Unlike ArgoCD, Flux does not need ignore rules for the Pod Interceptor secrets or the webhook `caBundle`. helm-controller renders the chart against the live cluster, so the generated TLS certificate and DB password are read back and kept the same on every upgrade.

**Step 1: Create the namespace and the API key Secret**

Keep the Sedai API key out of Git. Create the Secret directly, or through your secrets tooling (SOPS, Sealed Secrets, External Secrets Operator) under the same name and key:

```bash
kubectl create namespace sedai-smart-agent
kubectl create secret generic sedai-api-token \
  --from-literal=api-token='<SEDAI_API_KEY>' \
  -n sedai-smart-agent
```

**Step 2: Add the Sedai Helm repository**

Commit the following to the Git path that your Flux `Kustomization` reconciles for this cluster (for example `clusters/<cluster-name>/sedai-smart-agent/`):

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: sedai
  namespace: sedai-smart-agent
spec:
  interval: 1h
  url: https://sedaiengineering.github.io/helm-charts
```

**Step 3: Add the HelmRelease**

Add the HelmRelease in the same path. Keep the name `sedai-smart-agent`, keep it in the `sedai-smart-agent` namespace, and do not set `spec.targetNamespace` or `spec.releaseName`. That gives the Helm release the same name and namespace as a Helm CLI install (see Step 5).

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: sedai-smart-agent          # Also the Helm release name
  namespace: sedai-smart-agent
spec:
  interval: 10m
  timeout: 10m                     # Flux waits for every workload to become ready; 5m (the default) can be tight on a fresh cluster
  chart:
    spec:
      chart: sedai-smart-agent
      version: "2.0.36"            # Update Latest Helm Chart Version here
      sourceRef:
        kind: HelmRepository
        name: sedai
      interval: 1h
  values:
    sedaiVictoriaMetrics:
      enabled: true
    sedaiKSM:
      enabled: true
    sedaiNodeExporter:
      enabled: true
    sedaiBeyla:
      enabled: true
    sedaiPodInterceptor:
      enabled: true
    sedaiSmartScheduler:
      enabled: true
      compactor:
        enabled: true
    sedaiIntegrationSettings:
      nickName: "your-k8s-cluster-nickname"
      clusterName: "your-k8s-cluster"
      clusterProvider: "AWS"
      sedaiBaseUrl: "https://tenant.sedai.app"
      sedaiApiTokenSecret: "sedai-api-token"
      sedaiApiTokenSecretKey: "api-token"

  # Required when drift detection is on: the Smart Agent rewrites these ConfigMaps at runtime.
  driftDetection:
    mode: enabled
    ignore:
      - paths: ["/data"]
        target:
          kind: ConfigMap
          name: sedai-smart-scheduler-config
          namespace: sedai-smart-agent
      - paths: ["/data"]
        target:
          kind: ConfigMap
          name: sedai-smart-compactor-config
          namespace: sedai-smart-agent
```

The ConfigMap names above are the chart defaults. If you override `workload.smartScheduler.name` or `workload.smartCompactor.name`, use `<name>-config` instead. To only report drift without correcting it, set `mode: warn`. To turn drift detection off, set `mode: disabled` or remove the block.

**Step 4: Commit and verify**

Commit and push, then let Flux reconcile (or trigger it yourself):

```bash
flux reconcile kustomization <your-kustomization> --with-source
flux get helmreleases -n sedai-smart-agent
kubectl get pods -n sedai-smart-agent
```

The HelmRelease should show `Ready` `True`, and the cluster appears in the Sedai UI once the enroll job has finished.

After Sedai has pushed scheduler and compactor config to the cluster, you can confirm that drift detection leaves it alone:

```bash
flux reconcile helmrelease sedai-smart-agent -n sedai-smart-agent
kubectl get configmap sedai-smart-scheduler-config sedai-smart-compactor-config -n sedai-smart-agent -o yaml
flux events --for HelmRelease/sedai-smart-agent -n sedai-smart-agent
```

The ConfigMaps should still hold the config Sedai pushed (not the `sedai-scheduler-bootstrap` profile), and the events should show no drift correction on them.

**Step 5: Migrating an existing Helm CLI install (optional)**

If the Smart Agent was already installed with `helm upgrade --install sedai-smart-agent -n sedai-smart-agent`, Steps 1 to 4 take it over in place. Because the HelmRelease uses the same release name and namespace, helm-controller finds the existing release in Helm storage and upgrades it instead of attempting a fresh install. Skip `kubectl create namespace` in Step 1, and create the API key Secret only if the install doesn't already reference one.

**Upgrading**

Change `version` in the HelmRelease and commit; Flux runs `helm upgrade` for you. You can also set a semver range (for example `version: "2.0.x"`) so Flux picks up new patch versions automatically.

**Things to avoid**

- **Uninstall-based remediation.** Leave `spec.install.remediation.retries` at its default (`0`), and never set `spec.upgrade.remediation.strategy: uninstall`. Both make Flux uninstall the release after a failure. With `sedaiIntegrationSettings.enableDeRegisterJob: true`, an uninstall runs the de-register hook, which deletes the cluster's integration and all of its data in Sedai (see FAQ #12).
- **Rollback remediation.** With `spec.upgrade.remediation.retries` above `0`, a failed upgrade is rolled back by reapplying the previous release's stored manifest. That also resets the Smart Scheduler and compactor ConfigMaps to the copy saved at that release. Keeping remediation at the defaults avoids this.
- **Deleting the HelmRelease to pause Flux.** Deleting the HelmRelease, or removing it from Git with `prune: true`, uninstalls the chart; with `enableDeRegisterJob: true` that also removes the integration from Sedai, just like `helm uninstall`. To pause Flux without uninstalling, set `spec.suspend: true` instead.

## Sedai Smart Agent - Help?

Reach out to [support@sedai.io](mailto:support@sedai.io) for any assistance.
