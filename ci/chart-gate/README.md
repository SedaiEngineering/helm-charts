# Chart gate

`.github/workflows/chart-gate.yml` runs this on every PR and push to `main` and `edge` that
touches `charts/**`. It installs the chart **from the PR checkout** (a PR's chart is never
published, so nothing else can test it before merge) and fails if any component does not come up.
It needs no secrets: the Sedai API is mocked inside the cluster, so fork PRs get the same gate.

## What it checks

**Render** (`gate.py static`, no cluster, ~30s) for every profile in `profiles/`:

| Check | Catches |
|---|---|
| `helm lint --strict` | template and values errors |
| `helm template` on every k8s minor the chart maps (1.26–1.36), same resources on each | render errors; a component that silently stops rendering on one minor (the scheduler and compactor are gated on per-minor image maps) |
| `expected/<profile>.txt` — exactly these resources, no more, no less | an added, removed or renamed resource that was not intended |
| `expected/<profile>.rbac.txt` — every rule bound to every ServiceAccount, hooks included | a permission added or dropped, for the agent and for every hook Job |
| every rendered image resolves anonymously, across all minors | a tag that does not exist, or a registry that needs credentials |

**Install** (`gate.py install --profile <p>`, throwaway k3d cluster with real kubelets):

1. Deploys `mock-core/` — a stand-in for the Sedai API that records every call — and fixture
   workloads in `fixtures/`.
2. `helm install` from the checkout with the chart's hooks pointed at the mock,
   `--wait=watcher --wait-for-jobs`. Hook pods are streamed to the artifacts while they run.
3. Asserts:
   - **hooks**: no hook pod failed (retried attempts included) and no hook log shows a 403;
   - **enroll**: the real path ran — reachability, one account created with the chart's
     clusterName / provider, the agent Secret fetched and applied, and the profile's monitoring
     providers registered;
   - every **monitoring provider endpoint** is a Service in the release that answers PromQL;
   - every Deployment / StatefulSet / DaemonSet the release rendered is **Ready** (a DaemonSet must
     run at least one pod), checked again after the discovery window;
   - **no container restarted** and every container runs the image the chart rendered — right
     after install and again after discovery, so a crash or OOM kill after startup is caught;
   - the agent's `/agent/health` is UP and reports the chart's `image.smartAgent.imageTag`, and
     the agent runs in the configured REST connection mode;
   - **spec-controller**: each MutatingWebhookConfiguration trusts the generated CA, the certificate
     is valid for the Service the webhooks call, the controller answers `/sedai/health` over TLS,
     and a server-side dry-run Pod create and Deployment update are each answered by the
     controller (read from the API server's webhook metrics, fail-open excluded);
   - **discovery**: the agent pushes a topology round containing the fixture workloads and every
     workload in the release (matched by resource id) and finalizes exactly the ids it pushed;
   - the agent hits no **RBAC denial** beyond `expected/<profile>.rbac-denials.txt`;
   - **uninstall**: the post-delete hook deletes the agent Secret; with `enableDeRegisterJob`
     (profile `full`) it also deletes the Sedai account, otherwise it leaves it alone; no pods remain.

| Profile | Installs | What it covers |
|---|---|---|
| `default` | yes | chart defaults: agent + enroll hooks, default cleanup hook |
| `full` | yes | every component that runs on a CPU-only node except the eBPF instrumenters; deregister hook. Requests are lowered to fit a 4 vCPU runner; limits stay at the chart defaults |
| `observability` | yes | the eBPF instrumenters — Beyla and Grafana Alloy — with the VictoriaMetrics store they feed |
| `gpu` | render only | DCGM exporter (needs a GPU node) |
| `readonly` | render only | `rbacReadOnly` (the read-only agent ClusterRole) |

## Running it locally

```bash
python3 ci/chart-gate/gate.py static
python3 ci/chart-gate/gate.py install --profile full --keep-cluster
```

Needs helm 4, kubectl, openssl, k3d, Docker and python3 with PyYAML. The install uses its own
kubeconfig under `chart-gate-artifacts/<profile>/` and never touches your current context.
`--keep-cluster` leaves the cluster up for inspection; delete it with
`k3d cluster delete chart-gate-<profile>`.

## When the gate fails

- **expected resource list / RBAC**: if the chart change is intended, run
  `python3 ci/chart-gate/gate.py golden` and commit the updated `expected/*.txt`. The diff in the
  PR then shows reviewers exactly which resources or permissions changed.
- **RBAC denials**: grant the permission in the chart. If the gap is accepted, add the line to
  `expected/<profile>.rbac-denials.txt`; a line that no longer occurs is reported for removal.
- **install**: the job uploads `chart-gate-<profile>` artifacts: hook Job logs, every pod's current
  and previous logs, the full log of any container that restarted (`crashes/`), `describe`
  output, events, the k3s server log and the mock's recorded calls (`mock-state.json`).

## Limits

- The mock answers with the shapes the enroll scripts and agent parse. It does not prove the
  hosted Sedai API accepts what the agent sends.
- The correct-cluster-name hook runs in `full`, but it only acts on GKE, so it never reaches the
  API here.
- One discovery round: the agent's next scheduled round is an hour later.
