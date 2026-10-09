# Chart gate

`.github/workflows/chart-gate.yml` runs the chart gate on every PR, and on every push to `main` and
`edge`, that touches `charts/**` or the gate. It installs the chart **from the PR's merge commit** (a
PR's chart is never published, so nothing else can test it before merge) into a throwaway k3d
cluster and fails if any component does not come up.

The gate's code lives in [SedaiEngineering/sedai-tests](https://github.com/SedaiEngineering/sedai-tests),
`chart-gate/`, with the other test suites: the workflow checks it out from `main` with
`secrets.GHPAT`, as exporters-v2 does for its integration tests. Its README lists every check.
PRs from forks get no secrets, so the gate fails on them.

This directory is the chart's own gate data. It sits next to the chart so a chart PR updates it in
the same PR:

| Path | What |
|---|---|
| `profiles/<profile>.yaml` | values installed on top of `values/gate.yaml`, one per profile |
| `profiles/<profile>.expect.json` | what the profile should produce: monitoring providers, deregister, whether it installs |
| `expected/<profile>.txt`, `.rbac.txt` | exactly the resources and the RBAC each profile renders |
| `expected/<profile>.rbac-denials.txt` | RBAC denials the agent is allowed to log during discovery |
| `values/gate.yaml` | points the chart's hooks and agent at the gate's mock Sedai API |

| Profile | Installs | What it covers |
|---|---|---|
| `default` | yes | chart defaults: agent + enroll hooks, default cleanup hook |
| `full` | yes | every component that runs on a CPU-only node except the eBPF instrumenters; deregister hook. Requests are lowered to fit a 4 vCPU runner; limits stay at the chart defaults |
| `observability` | yes | the eBPF instrumenters — Beyla and Grafana Alloy — with the VictoriaMetrics store they feed |
| `gpu` | render only | DCGM exporter (needs a GPU node) |
| `readonly` | render only | `rbacReadOnly` (the read-only agent ClusterRole) |

## Required check

Require the **`Chart Gate`** check, not the render or install jobs. The workflow starts on every PR,
so `Chart Gate` always reports: it fails if render or any install profile fails or is cancelled, and
passes without a cluster when the PR changes nothing under `charts/`, `ci/chart-gate/` or the
workflow. Requiring a path-filtered job instead would leave every other PR waiting on a check that
never runs. It also re-runs when a PR's base branch is changed, since that changes what the PR merges.

Ruleset settings for `main` and `edge` that the check relies on:

- require `Chart Gate` from GitHub Actions;
- require branches to be up to date before merging. The check tests the PR merged into the base as
  it was when the check ran, and a later change to the base does not re-run it;
- require code-owner review for `.github/workflows/` and `ci/chart-gate/`. A PR runs its own copy of
  this workflow, so a PR that edits the workflow decides its own result.

## Running it locally

With sedai-tests cloned next to this repo, from the root of this repo:

```bash
python3 ../sedai-tests/chart-gate/gate.py static
python3 ../sedai-tests/chart-gate/gate.py install --profile full --keep-cluster
```

Needs helm 4, kubectl, openssl, k3d, Docker and python3 with PyYAML. On a fresh Linux host, load the
kernel modules listed in the workflow's "Load the kernel modules k3s uses" step first.

## When the gate fails

- **expected resource list / RBAC**: if the chart change is intended, run
  `python3 ../sedai-tests/chart-gate/gate.py golden` and commit the updated `expected/*.txt`. The
  diff in the PR then shows reviewers exactly which resources or permissions changed.
- **RBAC denials**: grant the permission in the chart. If the gap is accepted, add the line to
  `expected/<profile>.rbac-denials.txt`; a line that no longer occurs is reported for removal.
- **install**: the job uploads `chart-gate-<profile>` artifacts: hook Job logs, every pod's current
  and previous logs, the full log of any container that restarted (`crashes/`), `describe`
  output, events, the k3s server log and the mock's recorded calls (`mock-state.json`).
