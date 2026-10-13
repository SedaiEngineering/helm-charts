# Contributing

This repo publishes one Helm chart, [`sedai-smart-agent`](charts/sedai-smart-agent/), to:

- a Helm repo on GitHub Pages — `https://sedaiengineering.github.io/helm-charts/`
- an OCI artifact in a public ECR repo (stable releases only)

## Branches and release channels

Three long-lived branches, each mapped to a release channel. Pushing a change to
`charts/sedai-smart-agent/Chart.yaml`'s `version` on any of them is what cuts a release — a
GitHub Action (`chart-releaser-action`) packages and publishes it automatically. Everything else
(templates, values, docs) can be merged freely without triggering a release.

| Branch | Channel | `version` format | Example | `mark_as_latest` |
|---|---|---|---|---|
| `main` | Stable | Plain semver, no suffix | `2.0.18` | yes — this is what `helm install` resolves by default |
| `edge` | Edge | Must contain `-edge.N` | `2.1.1-edge.2` | no |
| `dev` | Beta / QA | Must contain `-beta.N` | `2.1.1-beta.4` | no |

Use them as:

- **`main`** — what customers get by default. Only tested, reviewed changes land here.
- **`edge`** — newer features ahead of the next stable cut, for anyone opted in to running closer
  to the tip. Never marked latest, so it's never installed by accident.
- **`dev`** — where work lands first for internal QA, before being promoted toward `edge`/`main`.

### CI-enforced guardrails (not just convention)

- Each release workflow only triggers on a push that touches `Chart.yaml` — editing other files
  doesn't cut a release by itself.
- `dev`'s workflow **fails the build** if `version` doesn't contain `beta`; `edge`'s fails if it
  doesn't contain `edge` — so you can't accidentally publish a beta-looking version from `edge` or
  vice versa.
- A **PR check on `main`** (`pr-check-no-prerelease.yaml`) blocks merging anything whose `version`
  still has a `beta`/`edge` suffix — `main` only ever ships clean semver.
- Only `main` pushes to the OCI/ECR mirror (`chart-release-oci.yaml`); `dev`/`edge` publish to the
  Helm repo index only.

## Opening a change

1. Branch off whichever channel you're targeting (usually `main`, unless the change is
   channel-specific).
2. Make the change. Run before opening a PR:
   ```bash
   helm lint charts/sedai-smart-agent --set <relevant-components>.enabled=true
   helm template test charts/sedai-smart-agent --set workload.smartAgent.secret=x
   ```
   — lint clean, and spot-check the rendered output for anything you touched (a new
   conditional, a renamed value, a new resource). If the change affects a values default, check
   it in both the enabled and disabled state.
3. Open a PR against that branch.

### A change that needs to land on more than one channel

Branches diverge (different `Chart.yaml` versions, occasionally channel-specific content), so a
straight merge/fast-forward across them doesn't work. Instead:

1. Open the PR and get it merged on the first branch.
2. Branch off each other target branch (`origin/dev`, `origin/edge`, etc.) and
   `git cherry-pick <commit-sha>` the same commit(s) across.
3. Resolve any conflicts per branch (usually minor — e.g. a neighboring value that only exists on
   one channel), re-run the lint/template checks above, then open a PR per branch.

This is slower than a single PR, but keeps each branch's history honest about what it actually
contains, and lets `edge`/`dev`-specific content stay where it belongs without leaking into `main`.

## The chart gate (`Chart Gate` check)

Every PR to `main` or `edge` that touches `charts/` runs `Chart Gate`
(`.github/workflows/chart-gate.yml`). It renders the chart on every supported Kubernetes version,
checks that it deploys exactly what the expected lists say, installs it into a throwaway cluster,
and checks every component comes up and discovery finds it. The gate's code and its expected
lists live in SedaiEngineering/sedai-tests, `chart-gate/`; this repo only has the workflow.

**A change that adds or removes a resource or a permission** (a new Deployment, Service, hook Job,
RBAC rule, ...) fails the gate until the expected lists in sedai-tests match. To make that change:

1. Open the chart PR as usual. `Chart Gate` fails and names what is missing or unexpected.
2. From your chart branch's checkout, with sedai-tests cloned next to this repo, run
   `python3 ../sedai-tests/chart-gate/gate.py golden --channel <main|edge>`. It rewrites
   `chart-gate/expected/<channel>/` in sedai-tests. Open a sedai-tests PR with that diff.
3. Merge the sedai-tests PR, re-run `Chart Gate` on the chart PR, and merge the chart PR right
   after. Between the two merges, other open chart PRs on that channel fail the gate.
4. When the change is cherry-picked to the other channel, do the same for that channel's lists.

Changes that do not change what is deployed (version bumps, image tags, values defaults) need
nothing in sedai-tests. Details: `chart-gate/README.md` in sedai-tests.

## Docs that live alongside the chart

- [`README.md`](charts/sedai-smart-agent/README.md) — chart reference: every component, its
  values, and example configuration snippets.
- [`CONFIGURATION.md`](charts/sedai-smart-agent/CONFIGURATION.md) — configuration guide, common
  patterns, best practices.
- [`ONBOARDING.md`](charts/sedai-smart-agent/ONBOARDING.md) — step-by-step self-provisioning
  walkthrough for a new cluster (API key, values-override examples per cloud provider, ArgoCD
  deployment, FAQ). Also published as a standalone styled page at
  `https://sedaiengineering.github.io/helm-charts/onboarding.html` (source: `onboarding.html` at
  the repo root of the `gh-pages` branch) — **that page is a manual mirror of `ONBOARDING.md`,
  not auto-generated**. If you edit one, update the other, and push to all three channel
  branches the same way as any other multi-channel change.

If a change adds or changes a value, default, or behavior a user would need to know about, update
the relevant doc(s) in the same PR.
