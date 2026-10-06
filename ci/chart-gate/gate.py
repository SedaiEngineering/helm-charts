#!/usr/bin/env python3
"""Install gate for charts/sedai-smart-agent.

  gate.py static                 render checks, no cluster: lint, every supported k8s minor, the
                                 expected resources and RBAC per profile, every image resolves
  gate.py golden                 rewrite expected/<profile>.txt and expected/<profile>.rbac.txt
  gate.py install --profile P    real install into a throwaway k3d cluster, against an in-cluster
                                 mock of the Sedai API: enroll hooks, monitoring providers, every
                                 workload Ready, agent health + version, spec-controller webhooks
                                 answering admission, one discovery round, uninstall hooks

Needs python3 + PyYAML, helm 4, kubectl, openssl and k3d + Docker (install only). Artifacts (hook
logs, pod logs, mock state, diagnostics) go to --artifacts. Exit code is non-zero when any check fails.
"""
import argparse
import base64
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CHART = HERE.parents[1] / "charts" / "sedai-smart-agent"
GATE_VALUES = HERE / "values" / "gate.yaml"
PROFILES = HERE / "profiles"
EXPECTED = HERE / "expected"

RELEASE = "sedai-smart-agent"
NAMESPACE = "sedai"
MOCK_NS = "chart-gate-mock"
MOCK_URL = f"http://mock-core.{MOCK_NS}.svc.cluster.local:8080"
FIXTURE_NS = "chart-gate-fixtures"
ACCOUNT_ID = "chart-gate-account"
AGENT_SECRET = "sedai-smart-agent"
# values/gate.yaml. They differ on purpose: enroll names the account after the nickName, and every
# hook that looks the account up again has to agree with it.
CLUSTER_NAME = "chart-gate"
NICK_NAME = "chart-gate-nick"

# The chart maps scheduler/compactor images per k8s minor for 1.26-1.36; render every one of them.
KUBE_MINORS = list(range(26, 37))
# The minor the install runs on and the expected lists are rendered at.
CLUSTER_MINOR = 36
K3S_IMAGE = os.environ.get("CHART_GATE_K3S_IMAGE", "rancher/k3s:v1.36.5-k3s1")

# Delivered to the agent through the Secret the mock serves (the agent reads it via envFrom).
AGENT_ENV = {
    # The agent image bakes SPRING_PROFILES_ACTIVE='prod' with literal quotes, which Spring rejects;
    # the Secret Sedai issues overrides it, so the mock's Secret does too.
    "SPRING_PROFILES_ACTIVE": "prod",
    # The default log4j2 config ships logs to the hosted Loki gateway; keep CI logs in the cluster.
    "LOKI_HOST": "127.0.0.1",
    # One deterministic discovery round shortly after startup; raw discovery out of the window.
    "SCHEDULER_TOPOLOGY_INITIALDELAYMILLIS": "20000",
    "SCHEDULER_TOPOLOGY_RAW_INITIALDELAYMILLIS": "86400000",
}

WORKLOAD_KINDS = ("Deployment", "StatefulSet", "DaemonSet")
POD_TEMPLATE_KINDS = WORKLOAD_KINDS + ("Job", "CronJob", "Pod")


# ---------------------------------------------------------------------------------------------
# plumbing
# ---------------------------------------------------------------------------------------------
def _gh_escape(text, prop=False):
    text = str(text).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return text.replace(":", "%3A").replace(",", "%2C") if prop else text


class Report:
    def __init__(self, title):
        self.title = title
        self.checks = []

    def add(self, name, ok, detail=""):
        self.checks.append((name, bool(ok), detail))
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""), flush=True)
        if not ok and os.environ.get("GITHUB_ACTIONS"):
            print(f"::error title={_gh_escape('chart-gate: ' + name, prop=True)}::{_gh_escape(detail or name)}",
                  flush=True)
        return ok

    @property
    def failed(self):
        return [c for c in self.checks if not c[1]]

    def write_summary(self):
        lines = [f"### {self.title}", "", "| | check | detail |", "|---|---|---|"]
        for name, ok, detail in self.checks:
            detail = str(detail).replace("|", "\\|").replace("\n", "<br>")
            lines.append(f"| {'✅' if ok else '❌'} | {name} | {detail} |")
        text = "\n".join(lines) + "\n\n"
        path = os.environ.get("GITHUB_STEP_SUMMARY")
        if path:
            with open(path, "a") as fh:
                fh.write(text)
        return text


def log(msg):
    print(f"[chart-gate {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run(cmd, check=True, timeout=None, env=None, input_text=None):
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, input=input_text)
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, proc.stdout, proc.stderr)
    return proc


class Kube:
    def __init__(self, kubeconfig):
        self.env = {**os.environ, "KUBECONFIG": str(kubeconfig)}

    def kubectl(self, *args, check=True, timeout=120, input_text=None):
        return run(["kubectl", *args], check=check, timeout=timeout, env=self.env, input_text=input_text)

    def helm(self, *args, check=True, timeout=None):
        return run(["helm", *args], check=check, timeout=timeout, env=self.env)

    def _read(self, args, missing_ok):
        """Reads retry through transient apiserver errors; only NotFound may mean 'absent'."""
        last = None
        for attempt in range(5):
            try:
                proc = self.kubectl(*args, check=False, timeout=60)
            except subprocess.TimeoutExpired as err:
                last = f"timeout: {err}"
            else:
                if proc.returncode == 0:
                    return proc.stdout
                if missing_ok and ("NotFound" in proc.stderr or "not found" in proc.stderr):
                    return None
                last = proc.stderr.strip()
            time.sleep(3 * (attempt + 1))
        raise RuntimeError(f"kubectl {' '.join(args)} kept failing: {last}")

    def get_json(self, *args, missing_ok=False):
        out = self._read(["get", *args, "-o", "json"], missing_ok)
        return json.loads(out) if out is not None else None

    def raw(self, path, missing_ok=False):
        return self._read(["get", "--raw", path], missing_ok)


def profiles():
    return sorted(p.stem for p in PROFILES.glob("*.yaml"))


def profile_expect(profile):
    return json.loads((PROFILES / f"{profile}.expect.json").read_text())


def installable_profiles():
    return [p for p in profiles() if profile_expect(p).get("install", True)]


def values_args(profile):
    return ["-f", str(GATE_VALUES), "-f", str(PROFILES / f"{profile}.yaml")]


# ---------------------------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------------------------
def render(profile, minor):
    proc = run(["helm", "template", RELEASE, str(CHART), "-n", NAMESPACE, *values_args(profile),
                "--set", "sedaiIntegrationSettings.sedaiApiToken=render-only",
                "--kube-version", f"1.{minor}.0"], check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"helm template failed (profile {profile}, k8s 1.{minor}):\n{proc.stderr.strip()}")
    return [d for d in yaml.safe_load_all(proc.stdout) if isinstance(d, dict) and d.get("kind")]


def resource_key(doc):
    meta = doc.get("metadata") or {}
    hook = (meta.get("annotations") or {}).get("helm.sh/hook")
    key = f"{doc['kind']}/{meta.get('name', '<no-name>')}"
    return f"{key}  [hook: {hook}]" if hook else key


def pod_spec(doc):
    spec = doc.get("spec") or {}
    if doc["kind"] == "Pod":
        return spec
    if doc["kind"] == "CronJob":
        spec = ((spec.get("jobTemplate") or {}).get("spec")) or {}
    return ((spec.get("template") or {}).get("spec")) or {}


def images_of(doc):
    if doc["kind"] not in POD_TEMPLATE_KINDS:
        return []
    spec = pod_spec(doc)
    return [c["image"] for c in (spec.get("initContainers") or []) + (spec.get("containers") or []) if c.get("image")]


def rbac_lines(docs):
    """Effective permissions per ServiceAccount the release binds: one line per rule, so any added
    or removed permission shows up as a diff, including on hook ServiceAccounts that are gone after
    install."""
    roles = {(d["kind"], d["metadata"]["name"]): d.get("rules") or []
             for d in docs if d["kind"] in ("Role", "ClusterRole")}
    lines = set()
    for binding in (d for d in docs if d["kind"] in ("RoleBinding", "ClusterRoleBinding")):
        ref = binding.get("roleRef") or {}
        scope = "cluster" if binding["kind"] == "ClusterRoleBinding" else \
            f"namespace {binding['metadata'].get('namespace', NAMESPACE)}"
        for subject in binding.get("subjects") or []:
            if subject.get("kind") != "ServiceAccount":
                continue
            who = f"{subject.get('namespace', NAMESPACE)}/{subject['name']}"
            rules = roles.get((ref.get("kind"), ref.get("name")))
            if rules is None:
                lines.add(f"{who} | {scope} | bound to {ref.get('kind')}/{ref.get('name')} (not in the chart)")
                continue
            for rule in rules:
                if rule.get("nonResourceURLs"):
                    what = "urls " + ",".join(sorted(rule["nonResourceURLs"]))
                else:
                    groups = ",".join(sorted(g or "core" for g in rule.get("apiGroups") or [""]))
                    what = f"{groups} {','.join(sorted(rule.get('resources') or []))}"
                    if rule.get("resourceNames"):
                        what += f" names={','.join(sorted(rule['resourceNames']))}"
                lines.add(f"{who} | {scope} | {what} | {','.join(sorted(rule.get('verbs') or []))}")
    return sorted(lines)


# ---------------------------------------------------------------------------------------------
# image resolution (anonymous registry v2 API — what a cluster without pull secrets can pull)
# ---------------------------------------------------------------------------------------------
MANIFEST_ACCEPT = ", ".join([
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
])
_TOKENS = {}


def split_image(ref):
    name, _, digest = ref.partition("@")
    slash, colon = name.rfind("/"), name.rfind(":")
    repo, tag = (name[:colon], name[colon + 1:]) if colon > slash else (name, "latest")
    first = repo.split("/")[0]
    if "." in first or ":" in first or first == "localhost":
        registry, path = first, repo[len(first) + 1:]
    else:
        registry, path = "registry-1.docker.io", repo if "/" in repo else f"library/{repo}"
    if registry == "docker.io":
        registry = "registry-1.docker.io"
    return registry, path, digest or tag


def _anonymous_token(challenge, path):
    params = dict(re.findall(r'(\w+)="([^"]*)"', challenge))
    if not params.get("realm"):
        raise ValueError(f"401 without a token realm ({challenge})")
    query = f"service={params.get('service', '')}&scope=repository:{path}:pull"
    with urllib.request.urlopen(f"{params['realm']}?{query}", timeout=30) as resp:
        body = json.load(resp)
    return body.get("token") or body.get("access_token")


def image_resolves(ref):
    registry, path, reference = split_image(ref)
    url = f"https://{registry}/v2/{path}/manifests/{reference}"
    last = None
    for attempt in range(5):
        headers = {"Accept": MANIFEST_ACCEPT}
        if (registry, path) in _TOKENS:
            headers["Authorization"] = f"Bearer {_TOKENS[(registry, path)]}"
        try:
            urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers=headers), timeout=30)
            return True, ""
        except urllib.error.HTTPError as err:
            if err.code == 401 and (registry, path) not in _TOKENS:
                try:
                    _TOKENS[(registry, path)] = _anonymous_token(err.headers.get("WWW-Authenticate", ""), path)
                    continue
                except (urllib.error.URLError, OSError, ValueError) as tok_err:
                    last = f"token: {tok_err!r}"
            elif err.code in (401, 403, 404):
                return False, f"HTTP {err.code} for {url}"
            else:
                last = f"HTTP {err.code}"
                retry_after = err.headers.get("Retry-After", "")
                if err.code == 429 and retry_after.isdigit():
                    time.sleep(min(int(retry_after), 30))
        except (urllib.error.URLError, OSError) as err:
            last = repr(err)
        time.sleep(2 * (attempt + 1))
    return False, f"unreachable after retries: {last}"


# ---------------------------------------------------------------------------------------------
# static tier
# ---------------------------------------------------------------------------------------------
def _expected_file(profile, kind):
    return EXPECTED / (f"{profile}.txt" if kind == "resources" else f"{profile}.rbac.txt")


def _read_expected(path):
    return {l for l in path.read_text().splitlines() if l.strip() and not l.startswith("#")}


def cmd_golden(_args):
    EXPECTED.mkdir(exist_ok=True)
    for profile in profiles():
        docs = render(profile, CLUSTER_MINOR)
        for kind, lines in (("resources", sorted(resource_key(d) for d in docs)), ("rbac", rbac_lines(docs))):
            path = _expected_file(profile, kind)
            what = "Resources" if kind == "resources" else \
                "Permissions per ServiceAccount (account | scope | apiGroups resources | verbs)"
            path.write_text(f"# {what} that charts/sedai-smart-agent renders for ci/chart-gate/profiles/{profile}.yaml "
                            f"(k8s 1.{CLUSTER_MINOR}).\n# Regenerate after an intended chart change: "
                            f"python3 ci/chart-gate/gate.py golden\n" + "\n".join(lines) + "\n")
            log(f"wrote {path.relative_to(HERE.parents[1])} ({len(lines)} lines)")
    return 0


def _diff_detail(expected, actual, path):
    missing, unexpected = sorted(expected - actual), sorted(actual - expected)
    if not missing and not unexpected:
        return ""
    return (f"missing: {missing} unexpected: {unexpected} — if the change is intended, run "
            f"python3 ci/chart-gate/gate.py golden and commit {path.relative_to(HERE.parents[1])}")


def cmd_static(_args):
    report = Report("chart-gate: render checks")
    for profile in profiles():
        proc = run(["helm", "lint", "--strict", str(CHART), *values_args(profile),
                    "--set", "sedaiIntegrationSettings.sedaiApiToken=render-only"], check=False)
        report.add(f"helm lint --strict ({profile})", proc.returncode == 0,
                   "" if proc.returncode == 0 else (proc.stdout + proc.stderr).strip()[-1500:])

    all_images = set()
    for profile in profiles():
        renders, errors = {}, []
        for minor in KUBE_MINORS:
            try:
                renders[minor] = render(profile, minor)
            except RuntimeError as err:
                errors.append(str(err))
        report.add(f"helm template on k8s 1.{KUBE_MINORS[0]}–1.{KUBE_MINORS[-1]} ({profile})", not errors,
                   "\n".join(errors)[-1500:])
        if CLUSTER_MINOR not in renders:
            continue
        for docs in renders.values():
            for doc in docs:
                all_images.update(images_of(doc))

        # Same resource set on every supported minor: catches a component silently not rendering.
        base = {resource_key(d) for d in renders[CLUSTER_MINOR]}
        drift = []
        for minor, docs in renders.items():
            keys = {resource_key(d) for d in docs}
            if keys != base:
                drift.append(f"1.{minor}: missing {sorted(base - keys)} unexpected {sorted(keys - base)}")
        report.add(f"same resources on every supported k8s minor ({profile})", not drift, "; ".join(drift)[-1500:])

        # Exactly the expected resources and permissions: no more, no less.
        for kind, actual in (("resources", base), ("rbac", set(rbac_lines(renders[CLUSTER_MINOR])))):
            path = _expected_file(profile, kind)
            label = "expected resource list" if kind == "resources" else "expected RBAC per ServiceAccount"
            if not path.exists():
                report.add(f"{label} ({profile})", False,
                           f"{path.name} missing — run: python3 ci/chart-gate/gate.py golden")
                continue
            detail = _diff_detail(_read_expected(path), actual, path)
            report.add(f"{label} ({profile}, {len(actual)} lines)", not detail, detail)

    unresolved = []
    for image in sorted(all_images):
        ok, why = image_resolves(image)
        if not ok:
            unresolved.append(f"{image}: {why}")
    report.add(f"every rendered image resolves ({len(all_images)} images)", not unresolved, "\n".join(unresolved))
    print(report.write_summary())
    return 1 if report.failed else 0


# ---------------------------------------------------------------------------------------------
# install tier
# ---------------------------------------------------------------------------------------------
class GateError(Exception):
    pass


def wait_for(what, fn, timeout, interval=5):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            result = fn()
            if result:
                return result
        except Exception as err:  # keep polling; report the last error on timeout
            last = err
        time.sleep(interval)
    raise GateError(f"timed out after {timeout}s waiting for {what}" + (f" (last error: {last})" if last else ""))


class HookLogCollector(threading.Thread):
    """Hook Jobs delete their pods as soon as they finish, so stream every hook pod's logs while it
    runs, and remember the worst phase and exit code each pod reached."""

    def __init__(self, kube, out_dir):
        super().__init__(daemon=True)
        self.kube, self.out_dir = kube, out_dir
        self.stop_event = threading.Event()
        self.pods = {}  # name -> {"phase": worst phase, "exit_codes": set}
        self.streams = {}
        out_dir.mkdir(parents=True, exist_ok=True)

    def run(self):
        while not self.stop_event.is_set():
            try:
                self.sweep()
            except Exception as err:  # never let one bad read end collection
                log(f"hook log sweep error: {err}")
            self.stop_event.wait(1)
        try:
            self.sweep()
        except Exception:
            pass
        for stream in self.streams.values():
            stream.join(timeout=15)

    def sweep(self):
        proc = self.kube.kubectl("get", "pods", "-n", NAMESPACE, "-l", "job-name", "-o", "json",
                                 check=False, timeout=30)
        if proc.returncode != 0:
            return
        for pod in json.loads(proc.stdout).get("items", []):
            name = pod["metadata"]["name"]
            seen = self.pods.setdefault(name, {"phase": None, "exit_codes": set()})
            phase = pod.get("status", {}).get("phase")
            if seen["phase"] != "Failed":
                seen["phase"] = phase
            for cs in pod.get("status", {}).get("containerStatuses", []) + \
                    pod.get("status", {}).get("initContainerStatuses", []):
                for state in (cs.get("state") or {}, cs.get("lastState") or {}):
                    term = state.get("terminated")
                    if term:
                        seen["exit_codes"].add(term.get("exitCode"))
            if name not in self.streams and phase != "Pending":
                stream = threading.Thread(target=self.stream, args=(name,), daemon=True)
                self.streams[name] = stream
                stream.start()

    def stream(self, pod):
        target = self.out_dir / f"{pod}.log"
        for _ in range(30):
            proc = self.kube.kubectl("logs", "-f", "-n", NAMESPACE, pod, "--all-containers", "--timestamps",
                                     check=False, timeout=900)
            if proc.stdout and (not target.exists() or len(proc.stdout) >= target.stat().st_size):
                target.write_text(proc.stdout)
            if proc.returncode == 0 or "NotFound" in proc.stderr or "not found" in proc.stderr:
                return
            time.sleep(1)

    def stop(self):
        self.stop_event.set()
        self.join(timeout=60)

    def logs(self):
        return {p.stem: p.read_text() for p in self.out_dir.glob("*.log")}


class MemorySampler(threading.Thread):
    """Samples the host's memory and commit accounting every 10s, so a process the kernel refuses
    memory to (as opposed to one the kubelet OOM-kills) can be tied to what the host had left. On a
    Linux runner that is this machine's /proc; elsewhere (Docker Desktop) it is read via the node."""

    FIELDS = ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree", "CommitLimit", "Committed_AS")

    def __init__(self, node, out_file):
        super().__init__(daemon=True)
        self.node, self.out_file = node, out_file
        self.stop_event = threading.Event()

    def read(self):
        script = ("cat /proc/sys/vm/overcommit_memory /proc/sys/vm/overcommit_ratio; "
                  "grep -E '^(" + "|".join(self.FIELDS) + "):' /proc/meminfo")
        cmd = ["sh", "-c", script] if Path("/proc/meminfo").exists() else ["docker", "exec", self.node, "sh", "-c", script]
        lines = run(cmd, check=False, timeout=30).stdout.split("\n")
        values = dict(re.findall(r"^(\w+):\s+(\d+)", "\n".join(lines[2:]), re.MULTILINE))
        return lines[0].strip(), lines[1].strip(), values

    def run(self):
        with open(self.out_file, "w") as fh:
            first = True
            while True:
                try:
                    mode, ratio, values = self.read()
                    if first:
                        fh.write(f"# vm.overcommit_memory={mode} vm.overcommit_ratio={ratio}; values in MiB\n")
                        fh.write("time\t" + "\t".join(self.FIELDS) + "\n")
                        first = False
                    fh.write(time.strftime("%H:%M:%S") + "\t" +
                             "\t".join(str(int(values.get(f, 0)) // 1024) for f in self.FIELDS) + "\n")
                    fh.flush()
                except Exception as err:
                    fh.write(f"# sample failed: {err}\n")
                if self.stop_event.wait(10):
                    return

    def stop(self):
        self.stop_event.set()
        self.join(timeout=30)


class Install:
    def __init__(self, args):
        self.profile = args.profile
        self.cluster = args.cluster_name or f"chart-gate-{self.profile}"
        self.keep = args.keep_cluster
        self.art = Path(args.artifacts).resolve() / self.profile
        self.art.mkdir(parents=True, exist_ok=True)
        self.kubeconfig = self.art / "kubeconfig"
        self.kube = Kube(self.kubeconfig)
        self.enroll_token = secrets.token_hex(16)
        self.agent_token = secrets.token_hex(16)
        self.expect = profile_expect(self.profile)
        self.report = Report(f"chart-gate: install ({self.profile})")
        self.manifest = []
        self.hook_dir = self.art / "hooks"

    # -- cluster ------------------------------------------------------------------------------
    def cluster_up(self):
        run(["k3d", "cluster", "delete", self.cluster], check=False, timeout=300)
        log(f"creating k3d cluster {self.cluster} ({K3S_IMAGE})")
        run(["k3d", "cluster", "create", self.cluster, "--image", K3S_IMAGE, "--servers", "1", "--agents", "0",
             "--no-lb", "--wait", "--timeout", "300s",
             "--k3s-arg", "--disable=traefik@server:0", "--k3s-arg", "--disable=metrics-server@server:0",
             "--kubeconfig-update-default=false", "--kubeconfig-switch-context=false"], timeout=420)
        self.kubeconfig.write_text(run(["k3d", "kubeconfig", "get", self.cluster]).stdout)
        self.kubeconfig.chmod(0o600)
        wait_for("node Ready", lambda: all(
            any(c["type"] == "Ready" and c["status"] == "True" for c in n["status"]["conditions"])
            for n in self.kube.get_json("nodes")["items"]), 180)
        wait_for("default StorageClass", lambda: any(
            (sc["metadata"].get("annotations") or {}).get("storageclass.kubernetes.io/is-default-class") == "true"
            for sc in self.kube.get_json("storageclass")["items"]), 180)
        self.kube.kubectl("rollout", "status", "-n", "kube-system", "deployment/coredns", "--timeout=180s", timeout=200)

    def cluster_down(self):
        if self.keep:
            log(f"keeping cluster {self.cluster}; KUBECONFIG={self.kubeconfig}")
            return
        run(["k3d", "cluster", "delete", self.cluster], check=False, timeout=300)

    # -- mock Sedai API + fixtures ---------------------------------------------------------
    def deploy_mock(self):
        log("deploying mock Sedai API")
        k = self.kube
        k.kubectl("create", "namespace", MOCK_NS)
        k.kubectl("create", "configmap", "mock-core-script", "-n", MOCK_NS,
                  f"--from-file=mock_core.py={HERE / 'mock-core' / 'mock_core.py'}")
        k.kubectl("create", "secret", "generic", "mock-core-config", "-n", MOCK_NS,
                  f"--from-literal=GATE_ENROLL_TOKEN={self.enroll_token}",
                  f"--from-literal=GATE_AGENT_TOKEN={self.agent_token}",
                  f"--from-literal=GATE_SELF_URL={MOCK_URL}",
                  f"--from-literal=GATE_ACCOUNT_ID={ACCOUNT_ID}",
                  f"--from-literal=GATE_AGENT_ENV={json.dumps(AGENT_ENV)}")
        k.kubectl("apply", "-f", str(HERE / "mock-core" / "mock-core.yaml"))
        k.kubectl("rollout", "status", "-n", MOCK_NS, "deployment/mock-core", "--timeout=180s", timeout=200)

    def mock_state(self):
        return json.loads(self.kube.raw(f"/api/v1/namespaces/{MOCK_NS}/services/mock-core:8080/proxy/gate/state"))

    def apply_fixtures(self):
        log("applying discovery fixtures")
        self.kube.kubectl("apply", "-f", str(HERE / "fixtures" / "workloads.yaml"))

    # -- helm -------------------------------------------------------------------------------
    def _check_hooks(self, collector, stage):
        failed = sorted(f"{name} (phase {info['phase']}, exit codes {sorted(c for c in info['exit_codes'] if c)})"
                        for name, info in collector.pods.items()
                        if info["phase"] == "Failed" or any(info["exit_codes"] - {0}))
        self.report.add(f"no {stage} hook pod failed, including retried attempts", not failed,
                        f"failed: {failed}" if failed else f"{len(collector.pods)} hook pod(s)")
        denied = sorted(name for name, text in collector.logs().items()
                        if re.search(r"forbidden|\(status 403\)", text, re.IGNORECASE))
        self.report.add(f"no RBAC denial in {stage} hook logs", not denied,
                        f"Forbidden / 403 in: {denied}" if denied else "")

    def helm_install(self):
        log(f"helm install {RELEASE} from {CHART.relative_to(HERE.parents[1])} (profile {self.profile})")
        collector = HookLogCollector(self.kube, self.hook_dir)
        collector.start()
        started = time.time()
        try:
            proc = self.kube.helm("install", RELEASE, str(CHART), "-n", NAMESPACE, "--create-namespace",
                                  *values_args(self.profile),
                                  "--set", f"sedaiIntegrationSettings.sedaiApiToken={self.enroll_token}",
                                  "--wait=watcher", "--wait-for-jobs", "--timeout", "12m", check=False, timeout=900)
        finally:
            collector.stop()
        took = int(time.time() - started)
        (self.art / "helm-install.log").write_text(proc.stdout + proc.stderr)
        self.report.add("helm install (hooks + --wait=watcher --wait-for-jobs)", proc.returncode == 0,
                        f"{took}s" + ("" if proc.returncode == 0 else f"; {proc.stderr.strip()[-1200:]}"))
        self._check_hooks(collector, "install")
        if proc.returncode != 0:
            raise GateError("helm install failed")
        self.manifest = [d for d in yaml.safe_load_all(
            self.kube.helm("get", "manifest", RELEASE, "-n", NAMESPACE).stdout) if isinstance(d, dict) and d.get("kind")]
        status = json.loads(self.kube.helm("status", RELEASE, "-n", NAMESPACE, "-o", "json").stdout)
        self.report.add("release status deployed", status["info"]["status"] == "deployed", status["info"]["status"])

    def helm_uninstall(self):
        log("helm uninstall (post-delete hooks)")
        collector = HookLogCollector(self.kube, self.hook_dir)
        collector.start()
        try:
            proc = self.kube.helm("uninstall", RELEASE, "-n", NAMESPACE, "--wait", "--timeout", "5m",
                                  check=False, timeout=420)
        finally:
            collector.stop()
        (self.art / "helm-uninstall.log").write_text(proc.stdout + proc.stderr)
        self.report.add("helm uninstall", proc.returncode == 0, proc.stderr.strip()[-800:])
        self._check_hooks(collector, "uninstall")
        state = self.mock_state()
        if self.expect["deregister"]:
            self.report.add("deregister hook deleted the Sedai account", state["account_deletes"] == [ACCOUNT_ID],
                            f"DELETE calls: {state['account_deletes']}")
        else:
            self.report.add("cleanup hook left the Sedai account alone", state["account_deletes"] == [],
                            f"DELETE calls: {state['account_deletes']}")
        secret = self.kube.get_json("secret", AGENT_SECRET, "-n", NAMESPACE, missing_ok=True)
        self.report.add("uninstall hook deleted the agent Secret", secret is None,
                        "" if secret is None else f"Secret {AGENT_SECRET} still present")
        try:
            wait_for("release pods gone", lambda: not self.kube.get_json("pods", "-n", NAMESPACE)["items"], 180)
            self.report.add("no pods left after uninstall", True)
        except GateError:
            left = [p["metadata"]["name"] for p in self.kube.get_json("pods", "-n", NAMESPACE)["items"]]
            self.report.add("no pods left after uninstall", False, f"left: {left}")

    # -- checks -----------------------------------------------------------------------------
    def check_enroll(self):
        state = self.mock_state()
        secret = self.kube.get_json("secret", AGENT_SECRET, "-n", NAMESPACE, missing_ok=True)
        account = base64.b64decode(secret["data"].get("AGENT_ACCOUNTID", "")).decode() if secret else ""
        self.report.add("enroll created the agent Secret from the Sedai API",
                        secret is not None and account == ACCOUNT_ID and state["secret_downloads"] >= 1,
                        f"secret={'present' if secret else 'MISSING'} AGENT_ACCOUNTID={account!r} "
                        f"downloads={state['secret_downloads']}")
        creates = state["account_creates"]
        self.report.add("enroll created exactly one account", len(creates) == 1, f"{len(creates)} create call(s)")
        if creates:
            body = creates[0]
            details = body.get("accountDetails", {})
            meta = details.get("metadata", {})
            identity = {"name": body.get("name"), "clusterName": meta.get("clusterName"),
                        "clusterProvider": meta.get("clusterProvider")}
            want = {"name": NICK_NAME, "clusterName": CLUSTER_NAME, "clusterProvider": "SELF_MANAGED"}
            self.report.add("account name, cluster name and provider come from the chart values", identity == want,
                            f"got {identity}, want {want}")
            flags = {k: v for k, v in details.items() if isinstance(v, bool) and k != "enabled"}
            want_flags = self.expect["account_flags"]
            wrong = {k: v for k, v in flags.items() if want_flags.get(k) != v}
            uncovered = sorted(set(flags) - set(want_flags))
            self.report.add("account component flags match the profile's toggles", not wrong and not uncovered,
                            f"mismatched (got): {wrong}; not in {self.profile}.expect.json: {uncovered}"
                            if wrong or uncovered else json.dumps(flags, sort_keys=True))
        got_mps = sorted((mp.get("monitoringProvider"), (mp.get("details") or {}).get("endpoint"))
                         for mp in state["monitoring_providers"])
        want_mps = sorted((mp["monitoringProvider"], mp["endpoint"]) for mp in self.expect["monitoring_providers"])
        self.report.add("enroll registered the profile's monitoring providers", got_mps == want_mps,
                        f"got {got_mps}, want {want_mps}")
        self.report.add("no unauthorized calls to the Sedai API", not state["auth_failures"],
                        "; ".join(state["auth_failures"])[:1000])
        self.report.add("hooks called only API paths the Sedai API serves", not state["unhandled"],
                        "; ".join(state["unhandled"])[:1000])

    def check_monitoring_endpoints(self):
        """Each registered endpoint must be a Service in the release that answers a PromQL query."""
        for mp in self.expect["monitoring_providers"]:
            host = mp["endpoint"].split("://", 1)[1]
            service, _, port = host.partition(":")
            path = (f"/api/v1/namespaces/{NAMESPACE}/services/{service}:{port or '80'}/proxy"
                    f"/api/v1/query?query=up")
            try:
                body = wait_for(f"{mp['endpoint']} to answer PromQL",
                                lambda: (lambda b: b if json.loads(b).get("status") == "success" else None)(
                                    self.kube.raw(path)), 120, 5)
                series = len(json.loads(body)["data"]["result"])
                self.report.add(f"{mp['monitoringProvider']} endpoint {mp['endpoint']} answers PromQL", True,
                                f"up: {series} series")
            except GateError as err:
                self.report.add(f"{mp['monitoringProvider']} endpoint {mp['endpoint']} answers PromQL", False,
                                str(err))

    def workloads(self):
        return [d for d in self.manifest if d["kind"] in WORKLOAD_KINDS]

    def check_workloads(self):
        for doc in self.workloads():
            kind, name = doc["kind"], doc["metadata"]["name"]
            live = self.kube.get_json(kind.lower(), name, "-n", NAMESPACE, missing_ok=True)
            if not live:
                self.report.add(f"{kind}/{name} Ready", False, "not found in the cluster")
                continue
            st, spec = live.get("status", {}), live.get("spec", {})
            if kind == "DaemonSet":
                desired, ready = st.get("desiredNumberScheduled", 0), st.get("numberReady", 0)
                ok, detail = desired >= 1 and ready == desired, f"{ready}/{desired} pods ready"
            else:
                want = spec.get("replicas", 1)
                ready = st.get("readyReplicas", 0) if kind == "StatefulSet" else st.get("availableReplicas", 0)
                ok, detail = ready >= want and want >= 1, f"{ready}/{want} replicas ready"
            self.report.add(f"{kind}/{name} Ready", ok, detail)

    def check_pods(self, when):
        rendered_images = {img for d in self.manifest for img in images_of(d)}
        pods = [p for p in self.kube.get_json("pods", "-n", NAMESPACE)["items"]
                if "job-name" not in (p["metadata"].get("labels") or {})]
        restarts, foreign, unpulled = [], [], []
        for pod in pods:
            name = pod["metadata"]["name"]
            statuses = pod["status"].get("initContainerStatuses", []) + pod["status"].get("containerStatuses", [])
            for cs in statuses:
                if cs.get("restartCount", 0) > 0:
                    last = (cs.get("lastState") or {}).get("terminated") or {}
                    prev = self.kube.kubectl("logs", "-n", NAMESPACE, name, "-c", cs["name"], "--previous",
                                             "--tail", "3", check=False, timeout=60).stdout.strip().splitlines()
                    restarts.append(f"{name}/{cs['name']} x{cs['restartCount']} "
                                    f"(last: {last.get('reason', '?')} exit {last.get('exitCode', '?')}; "
                                    f"last log line: {prev[-1][:200] if prev else 'n/a'})")
                if not cs.get("imageID"):
                    unpulled.append(f"{name}/{cs['name']}")
            for c in pod["spec"].get("initContainers", []) + pod["spec"]["containers"]:
                if c["image"] not in rendered_images:
                    foreign.append(f"{name}/{c['name']}={c['image']}")
        self.report.add(f"no container restarts ({when})", not restarts, "; ".join(restarts))
        self.report.add(f"every container runs the image the chart rendered ({when})", not foreign and not unpulled,
                        f"not rendered: {foreign} no imageID: {unpulled}" if foreign or unpulled
                        else f"{len(rendered_images)} images")

    def agent_pods(self):
        return [p["metadata"]["name"] for p in self.kube.get_json("pods", "-n", NAMESPACE)["items"]
                if p["metadata"]["name"].startswith("sedai-smart-agent-")
                and "job-name" not in (p["metadata"].get("labels") or {})]

    def agent_logs(self):
        text = ""
        for pod in self.agent_pods():
            for flag in ([], ["--previous"]):
                text += self.kube.kubectl("logs", "-n", NAMESPACE, pod, "--all-containers", *flag,
                                          check=False, timeout=60).stdout
        return text

    def check_agent_health(self):
        values = self.kube.helm("get", "values", RELEASE, "-n", NAMESPACE, "--all", "-o", "json").stdout
        want = json.loads(values)["image"]["smartAgent"]["imageTag"]
        pods = self.agent_pods()
        if not pods:
            self.report.add("agent /agent/health UP", False, "no smart-agent pod")
            return
        body = self.kube.raw(f"/api/v1/namespaces/{NAMESPACE}/pods/{pods[0]}:8080/proxy/agent/health")
        (self.art / "agent-health.json").write_text(body or "")
        found = {}

        def walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k in ("status", "version") and isinstance(v, str):
                        found.setdefault(k, set()).add(v)
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(json.loads(body))
        self.report.add("agent /agent/health UP", "UP" in found.get("status", set()),
                        f"statuses {sorted(found.get('status', []))}")
        self.report.add("agent reports the chart's image version", want in found.get("version", set()),
                        f"chart imageTag {want}, agent reports {sorted(found.get('version', []))}")

    def _webhook_metrics(self):
        counts = {}
        for line in self.kube.raw("/metrics").splitlines():
            m = re.match(r'(apiserver_admission_webhook_(?:request_total|fail_open_count))\{([^}]*)\} (\S+)', line)
            if m:
                labels = dict(re.findall(r'(\w+)="([^"]*)"', m.group(2)))
                key = (m.group(1), labels.get("name"), labels.get("operation", ""), labels.get("code", ""))
                counts[key] = counts.get(key, 0) + float(m.group(3))
        return counts

    def check_webhooks(self):
        hooks = [d for d in self.manifest if d["kind"] == "MutatingWebhookConfiguration"]
        if not hooks:
            return
        tls = self.kube.get_json("secret", "sedai-kube-spec-controller-tls", "-n", NAMESPACE, missing_ok=True)
        ca = (tls or {}).get("data", {}).get("ca.crt")
        cert = base64.b64decode((tls or {}).get("data", {}).get("tls.crt", "")) if tls else b""
        with tempfile.NamedTemporaryFile("wb", suffix=".crt") as fh:
            fh.write(cert)
            fh.flush()
            san = run(["openssl", "x509", "-noout", "-ext", "subjectAltName", "-in", fh.name], check=False).stdout
        services = set()
        for doc in hooks:
            name = doc["metadata"]["name"]
            live = self.kube.get_json("mutatingwebhookconfiguration", name, missing_ok=True)
            bundles = {w.get("clientConfig", {}).get("caBundle") for w in (live or {}).get("webhooks", [])}
            self.report.add(f"MutatingWebhookConfiguration/{name} trusts the controller's CA",
                            live is not None and ca is not None and bundles == {ca},
                            "caBundle matches the TLS Secret" if live and bundles == {ca}
                            else f"live={'yes' if live else 'no'} tls-ca={'yes' if ca else 'no'}")
            for hook in (live or {}).get("webhooks", []):
                svc = hook.get("clientConfig", {}).get("service") or {}
                services.add((svc.get("name"), svc.get("namespace"), svc.get("port", 443)))
        for svc_name, svc_ns, port in sorted(services, key=str):
            dns = f"DNS:{svc_name}.{svc_ns}.svc"
            self.report.add(f"controller certificate is valid for {svc_name}.{svc_ns}.svc", dns in san,
                            san.strip().splitlines()[-1].strip() if san.strip() else "could not read tls.crt")
            live_svc = self.kube.get_json("service", svc_name, "-n", svc_ns, missing_ok=True)
            ports = [p.get("port") for p in (live_svc or {}).get("spec", {}).get("ports", [])]
            self.report.add(f"webhook Service {svc_name}:{port} exists", port in ports, f"service ports {ports}")
        if not services:
            self.report.add("webhooks point at a Service", False, "no clientConfig.service in the live webhooks")
            return
        # The controller answers on the Service the webhooks dial.
        svc_name, svc_ns, port = sorted(services, key=str)[0]
        try:
            wait_for("spec-controller /sedai/health", lambda: self.kube.raw(
                f"/api/v1/namespaces/{svc_ns}/services/https:{svc_name}:{port}/proxy/sedai/health"), 120, 5)
            self.report.add("spec-controller answers /sedai/health over TLS", True)
        except GateError as err:
            self.report.add("spec-controller answers /sedai/health over TLS", False, str(err))
        # End to end: send admission requests through the API server and read its webhook metrics.
        # A list, not a dict by name: the pod and spark webhooks share one webhook name.
        entries = [h for d in hooks for h in d.get("webhooks", [])]
        pod_hook = next((h["name"] for h in entries
                         if any("pods" in r.get("resources", []) and "CREATE" in r.get("operations", [])
                                for r in h.get("rules", []))), None)
        workload_hook = next((h["name"] for h in entries
                              if any("deployments" in r.get("resources", []) and "UPDATE" in r.get("operations", [])
                                     for r in h.get("rules", []))), None)
        before = self._webhook_metrics()
        probe = {"apiVersion": "v1", "kind": "Pod",
                 "metadata": {"name": "chart-gate-webhook-probe", "namespace": FIXTURE_NS},
                 "spec": {"containers": [{"name": "pause", "image": "registry.k8s.io/pause:3.10"}]}}
        self.kube.kubectl("create", "--dry-run=server", "-f", "-", "-o", "name", input_text=json.dumps(probe))
        self.kube.kubectl("annotate", "deployment/gate-fixture-deployment", "-n", FIXTURE_NS,
                          "chart-gate/webhook-probe=1", "--overwrite", "--dry-run=server")
        after = self._webhook_metrics()

        def delta(metric, name, operation, code=""):
            keys = {k for k in set(before) | set(after)
                    if k[0] == metric and k[1] == name and k[2] == operation and (not code or k[3] == code)}
            return sum(after.get(k, 0) - before.get(k, 0) for k in keys)

        for hook, operation, what in ((pod_hook, "CREATE", "Pod create"), (workload_hook, "UPDATE", "Deployment update")):
            if not hook:
                self.report.add(f"admission webhook for {what} is registered", False, "no matching webhook rule")
                continue
            answered = delta("apiserver_admission_webhook_request_total", hook, operation, "200")
            failed_open = delta("apiserver_admission_webhook_fail_open_count", hook, operation)
            self.report.add(f"spec-controller answered a {what} admission ({hook})", answered >= 1 and not failed_open,
                            f"HTTP 200 responses +{answered:g}, fail-open +{failed_open:g}")

    def check_discovery(self):
        log("waiting for the agent's discovery round (topology push + finalize-refresh)")
        try:
            state = wait_for("finalize-refresh from the agent",
                             lambda: (lambda s: s if s["finalize"] else None)(self.mock_state()), 480, 10)
        except GateError as err:
            state = self.mock_state()
            self.report.add("agent completed a discovery round", False,
                            f"{err}; chunk posts={state['chunk_posts']} agent calls={state['agent_calls']}")
            return
        resources = state["resources"]
        self.report.add("agent completed a discovery round", len(resources) > 0,
                        f"{len(resources)} resources in {state['chunk_posts']} chunk(s)")
        self.report.add("discovery payloads parsed", not state["chunk_errors"], "; ".join(state["chunk_errors"]))
        pushed = {str(r["id"]) for r in resources if "id" in r}
        finalized = set(state["finalize"][0])
        self.report.add("finalize-refresh lists exactly the pushed resources", bool(pushed) and pushed == finalized,
                        f"pushed {len(pushed)}, finalized {len(finalized)}, "
                        f"only pushed {sorted(pushed - finalized)[:5]}, only finalized {sorted(finalized - pushed)[:5]}")
        # The agent ids workloads as <account>/<Kind>/<clusterName>/<namespace>/<name>.
        expected = [("Deployment", FIXTURE_NS, "gate-fixture-deployment"),
                    ("StatefulSet", FIXTURE_NS, "gate-fixture-statefulset"),
                    ("DaemonSet", FIXTURE_NS, "gate-fixture-daemonset")]
        expected += [(d["kind"], NAMESPACE, d["metadata"]["name"]) for d in self.workloads()]
        missing = [f"{kind}/{ns}/{name}" for kind, ns, name in expected
                   if f"{ACCOUNT_ID}/{kind}/{CLUSTER_NAME}/{ns}/{name}" not in pushed]
        self.report.add(f"discovery reported every expected workload ({len(expected)})", not missing,
                        f"missing: {missing}" if missing else "fixtures + chart workloads, matched by id")
        unmodelled = state.get("agent_unmodelled", [])
        if unmodelled:
            log(f"agent called endpoints the mock does not model (answered OK): {sorted(set(unmodelled))}")

    def check_agent_logs(self):
        """The agent swallows RBAC denials and keeps going, so a chart that drops a rule still
        'works' — it just stops seeing those resources. Compare what the agent was denied against
        the committed baseline for this profile; a new denial fails, a fixed one is reported."""
        text = self.agent_logs()
        (self.art / "agent.log").write_text(text)
        self.report.add("agent logs captured (discovery ran in them)", "Topology discovery took" in text,
                        f"{len(text.splitlines())} lines")
        self.report.add("agent runs in the chart's REST connection mode",
                        "Connection Type is not WS" in text,
                        "connectionType: REST in values/gate.yaml must reach the agent as AGENT_CONNECTIONTYPE")
        denied = set()
        for verb, resource, group in re.findall(
                r'cannot (\w+) resource \\?"([^"\\]+)\\?" in API group \\?"([^"\\]*)\\?"', text):
            denied.add(f"{verb} {group or 'core'}/{resource}")
        for what in re.findall(r"insuff\w* privileges to discover ([a-z][a-z ]*?)(?= for | in |:|$)",
                               text, re.IGNORECASE | re.MULTILINE):
            denied.add(f"discover {what.strip().lower()}")
        baseline_file = EXPECTED / f"{self.profile}.rbac-denials.txt"
        baseline = _read_expected(baseline_file) if baseline_file.exists() else set()
        new, fixed = sorted(denied - baseline), sorted(baseline - denied)
        detail = f"denied: {sorted(denied) or 'nothing'}"
        if new:
            detail = (f"denied but not in expected/{baseline_file.name}: {new} — the agent's ServiceAccount "
                      f"cannot read what discovery needs. Grant it in the chart, or if the gap is accepted, "
                      f"add the lines to that file")
        elif fixed:
            detail += f"; no longer denied (remove from expected/{baseline_file.name}): {fixed}"
        self.report.add("no new RBAC denials for the agent", not new, detail)

    # -- diagnostics ------------------------------------------------------------------------
    def diagnostics(self):
        out = self.art / "diagnostics"
        out.mkdir(exist_ok=True)
        k = self.kube
        for name, args in {
            "all.txt": ["get", "all,pvc,secret,configmap,events", "-A", "-o", "wide"],
            "describe-sedai.txt": ["describe", "all,pvc", "-n", NAMESPACE],
            "describe-mock.txt": ["describe", "all", "-n", MOCK_NS],
        }.items():
            proc = k.kubectl(*args, check=False, timeout=120)
            (out / name).write_text(proc.stdout + proc.stderr)
        for ns in (NAMESPACE, MOCK_NS):
            proc = k.kubectl("get", "pods", "-n", ns, "-o", "json", check=False, timeout=60)
            pods = json.loads(proc.stdout) if proc.returncode == 0 else {"items": []}
            for pod in pods["items"]:
                name = pod["metadata"]["name"]
                for flag, suffix in (([], ""), (["--previous"], ".previous")):
                    proc = k.kubectl("logs", "-n", ns, name, "--all-containers", "--timestamps", *flag,
                                     check=False, timeout=60)
                    if proc.stdout:
                        (out / f"{ns}--{name}{suffix}.log").write_text(proc.stdout)
        server = run(["docker", "logs", f"k3d-{self.cluster}-server-0"], check=False, timeout=120)
        (out / "k3s-server.log").write_text(server.stdout + server.stderr)
        # Per-pod memory as the kubelet sees it, to set against the host's commit accounting.
        nodes = k.get_json("nodes")["items"]
        for node in nodes:
            name = node["metadata"]["name"]
            proc = k.kubectl("get", "--raw", f"/api/v1/nodes/{name}/proxy/stats/summary", check=False, timeout=60)
            (out / f"stats-summary-{name}.json").write_text(proc.stdout or proc.stderr)

    def save_mock_state(self):
        try:
            (self.art / "mock-state.json").write_text(json.dumps(self.mock_state(), indent=2))
        except Exception as err:
            log(f"could not read mock state: {err}")

    # -- flow -------------------------------------------------------------------------------
    def run(self):
        sampler = None
        try:
            self.cluster_up()
            sampler = MemorySampler(f"k3d-{self.cluster}-server-0", self.art / "host-memory.tsv")
            sampler.start()
            self.deploy_mock()
            self.apply_fixtures()
            self.helm_install()
            self.check_enroll()
            self.check_workloads()
            self.check_pods("after install")
            self.check_agent_health()
            self.check_monitoring_endpoints()
            self.check_webhooks()
            self.check_discovery()
            self.check_agent_logs()
            # Again after the discovery window: catches anything that crashed or was OOM-killed
            # once it was running, not just at startup.
            self.check_workloads()
            self.check_pods("after discovery")
            self.diagnostics()
            self.save_mock_state()
            self.helm_uninstall()
        except (GateError, RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as err:
            detail = str(err)
            if isinstance(err, subprocess.CalledProcessError):
                detail += f"\n{(err.stderr or '').strip()[-1500:]}"
            self.report.add("gate ran to completion", False, detail)
            try:
                self.diagnostics()
            except Exception as diag_err:
                log(f"diagnostics failed: {diag_err}")
        finally:
            if sampler:
                sampler.stop()
            self.save_mock_state()
            self.cluster_down()
            print(self.report.write_summary())
        return 1 if self.report.failed else 0


def cmd_install(args):
    return Install(args).run()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("static", help="render checks (no cluster)").set_defaults(fn=cmd_static)
    sub.add_parser("golden", help="rewrite expected/<profile>.txt and .rbac.txt").set_defaults(fn=cmd_golden)
    inst = sub.add_parser("install", help="install into a throwaway k3d cluster and verify")
    inst.add_argument("--profile", required=True, choices=installable_profiles())
    inst.add_argument("--cluster-name")
    inst.add_argument("--keep-cluster", action="store_true")
    inst.add_argument("--artifacts", default="chart-gate-artifacts")
    inst.set_defaults(fn=cmd_install)
    args = parser.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
