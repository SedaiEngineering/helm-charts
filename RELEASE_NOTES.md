# Release Notes — sedai-smart-agent

Generated from the git history of `main` on the first-parent line. A release is the first commit that changes `version` in `charts/sedai-smart-agent/Chart.yaml`; each release lists the commits since the previous bump, up to and including that bump. Merge commits are omitted.

## 2.0.15 — 2026-09-25

Version bumped in `c717f67`.

- adding resource quota to agent; adding proxy settings to all jobs; adding option to configure WS / REST for agent via values file (`55379d2`, haribtw, 2026-09-25)
- bumped chart version (`c717f67`, haribtw, 2026-09-25)

## 2.0.14 — 2026-09-22

Version bumped in `b127dba`.

- docs: document disruptionProtection and clusterDomain in README (`f305dfd`, Arun Ramesh, 2026-09-21)
- docs: add self-provisioning onboarding guide as ONBOARDING.md (`94eeeec`, Arun Ramesh, 2026-09-21)
- docs: link README to ONBOARDING.md, trim PDB detail from FAQ #15 (`8e9387d`, Arun Ramesh, 2026-09-21)
- docs: surface disruption-avoidance settings directly in deployment steps (`2f01ba9`, Arun Ramesh, 2026-09-21)
- docs: scope the "strongly recommend" line to Pod Interceptor (`5949ef4`, Arun Ramesh, 2026-09-21)
- docs: add RespectIgnoreDifferences=true to the ArgoCD example (`a6523a9`, Arun Ramesh, 2026-09-21)
- upgrading agent to 2.0.10 (`b127dba`, haribtw, 2026-09-22)

## 2.0.13 — 2026-09-21

Version bumped in `4fbdc3e`.

- chore(prod): bump sedaiSync image to v2.1.0 (`37aef9f`, sedai-ops-bot, 2026-09-18)
- Update values.yaml (`73dcbd2`, arun-sedai, 2026-09-21)
- removing metaspace reference from Dockerfile (`220868d`, haribtw, 2026-09-21)
- feat: protect singleton pods from Karpenter node-churn eviction (`ea46476`, Arun Ramesh, 2026-09-21)
- fixup: simplify scheduler/compactor disruption protection, no toggle (`0539778`, Arun Ramesh, 2026-09-21)
- fixup: gate scheduler/compactor karpenter.sh/do-not-disrupt behind a toggle (`30dbbd7`, Arun Ramesh, 2026-09-21)
- feat: protect smart-agent from Karpenter node-churn eviction too (`3f722d4`, Arun Ramesh, 2026-09-21)
- fixup: drop the spec-controller/DB PDB, keep just the annotation (`edfa954`, Arun Ramesh, 2026-09-21)
- Update values.yaml (`32b8fe3`, arun-sedai, 2026-09-21)
- Update values.yaml (`af459b7`, arun-sedai, 2026-09-21)
- Update Chart.yaml (`4fbdc3e`, arun-sedai, 2026-09-21)

## 2.0.12 — 2026-09-18

Version bumped in `c6eb41f`.

- adding ns exclusion for spec controller (`c6eb41f`, haribtw, 2026-09-18)

## 2.0.11 — 2026-09-17

Version bumped in `755d6b9`.

- feat: add clusterDomain toggle for the spec-controller service URL (`7e8ca0d`, Arun Ramesh, 2026-09-17)
- docs: add example value for clusterDomain in values.yaml (`1a33b33`, Arun Ramesh, 2026-09-17)
- Update Chart.yaml (`755d6b9`, arun-sedai, 2026-09-17)

## 2.0.10 — 2026-09-17

Version bumped in `a1cb3b3`.

- Update Chart.yaml (`a1cb3b3`, haribtw, 2026-09-17)

## 2.0.10-edge.2 — 2026-09-17

Version bumped in `290d0ad`.

- edge version branch (`acc209c`, haribtw, 2026-09-11)
- edge release (`d73541f`, haribtw, 2026-09-11)
- adding sedaiBundled flag (`8602a1a`, haribtw, 2026-09-14)
- using container support instead of xms (`92b78e9`, haribtw, 2026-09-16)
- agent to v2.0.7 (`3600a23`, Arun Ramesh, 2026-09-16)
- agent to v2.0.7 (`1830d32`, Arun Ramesh, 2026-09-16)
- using container support instead of xms (`a1056de`, haribtw, 2026-09-16)
- Update values.yaml (`7427b96`, arun-sedai, 2026-09-17)
- Update Chart.yaml (`290d0ad`, arun-sedai, 2026-09-17)

## 2.0.9 — 2026-09-16

Version bumped in `7a6dac3`.

- Update Chart.yaml (`7a6dac3`, arun-sedai, 2026-09-16)

## 2.0.8-beta.1 — 2026-09-16

Version bumped in `fd3e958`.

- Update Chart.yaml (`b9d6130`, arun-sedai, 2026-09-16)
- fixing sheduler flag (`fd3e958`, Arun Ramesh, 2026-09-16)

## 2.0.8 — 2026-09-15

Version bumped in `8d88309`.

- adding sedaiBundled flag (`f13e191`, haribtw, 2026-09-14)
- logs for scheduler (`4204e26`, Arun Ramesh, 2026-09-14)
- logs for scheduler (`22ad0dd`, Arun Ramesh, 2026-09-14)
- Update Chart.yaml (`85bcec8`, arun-sedai, 2026-09-14)
- logs for scheduler (`61f3364`, Arun Ramesh, 2026-09-14)
- Update Chart.yaml (`6760bc1`, arun-sedai, 2026-09-14)
- Update Chart.yaml (`780736c`, arun-sedai, 2026-09-14)
- logs for scheduler (`af98e75`, Arun Ramesh, 2026-09-14)
- Update Chart.yaml (`5da1d4b`, arun-sedai, 2026-09-14)
- Source AGENT_TENANT/AGENT_ACCOUNTID for log-forwarder from the agent's own Secret (`c14af7e`, Arun Ramesh, 2026-09-15)
- Update Chart.yaml (`3ad6359`, arun-sedai, 2026-09-15)
- Update Chart.yaml (`8d88309`, arun-sedai, 2026-09-15)

## 2.0.7 — 2026-09-14

Version bumped in `3e084d8`.

- adding sedaiBundled flag (`3e084d8`, haribtw, 2026-09-14)

## 2.0.6 — 2026-09-14

Version bumped in `1ad2929`.

- pr check for edge (`cf9601b`, haribtw, 2026-09-11)
- Update Chart.yaml (`1ad2929`, arun-sedai, 2026-09-14)

## 2.0.6-beta.1 — 2026-09-10

Version bumped in `60cc7fc`.

- chore(prod): bump sedaiSync image to 0.1.5 (`fec93de`, sedai-ops-bot, 2026-08-27)
- chore(prod): bump sedaiSync image to 1.0.0 (`854369b`, sedai-ops-bot, 2026-09-01)
- chore(prod): bump sedaiSync image to v2.0.0 (`5cead0e`, sedai-ops-bot, 2026-09-01)
- using release namespace for spec controller cm (`a8cdaf7`, haribtw, 2026-09-10)
- pr check for edge (`b40aea3`, haribtw, 2026-09-11)
- reverting (`6dadb14`, haribtw, 2026-09-14)
- Kubeflow Spark - VM Alert and Metrics (`a7d5b92`, Thomas Abraham, 2026-05-27)
- Added App Selector label to be emitted in KSM (`491593c`, Thomas Abraham, 2026-05-27)
- Kubeflow Spark - VM Alert and Metrics (`21d4b42`, Thomas Abraham, 2026-06-14)
- Added Spark Optimization changes - Adding Components (`5601324`, Thomas Abraham, 2026-06-24)
- Added Spark Optimization changes - Adding Components (`2a0610e`, Thomas Abraham, 2026-06-24)
- spark-kubeflow-integration-webhook (`b179ea4`, abhinavkrishnav, 2026-06-24)
- Address PR #17 review comments (`a47d1f3`, Thomas Abraham, 2026-06-25)
- adding scheduler-chart (`47207f8`, arun-sedai, 2026-06-26)
- adding scheduler-chart (`894e34c`, arun-sedai, 2026-06-26)
- adding scheduler-chart (`8756532`, arun-sedai, 2026-06-26)
- testing beta branch (`dcb542e`, haribtw, 2026-06-24)
- fixing latest flag (`33898e9`, haribtw, 2026-06-24)
- setting latest (`91ce2f5`, haribtw, 2026-06-24)
- Updating webhook endpoint to use new endpoint for podspec (`13d1fbc`, Thomas Abraham, 2026-06-14)
- beta release for kube spec controller (`ed6dfa9`, haribtw, 2026-06-24)
- added lookup to avoid cert generation (`2fe035f`, haribtw, 2026-06-25)
- adding rbac for kube spec controller (`310a555`, haribtw, 2026-06-25)
- adding security context for victoria metrics (`4d0c2ed`, haribtw, 2026-06-26)
- Update Chart.yaml (`747dee2`, haribtw, 2026-06-26)
- using similar names for compactor and scheduler; setting compactor enabled by default (`7d798e6`, haribtw, 2026-06-26)
- fixing cert generation (`8bd4f08`, haribtw, 2026-06-26)
- scheduler logs (`58d7cfe`, arun-sedai, 2026-06-29)
- scheduler logs (`aed0d71`, arun-sedai, 2026-06-29)
- Revert "scheduler logs" (`2eb52c5`, haribtw, 2026-06-29)
- bump chart to 1.4.63-beta.10 (`ec2185d`, haribtw, 2026-06-29)
- bump appVersion to 1.4.63-beta.10 (`92e8153`, haribtw, 2026-06-29)
- adding lookup for scheduler and compactor bootstrap configmaps; bump up chart version (`3174f34`, haribtw, 2026-06-30)
- Fix for Spark (`0030e79`, Thomas Abraham, 2026-06-29)
- Fixes for Spark (`c6d4def`, Thomas Abraham, 2026-06-29)
- disabling scheduler + compactor; spark changes; helm version bump up (`d4bf7fc`, haribtw, 2026-06-30)
- adding dra permissions; priorityclass (`0ddf9bf`, haribtw, 2026-06-30)
- fixing naming convention; enabled sync by default (`157d803`, haribtw, 2026-06-30)
- updating images to public (`b90ce7f`, arun-sedai, 2026-06-30)
- SED-18859 Add filesystem metrics to node exporter (`e44012c`, Athul Raj K, 2026-07-15)
- Host address customization (`44aeadf`, Thomas Abraham, 2026-08-02)
- Host address customization - Commit 2 (`c1f0e9b`, Thomas Abraham, 2026-08-02)
- Host address customization - Adjusted agent port (`8660be5`, Thomas Abraham, 2026-08-03)
- updating enroll job version to v3.1.17 (`6512ea3`, haribtw, 2026-08-04)
- adding support for optedEnableKarpenter (`a7c62e6`, haribtw, 2026-08-04)
- Update values.yaml (`68afafa`, arun-sedai, 2026-08-04)
- Update Chart.yaml (`f1cae27`, arun-sedai, 2026-08-04)
- feat(SED-21442): add Postgres store for the kube spec controller (`237860a`, brian, 2026-08-05)
- refactor(SED-21442): split spec-controller DB PVC into its own template (`f534909`, brian, 2026-08-05)
- Revert "feat(SED-21442): add Postgres store for the kube spec controller" (`d2d9e9b`, haribtw, 2026-08-07)
- adding cleanup job for legacy migration (`9e211ae`, haribtw, 2026-08-10)
- Revert "Revert "feat(SED-21442): add Postgres store for the kube spec controller"" (`3019040`, brian, 2026-08-12)
- Update Chart.yaml (`5b13514`, brian, 2026-08-13)
- Update Chart.yaml (`f492f9a`, brian, 2026-08-13)
- adding job to correct cluster names using gke metadata (`1959048`, haribtw, 2026-08-14)
- corrected secret name (`b406e86`, haribtw, 2026-08-27)
- scheduler version fix (`ad1deeb`, haribtw, 2026-08-25)
- adding regex to allow *metrics.* for node exporter scraping; using 19100 as default node exporter port (`27c0436`, haribtw, 2026-08-27)
- broaden spec-controller RBAC for custom-CRD owner resolution (`c42c589`, arun-sedai, 2026-08-27)
- fix: broaden spec-controller RBAC for custom-CRD owner resolution (`6abf28e`, brian, 2026-08-27)
- avoids hitting sedai api if secret already present (`860d1f7`, haribtw, 2026-08-28)
- Update Chart.yaml (`eebae7e`, haribtw, 2026-08-28)
- changing default name of beyla (`bcf3276`, haribtw, 2026-08-28)
- changing default name of victoriametrics (`3ff961a`, haribtw, 2026-08-28)
- changing default name of spec controller (`452427e`, haribtw, 2026-08-28)
- changing default name of spec controller (`c7e645d`, haribtw, 2026-08-28)
- disabling sync and spark by default (`695e081`, haribtw, 2026-08-28)
- updating all the changes in chart (`1f82ca1`, arun-sedai, 2026-08-31)
- updating the smartagent version (`625b2ab`, Arun Ramesh, 2026-09-01)
- Renaming SedaiSync to PodInterceptor (`74c8c24`, Arun Ramesh, 2026-09-02)
- Renaming SedaiSync to PodInterceptor (`e17982b`, Arun Ramesh, 2026-09-02)
- Renaming SedaiSync to PodInterceptor (`3af8bad`, Arun Ramesh, 2026-09-02)
- permssions for cleanup (`a49bd5a`, Arun Ramesh, 2026-09-04)
- added fix to update prometheus url in server with self-provisioning url (`c8de4e3`, haribtw, 2026-09-02)
- Update Chart.yaml (`657a1c1`, arun-sedai, 2026-09-02)
- SED-22068: register the /mutate/workload webhook (`cdcf0a7`, Pooja Malik, 2026-09-02)
- Update Chart.yaml (`8deaf5d`, haribtw, 2026-09-02)
- SED-22632: pass the pod namespace to the agent (`6401f07`, John Daison Arikkat, 2026-09-03)
- updated images for scheduler (`5b13990`, Arun Ramesh, 2026-09-04)
- cleanup workflow (`a544086`, Arun Ramesh, 2026-09-05)
- Revert "cleanup workflow" (`bb3c7ff`, Arun Ramesh, 2026-09-05)
- Update values.yaml (`0a0ab40`, arun-sedai, 2026-09-04)
- Update Chart.yaml (`a9b616b`, arun-sedai, 2026-09-04)
- Update Chart.yaml (`e1bcb5e`, arun-sedai, 2026-09-04)
- Update values.yaml (`211f5ef`, arun-sedai, 2026-09-05)
- Update Chart.yaml (`e25c502`, arun-sedai, 2026-09-05)
- added deletion permission for mutationwebhook (`5edcea5`, haribtw, 2026-09-05)
- Update values.yaml (`78e2ef6`, arun-sedai, 2026-09-05)
- Update Chart.yaml (`fb337bd`, arun-sedai, 2026-09-05)
- Update values.yaml (`3cd1dd2`, arun-sedai, 2026-09-05)
- Update Chart.yaml (`81f5ac7`, arun-sedai, 2026-09-05)
- SED-22632: permit the scheduler's critical priority class (`f3e3331`, John Daison Arikkat, 2026-09-04)
- Grant the pod interceptor read access to argoproj.io for owner resolution (`87cc11b`, brian, 2026-09-06)
- rbac changes in duplicate check job (`ba33000`, Arun Ramesh, 2026-09-09)
- Update Chart.yaml (`4f4af83`, arun-sedai, 2026-09-09)
- priorityclass to spec-controller (`b108936`, Arun Ramesh, 2026-09-09)
- priorityclass to spec-controller (`d4a8c41`, Arun Ramesh, 2026-09-09)
- updating smartagent to 2.0.4 (`63054eb`, Arun Ramesh, 2026-09-09)
- Fix sideEffects declaration on pod-interceptor webhooks to NoneOnDryRun (`77323b4`, brian, 2026-09-09)
- updating smartagent to 2.0.5 (#61) (`c91c4ea`, pmaliksedai, 2026-09-09)
- added storageClass field for pod interceptor pvc (`ab78d93`, haribtw, 2026-09-09)
- updating agent (`3d05f54`, Arun Ramesh, 2026-09-10)
- using release namespace for spec controller cm (`60cc7fc`, haribtw, 2026-09-10)

## 1.4.75 — 2026-08-27

Version bumped in `e1f5145`.

- adding regex to allow *metrics.* for node exporter scraping; using 19100 (`fa0fb58`, haribtw, 2026-08-27)
- bumped chart version (`e1f5145`, haribtw, 2026-08-27)

## 1.4.74 — 2026-08-25

Version bumped in `cdde5af`.

- enabling forceCreate (`cdde5af`, haribtw, 2026-08-25)

## 1.4.73 — 2026-08-20

Version bumped in `dbe780a`.

- Update values.yaml (`4ee761c`, arun-sedai, 2026-08-20)
- Update Chart.yaml (`dbe780a`, arun-sedai, 2026-08-20)

## 1.4.72 — 2026-08-14

Version bumped in `b7fe1d4`.

- adding job to correct cluster names using gke metadata (`ba08265`, haribtw, 2026-08-14)
- increased chart version (`b7fe1d4`, haribtw, 2026-08-14)

## 1.4.71 — 2026-08-14

Version bumped in `39444da`.

- increased chart version (`39444da`, haribtw, 2026-08-14)

## 1.4.70 — 2026-08-12

Version bumped in `d3aaa30`.

- adding cleanup job for legacy migration (`d3aaa30`, haribtw, 2026-08-12)

## 1.4.69 — 2026-08-06

Version bumped in `268c49b`.

- Update Chart.yaml (`268c49b`, haribtw, 2026-08-06)

## 1.4.68 — 2026-08-06

Version bumped in `3a6c213`.

- updating to agent v1.25.50 (`3a6c213`, almira-khan, 2026-08-06)

## 1.4.67 — 2026-08-04

Version bumped in `4a7f3c6`.

- updating enroll job version to v3.1.17 (`23a6240`, haribtw, 2026-07-30)
- Update values.yaml (`25e5b76`, arun-sedai, 2026-08-04)
- Update Chart.yaml (`4a7f3c6`, arun-sedai, 2026-08-04)

## 1.4.66 — 2026-07-24

Version bumped in `6432973`.

- Update values.yaml (`e67b600`, arun-sedai, 2026-07-24)
- Update Chart.yaml (`6432973`, arun-sedai, 2026-07-24)

## 1.4.65 — 2026-07-24

Version bumped in `233130e`.

- updating agent version to v1.25.47 (`233130e`, haribtw, 2026-07-24)

## 1.4.64 — 2026-07-16

Version bumped in `5c8cc8a`.

- chore(prod): bump sedaiSync image to 0.1.2 (`6d8a84a`, sedai-ops-bot, 2026-06-25)
- chore(prod): bump sedaiSync image to 0.1.3 (`87a7746`, sedai-ops-bot, 2026-06-29)
- chore(prod): bump sedaiSync image to 0.1.4 (`b08028a`, sedai-ops-bot, 2026-06-30)
- updating smartaget image to v1.25.40 (`5c8cc8a`, arun-sedai, 2026-07-16)

## 1.4.63 — 2026-06-24

Version bumped in `2c6fd0d`.

- adding dev branch (`063ea22`, haribtw, 2026-06-24)
- SED-20872 Separate Mutating web-hook for Spark CRD in Spec Controller (`be6a34b`, abhinavkrishnav, 2026-06-09)
- Revert "Merge pull request #18 from SedaiEngineering/SED-20872-mutating-webhook-spark-crd" (`7564501`, abhinavkrishnav, 2026-06-22)
- triggering PR check for any change (`9f52a35`, haribtw, 2026-06-24)
- setting non-latest release for dev (`499d408`, haribtw, 2026-06-24)
- fixing latest flag (`62e2b5b`, haribtw, 2026-06-24)
- setting latest (`2c6fd0d`, haribtw, 2026-06-24)

## 1.4.62 — 2026-06-22

Version bumped in `19481ca`.

- using single flag for prometheus (`19481ca`, haribtw, 2026-06-22)

## 1.4.61 — 2026-06-19

Version bumped in `9881eb6`.

- relax timeouts and readiness; fix for SCS-934 (`9881eb6`, haribtw, 2026-06-19)

## 1.4.60 — 2026-06-11

Version bumped in `cf29cec`.

- fixed dropping container_network metrics (`cf29cec`, haribtw, 2026-06-11)

## 1.4.59 — 2026-06-10

Version bumped in `db5333f`.

- fixing victoriametrics svc name wrt workload name (`db5333f`, haribtw, 2026-06-10)

## 1.4.58 — 2026-06-10

Version bumped in `963e0e9`.

- using configurable name for victoriametrics (`963e0e9`, haribtw, 2026-06-10)

## 1.4.57 — 2026-06-10

Version bumped in `d8b3016`.

- Update values.yaml (`18d20dc`, arun-sedai, 2026-05-29)
- Update Chart.yaml (`85bdd2f`, arun-sedai, 2026-05-29)
- using configurable name for victoriametrics (`d8b3016`, haribtw, 2026-06-10)

## 1.4.56 — 2026-06-09

Version bumped in `34aea32`.

- adding sc support for prometheus and victoriametrics (`34aea32`, haribtw, 2026-06-09)

## 1.4.54 — 2026-05-25

Version bumped in `f26a1c2`.

- using same k8s auth for applying secrets (`f26a1c2`, haribtw, 2026-05-25)

## 1.4.53 — 2026-05-21

Version bumped in `bdfc385`.

- updating the image to v1.25.29 (`6e44d73`, arun-sedai, 2026-05-21)
- updating the image to v1.25.29 (`bdfc385`, arun-sedai, 2026-05-21)

## 1.4.52 — 2026-05-21

Version bumped in `02be603`.

- enroll job - added timeouts; using /lite endpoint to avoid slowness (`02be603`, haribtw, 2026-05-21)

## 1.4.51 — 2026-05-13

Version bumped in `741cbc5`.

- adding imagePullSecret field for all sa (`741cbc5`, haribtw, 2026-05-13)

## 1.4.50 — 2026-05-06

Version bumped in `49c5d83`.

- Vulnerability fix for SmartAgent (`49c5d83`, Vinod Sethumadhavan, 2026-05-06)

## 1.4.49 — 2026-05-05

Version bumped in `7555b81`.

- Drop unwanted labels to reduce scrape errors (`f0fbda0`, Vinod Sethumadhavan, 2026-05-02)
- Update smart agent to 20 and chart to 49 (#15) (`7555b81`, pmaliksedai, 2026-05-05)

## 1.4.48 — 2026-04-28

Version bumped in `5995ce8`.

- adding Gi support for agent JAVA_OPTIONS (`5995ce8`, haribtw, 2026-04-28)

## 1.4.47 — 2026-04-22

Version bumped in `a24896a`.

- adding strict fail if secret exists (`a24896a`, haribtw, 2026-04-22)

## 1.4.46 — 2026-04-22

Version bumped in `8de340f`.

- upgrading agent version to v1.25.24 (`8de340f`, haribtw, 2026-04-22)

## 1.4.45 — 2026-04-14

Version bumped in `44ae524`.

- reverting agent version (`44ae524`, haribtw, 2026-04-14)

## 1.4.44 — 2026-04-14

Version bumped in `5981d59`.

- chore(prod): bump sedaiSync image to 0.1.1 (`b68484a`, sedai-ops-bot, 2026-04-09)
- upgraded the agent versio (`5981d59`, haribtw, 2026-04-14)

## 1.4.43 — 2026-04-09

Version bumped in `b1c8a86`.

- chore(prod): bump sedaiSync image to 0.1.0 (`6da57d5`, sedai-ops-bot, 2026-04-06)
- adding RollingUpdate to prevent conflict with argocd (`b1c8a86`, haribtw, 2026-04-09)

## 1.4.42 — 2026-03-31

Version bumped in `8b54fa6`.

- upgrading components; setting low retention for vm (`d8957bc`, haribtw, 2026-03-27)
- adding workflow dispatch (`20aafb0`, haribtw, 2026-03-27)
- using latest busybox version (`8b54fa6`, haribtw, 2026-03-31)

## 1.4.41 — 2026-03-23

Version bumped in `191b1c3`.

- using vm instead of prom (`191b1c3`, haribtw, 2026-03-23)

## 1.4.40 — 2026-03-13

Version bumped in `bf17503`.

- upgrade agent version to v1.25.20 (`bf17503`, haribtw, 2026-03-13)

## 1.4.39 — 2026-03-10

Version bumped in `da584ef`.

- reduce retention for vm; increase default pvc size (`da584ef`, haribtw, 2026-03-10)

## 1.4.38 — 2026-03-09

Version bumped in `7bcd72b`.

- configurable resource name for beyla; mem improvement for prometheus and vm; fix istio + envoy scrape (`d7bb169`, haribtw, 2026-03-06)
- increased resources for vm (`c59a685`, haribtw, 2026-03-06)
- upgrade agent version to v1.25.19 (`7bcd72b`, haribtw, 2026-03-09)

## 1.4.37 — 2026-03-06

Version bumped in `62e932d`.

- upgraded helm chart version (`62e932d`, haribtw, 2026-03-06)

## 1.4.36 — 2026-02-26

Version bumped in `93dcb82`.

- REduced retention to 4h for SMP (`68e9616`, Vinod Sethumadhavan, 2026-02-24)
- adding http_ metrics; syncing vm scrape config with prom (`93dcb82`, haribtw, 2026-02-26)

## 1.4.35 — 2026-02-18

Version bumped in `5cd1d76`.

- using scrape interval - 1m (`5cd1d76`, haribtw, 2026-02-18)

## 1.4.34 — 2026-02-13

Version bumped in `c43262a`.

- Update values.yaml (`d38da92`, haribtw, 2026-02-13)
- Update Chart.yaml (`c43262a`, haribtw, 2026-02-13)

## 1.4.33 — 2026-02-10

Version bumped in `5bff34a`.

- adding custom scrape (`d4f1cbe`, haribtw, 2026-02-03)
- cleanup (`854220e`, haribtw, 2026-02-03)
- fixed daemonset metrics (`022c3df`, haribtw, 2026-02-04)
- upgraded dcgm version; added extra permissions for gpu-operator clusters; trimmed metrics (`fb92294`, haribtw, 2026-02-10)
- upgrading chart version (`5bff34a`, haribtw, 2026-02-10)

## 1.4.32 — 2026-02-04

Version bumped in `49bb973`.

- Update smart agent to 17 version (`18e2650`, pmaliksedai, 2026-02-03)
- Update Chart.yaml (`787a645`, pmaliksedai, 2026-02-03)
- upgraded agent version to v1.25.17 (`49bb973`, haribtw, 2026-02-04)

## 1.4.31 — 2026-02-04

Version bumped in `8ccd30e`.

- upgraded agent version to v1.25.17 (`ff445f8`, haribtw, 2026-02-04)
- upgraded agent version to v1.25.17 (`8ccd30e`, haribtw, 2026-02-04)

## 1.4.30 — 2026-02-02

Version bumped in `de83afa`.

- updated agent to v1.25.16 (`4b7c625`, haribtw, 2026-02-02)
- added dcgm metrics (`de83afa`, haribtw, 2026-02-02)

## 1.4.29 — 2026-02-02

Version bumped in `05f6f45`.

- added dcgm exporter (`05f6f45`, haribtw, 2026-02-02)

## 1.4.28 — 2026-01-30

Version bumped in `db07321`.

- SOT-386 Github runner upgrade (`7057f9a`, arun-sedai, 2026-01-14)
- adding port support for node exporter and beyla (`db07321`, haribtw, 2026-01-30)

## 1.4.27 — 2025-12-22

Version bumped in `41aa73c`.

- adding kube spec controller config; configmap permission (`41aa73c`, haribtw, 2025-12-22)

## 1.4.26 — 2025-12-10

Version bumped in `b801413`.

- upgrading prometheus components (`b801413`, haribtw, 2025-12-10)

## 1.4.25 — 2025-12-03

Version bumped in `3e2c8d9`.

- update agent to  v1.25.13 (`3e2c8d9`, haribtw, 2025-12-03)

## 1.4.24 — 2025-11-24

Version bumped in `b522dcd`.

- adding new cluster label for datadog (`b522dcd`, haribtw, 2025-11-24)

## 1.4.23 — 2025-11-21

Version bumped in `57d2476`.

- adding additional hooks / rbac to work with upgrade (`57d2476`, haribtw, 2025-11-21)

## 1.4.22 — 2025-11-20

Version bumped in `70dcbe4`.

- adding cleanup hooks for enroll job (`70dcbe4`, haribtw, 2025-11-20)

## 1.4.21 — 2025-11-14

Version bumped in `4f55089`.

- update agent to  v1.25.9 (`4f55089`, haribtw, 2025-11-14)

## 1.4.20 — 2025-11-13

Version bumped in `cbe9cfb`.

- Add permissions for mutating webhook configurations (`9eda1d4`, ajithsedai, 2025-11-13)
- Add permissions for mutating webhook configurations (`862cac0`, ajithsedai, 2025-11-13)
- improved comments (`cbe9cfb`, haribtw, 2025-11-13)

## 1.4.19 — 2025-11-11

Version bumped in `df6d3ce`.

- updated sync webhook; added env vars for sync (`df6d3ce`, haribtw, 2025-11-11)

## 1.4.18 — 2025-10-28

Version bumped in `7aa72a0`.

- updated image (`7aa72a0`, haribtw, 2025-10-28)

## 1.4.17 — 2025-10-27

Version bumped in `933fb11`.

- added gcp sa json support (`4ac5d5b`, haribtw, 2025-10-27)
- added gcp sa json support (`933fb11`, haribtw, 2025-10-27)

## 1.4.16 — 2025-10-22

Version bumped in `159ad17`.

- using post-delete for deregister job to work with argocd (`159ad17`, haribtw, 2025-10-22)

## 1.4.15 — 2025-10-22

Version bumped in `42e9a21`.

- using post-delete for cleanup job to work with argocd (`42e9a21`, haribtw, 2025-10-22)

## 1.4.12 — 2025-10-21

Version bumped in `b90319e`.

- added annotations (`b90319e`, haribtw, 2025-10-21)

## 1.4.11 — 2025-10-21

Version bumped in `13320db`.

- added cleanup and post upgrade jobs (`fd9e1a3`, haribtw, 2025-10-21)
- Update Chart.yaml (`13320db`, haribtw, 2025-10-21)

## 1.4.10 — 2025-10-16

Version bumped in `c21ade9`.

- upgraded to v1.25.8 (`c21ade9`, haribtw, 2025-10-16)

## 1.4.9 — 2025-10-16

Version bumped in `a66144c`.

- update rbac (`a66144c`, haribtw, 2025-10-16)

## 1.4.8 — 2025-10-15

Version bumped in `26a038a`.

- correct chart repo url in docs (`54f6892`, haribtw, 2025-10-15)
- ingress/sidecar metrics support (`de385d6`, dijeesh, 2025-10-15)
- ingress/sidecar metrics support (`26a038a`, dijeesh, 2025-10-15)

## 1.4.7 — 2025-10-09

Version bumped in `d276d5b`.

- updated enroll (`d276d5b`, haribtw, 2025-10-09)

## 1.4.6 — 2025-10-09

Version bumped in `e27f33f`.

- using oci chart (`dac3c3f`, haribtw, 2025-10-06)
- adding oidc permission (`cb46702`, haribtw, 2025-10-06)
- fixed chart location (`2e121b7`, haribtw, 2025-10-06)
- adding checkout actions (`dccf122`, haribtw, 2025-10-06)
- fixed chart location (`6f8709f`, haribtw, 2025-10-06)
- added global tolerations; registry url; removed ns dependency from values (`d1b689d`, haribtw, 2025-10-07)
- added priorityClassNameg (`da28d74`, haribtw, 2025-10-07)
- updating helm chart (`74083f0`, dijeesh, 2025-10-08)
- added gateway api (`f96f7fa`, haribtw, 2025-10-08)
- support for setting global registry; support for existing custom registries (`9a43c91`, haribtw, 2025-10-08)
- GCP fix; added dynatrace (`e27f33f`, haribtw, 2025-10-09)

## 1.4.5 — 2025-10-02

Version bumped in `28a7161`.

- examples and annotation (`b00975f`, dijeesh, 2025-10-01)
- examples and annotation (`564b3f7`, dijeesh, 2025-10-01)
- examples and annotation (`97f2763`, dijeesh, 2025-10-01)
- update job spec (`2456d39`, dijeesh, 2025-10-02)
- Add capability to bring in job specific annotations (`ab871b9`, Surya Vallabhaneni, 2025-10-01)
- Allow jobAnnotations, podAnnotations (`2066ca5`, Surya Vallabhaneni, 2025-10-01)
- allow annotations to be defined in pod and job (`b489112`, Surya Vallabhaneni, 2025-10-01)
- deploymentAnnotations cleanup (`8193028`, dijeesh, 2025-10-02)
- Update Chart.yaml (`28a7161`, haribtw, 2025-10-02)

## 1.4.4 — 2025-09-22

Version bumped in `b31688c`.

- updating smart agent release to latest (`48508e5`, pmaliksedai, 2025-09-18)
- upgraded agent version to v1.25.5 (`b31688c`, haribtw, 2025-09-22)

## 1.4.3 — 2025-09-18

Version bumped in `1e95a79`.

- Update sedai-smart-agent-deployment.yaml (`a248eba`, pmaliksedai, 2025-09-18)
- Update Chart.yaml to new version (`1e95a79`, pmaliksedai, 2025-09-18)

## 1.4.2 — 2025-09-10

Version bumped in `4dd527d`.

- added argo rollout permission (`4dd527d`, haribtw, 2025-09-10)

## 1.4.1 — 2025-09-09

Version bumped in `bd37a5b`.

- Update values.yaml to v1.24.53 (`f502670`, pmaliksedai, 2025-09-08)
- Update Chart.yaml (`bd37a5b`, haribtw, 2025-09-09)

## 1.4.0 — 2025-09-08

Version bumped in `b750a89`.

- deploying ksm along with alloy (`b750a89`, haribtw, 2025-09-08)

## 1.3.89 — 2025-09-08

Version bumped in `20a3479`.

- added grafana alloy + vm (`090ff34`, haribtw, 2025-07-30)
- added application to prometheus_export (`8e4b4b0`, haribtw, 2025-07-30)
- using prometheus.exporter.unix for node exporter metrics (`bb0daa8`, haribtw, 2025-07-30)
- added ksm scraping; restriction to per node scraping for some (`658ccd1`, haribtw, 2025-07-30)
- added grafana alloy + vm support (`0ea71e5`, haribtw, 2025-08-05)
- upgraded agent version to v1.24.44 (`9aff220`, haribtw, 2025-08-12)
- using VM as a replacement for prometheus (`655868c`, haribtw, 2025-08-20)
- updated chart version (`20a3479`, haribtw, 2025-09-08)

## 1.3.88 — 2025-08-12

Version bumped in `bd4c7c0`.

- upgraded agent version to v1.24.44 (`f57a15c`, haribtw, 2025-08-12)
- upgraded agent version to v1.24.44 (`bd4c7c0`, haribtw, 2025-08-12)

## 1.3.87 — 2025-08-06

Version bumped in `881130c`.

- fixed indendation (`881130c`, haribtw, 2025-08-06)

## 1.3.86 — 2025-08-06

Version bumped in `a5fe575`.

- added restrictions to container level (`a5fe575`, haribtw, 2025-08-06)

## 1.3.85 — 2025-07-30

Version bumped in `5b0929f`.

- upgraded agent version to v1.24.37 (`5b0929f`, haribtw, 2025-07-30)

## 1.3.84 — 2025-07-30

Version bumped in `26db127`.

- added application to prometheus_export (`26db127`, haribtw, 2025-07-30)

## 1.3.83 — 2025-07-28

Version bumped in `03e7ab2`.

- Update values.yaml to v0.0.4 Spec Controller (`7bce76d`, Rajat Krishna, 2025-07-23)
- added pods/resize (`03e7ab2`, haribtw, 2025-07-28)

## 1.3.82 — 2025-07-23

Version bumped in `c696917`.

- setting sync timeout to 1s (`c696917`, haribtw, 2025-07-23)

## 1.3.81 — 2025-07-23

Version bumped in `b291d72`.

- using sqlite instead of postgres (`b291d72`, haribtw, 2025-07-23)

## 1.3.80 — 2025-07-21

Version bumped in `fcbb8cc`.

- fixed vpa typo (`fcbb8cc`, haribtw, 2025-07-21)

## 1.3.79 — 2025-07-17

Version bumped in `a2a85fc`.

- added envDimensions for datadog (`a2a85fc`, haribtw, 2025-07-17)

## 1.3.78 — 2025-07-04

Version bumped in `76b4a59`.

- added support for cluster nickname (`6283bdb`, haribtw, 2025-07-17)
- Enroll 3.0.0 and kubernetes_master env (`f1730d6`, dijeesh, 2025-06-23)
- Enroll 3.0.0 and kubernetes_master env (`d91bb75`, dijeesh, 2025-06-23)
- Enroll 3.0.0 and kubernetes_master env (`a4ef5c1`, dijeesh, 2025-06-23)
- Update de-register job settings (`842053e`, dijeesh, 2025-06-23)
- Add global labels (`6e16798`, dijeesh, 2025-06-24)
- Enable support for AMP (`446996a`, dijeesh, 2025-06-26)
- Release smartagent v1.24.28 (`76b4a59`, dijeesh, 2025-07-04)

## 1.3.71 — 2025-06-19

Version bumped in `b7298c8`.

- updated beyla version and cfm (`b7298c8`, haribtw, 2025-06-19)

## 1.3.70 — 2025-06-19

Version bumped in `1e40ddc`.

- added tolerations and nodeselectors (`1e40ddc`, haribtw, 2025-06-19)

## 1.3.69 — 2025-06-19

Version bumped in `8d55207`.

- added support for datadog creds as secret (`8d55207`, haribtw, 2025-06-19)

## 1.3.68 — 2025-06-18

Version bumped in `bbfe543`.

- upgraded agent version to v1.24.22 (`bbfe543`, haribtw, 2025-06-18)

## 1.3.67 — 2025-06-17

Version bumped in `f560991`.

- fixed node exporter metrics (`f66a39b`, haribtw, 2025-06-17)
- upgraded enroll version (`f560991`, haribtw, 2025-06-17)

## 1.3.66 — 2025-06-17

Version bumped in `36e6578`.

- added beyla scrapeconfig (`36e6578`, haribtw, 2025-06-17)

## 1.3.65 — 2025-06-17

Version bumped in `d5cacfc`.

- added beyla and nodeexporter (`d5cacfc`, haribtw, 2025-06-17)

## 1.3.64 — 2025-06-13

Version bumped in `63b6ce4`.

- Set AutoPilot as default option (`63b6ce4`, dijeesh, 2025-06-13)

## 1.3.62 — 2025-06-13

Version bumped in `e00c751`.

- Release 1.3.62 (`e00c751`, dijeesh, 2025-06-13)

## 1.3.61 — 2025-06-13

Version bumped in `55819e1`.

- update Chart Name (`55819e1`, dijeesh, 2025-06-13)

## 1.3.60 — 2025-06-13

Version bumped in `ff8d624`.

- Support for Sedai RW/RO Roles (`ff8d624`, dijeesh, 2025-06-13)

## 1.3.51 — 2025-06-12

Version bumped in `5d336dd`.

- upgraded agent and sync version (`59bbf2c`, haribtw, 2025-06-12)
- upgraded agent to support mimir (`5d336dd`, haribtw, 2025-06-12)

## 1.3.50 — 2025-06-12

Version bumped in `de2139f`.

- Support for Mimi MP (`de2139f`, dijeesh, 2025-06-12)

## 1.3.26 — 2025-06-10

Version bumped in `e91f69e`.

- using namespace for pass (`e91f69e`, haribtw, 2025-06-10)

## 1.3.25 — 2025-06-10

Version bumped in `5db3aee`.

- Add support for Newrelic (`5db3aee`, dijeesh, 2025-06-10)

## 1.3.23 — 2025-06-10

Version bumped in `7577c9e`.

- modified db pass (`3927699`, haribtw, 2025-06-10)
- disabled managed prometheus by default (`7577c9e`, haribtw, 2025-06-10)

## 1.3.22 — 2025-06-10

Version bumped in `4366e1d`.

- modified db pass (`4366e1d`, haribtw, 2025-06-10)

## 1.3.21 — 2025-06-09

Version bumped in `4f363d5`.

- disable autoupdate (`4f363d5`, haribtw, 2025-06-09)

## 1.3.20 — 2025-06-07

Version bumped in `478d811`.

- imagepull secrts for airgapped installations (`478d811`, dijeesh, 2025-06-07)

## 1.3.16 — 2025-06-06

Version bumped in `5f89676`.

- Release 1.3.16 with postgres upgrade and enrollJob  2.3.1 (`5f89676`, dijeesh, 2025-06-06)

## 1.3.14 — 2025-06-04

Version bumped in `351508e`.

- update values file with detailed instruction (`351508e`, dijeesh, 2025-06-04)

## 1.3.13 — 2025-05-29

Version bumped in `96427e6`.

- added sa for sync (`5a3d067`, haribtw, 2025-05-23)
- updated agent image (`96427e6`, haribtw, 2025-05-29)

## 1.3.12 — 2025-05-23

Version bumped in `8b37e86`.

- testing securityContext for sync (`e4d51ae`, haribtw, 2025-05-22)
- fixed indentation (`8e97258`, haribtw, 2025-05-22)
- fixed indentation (`f8a7103`, haribtw, 2025-05-22)
- using postgres user for db (`c45706b`, haribtw, 2025-05-22)
- removed fsgroup from sts (`3d1879e`, haribtw, 2025-05-22)
- added fsgroup to pod level for DB (`707ddcf`, haribtw, 2025-05-22)
- added sa for sync (`8b37e86`, haribtw, 2025-05-23)

## 1.3.11 — 2025-05-22

Version bumped in `bd9cd1d`.

- upgraded agent version to v1.24.12 (`01f422d`, haribtw, 2025-05-21)
- setting busybox version to 1.37 (`c86dd75`, haribtw, 2025-05-21)
- testing securityContext for sync (`bd9cd1d`, haribtw, 2025-05-22)

## 1.3.10 — 2025-05-21

Version bumped in `50148fc`.

- added sync enable env var (`fdc664e`, haribtw, 2025-05-21)
- setting version to 1.3.10 (`50148fc`, haribtw, 2025-05-21)

## 1.3.11 — 2025-05-21

Version bumped in `6e0f829`.

- moved tls secret (`d1a231e`, haribtw, 2025-05-19)
- corrected forcecreate env var (`1b52377`, haribtw, 2025-05-19)
- Update Kube Spec Controller tag (`dbd3df7`, Rajat Krishna, 2025-05-20)
- upgraded version (`6e0f829`, haribtw, 2025-05-21)

## 1.3.10 — 2025-05-19

Version bumped in `2660e57`.

- added sync; added option to force create resources (`2660e57`, haribtw, 2025-05-19)

## 1.3.9 — 2025-05-07

Version bumped in `2e2131b`.

- Update template structure (`2e2131b`, dijeesh, 2025-05-07)

## 1.3.8 — 2025-05-06

Version bumped in `c2cde5e`.

- setting resources to prometheus (`e2681bd`, haribtw, 2025-05-06)
- setting resources to prometheus (`816546d`, haribtw, 2025-05-06)
- adjusted livez port (`f5fc53b`, haribtw, 2025-05-06)
- Support for External Secrets (`311bc03`, dijeesh, 2025-05-06)
- updating version (`c2cde5e`, haribtw, 2025-05-06)

## 1.3.7 — 2025-05-06

Version bumped in `e36b9b8`.

- set resource limits for prometheus (`e36b9b8`, dijeesh, 2025-05-06)

## 1.3.6 — 2025-05-06

Version bumped in `8c538ed`.

- retention reduced to 12h; removed kubernetes-services and kubernetes-pods jobs (`801c48a`, haribtw, 2025-05-06)
- increased resources for KSM (`64de38a`, haribtw, 2025-05-06)
- remove duplicate file (`db42065`, dijeesh, 2025-05-06)
- remove duplicates (`8d73984`, dijeesh, 2025-05-06)
- Disable SedaiManaged Prometheus by Default (`8c538ed`, dijeesh, 2025-05-06)

## 1.3.5 — 2025-05-05

Version bumped in `6a3ca0f`.

- updated chart to v1.2.0 (`6a3ca0f`, haribtw, 2025-05-05)

## 1.3.2 — 2025-04-25

Version bumped in `de02a10`.

- Initial commit (`1c90a89`, haribtw, 2025-04-25)
- added agent enroll chart (`de02a10`, haribtw, 2025-04-25)

