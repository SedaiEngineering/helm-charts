#!/usr/bin/env python3
"""Stand-in for the Sedai API used by the chart install gate.

Serves the calls the chart's enroll hooks and the smart agent make during install, startup
and one topology-discovery round, and records every call so the gate can assert on what the
chart actually did. Standard library only, so it runs from a stock python image.

Enroll side (paths under SEDAI_BASE_URL):
  HEAD /                                                   reachability probe
  GET  /api/site/accounts/lite                             account lookup by name
  POST /api/site/accounts                                  account create (component flags in body)
  GET  /api/site/accounts/{id}                             full account (correct-cluster-name job)
  DELETE /api/site/accounts/{id}                           deregister hook
  GET  /api/agent/accounts/{id}/agent-installation-gitops-commands
  GET  /gate/agent-secret.yaml                             the agent Secret the enroll Job applies
  GET|POST /api/monitoring/monitoringProviders/accounts/{id}

Agent side (paths under SERVER_REST_BASEURL = <self>/api):
  GET  /api/agent/operations/monitoringProviders/accounts/{id}/agent   fatal at agent startup
  GET  /api/agent/operations/config/{id}                               null keeps agent defaults
  GET  /api/agent/operations/action/requests/v2/{id}/...               REST-mode action poll
  POST /api/agent/operations/clouds/chunks/agent                       gzip topology chunk
  POST /api/agent/operations/clouds/agent/{id}/finalize-refresh        ids of every pushed resource
  *    /api/agent/operations/**                                        acknowledged and counted

Gate side:
  GET  /gate/state                                         everything recorded so far
"""
import gzip
import json
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ENROLL_TOKEN = os.environ["GATE_ENROLL_TOKEN"]
AGENT_TOKEN = os.environ["GATE_AGENT_TOKEN"]
SELF_URL = os.environ["GATE_SELF_URL"].rstrip("/")
ACCOUNT_ID = os.environ.get("GATE_ACCOUNT_ID", "chart-gate-account")
# Extra env for the agent, delivered through the Secret (the agent reads it via envFrom).
AGENT_ENV = json.loads(os.environ.get("GATE_AGENT_ENV", "{}"))

OPS = "/api/agent/operations/"
# Agent calls the mock answers with a plain OK on purpose; anything else is recorded so a new agent
# endpoint is visible in the gate output.
AGENT_MODELLED = re.compile(
    r"(POST heartbeat|POST metrics/internal.*|GET discoverMetrics/.*|GET spark/runs/non-terminated"
    r"|POST action/responses|POST raw/.*)$")

_lock = threading.Lock()
_state = {
    "accounts": [],              # what accounts/lite returns
    "account_creates": [],       # POST /api/site/accounts bodies
    "account_deletes": [],       # DELETE /api/site/accounts/{id}
    "secret_downloads": 0,
    "monitoring_providers": [],  # POST bodies
    "agent_calls": {},           # "METHOD /normalized/path" -> count
    "chunk_posts": 0,
    "resources": [],             # one summary per discovered resource
    "chunk_errors": [],
    "chunk_sample": [],          # first resources of the first chunk, verbatim, for debugging
    "finalize": [],              # one id list per finalize-refresh
    "auth_failures": [],
    "unhandled": [],
    "agent_unmodelled": [],
}


def _record(key, value):
    with _lock:
        _state[key].append(value)


def _count_agent_call(method, path):
    # Collapse ids so counts group by endpoint, not by account.
    norm = re.sub(r"/" + re.escape(ACCOUNT_ID) + r"(?=/|$)", "/{id}", path)
    with _lock:
        key = f"{method} {norm}"
        _state["agent_calls"][key] = _state["agent_calls"].get(key, 0) + 1


def _agent_secret_yaml():
    # Like Sedai, name the agent after the account enroll created: the account name and the cluster
    # name in the create body, not values the mock picks.
    with _lock:
        created = _state["account_creates"][-1] if _state["account_creates"] else None
    if created is None:
        return None
    data = {
        "AGENT_ACCOUNTID": ACCOUNT_ID,
        "AGENT_TENANT": "chart-gate",
        "AGENT_ACCOUNTNAME": created.get("name"),
        "AGENT_CLUSTERNAME": (created.get("accountDetails") or {}).get("metadata", {}).get("clusterName"),
        "SERVER_ACCESSKEY": AGENT_TOKEN,
        "SERVER_REST_BASEURL": SELF_URL + "/api",
        "SERVER_WS_BASEURL": SELF_URL.replace("http", "ws", 1) + "/ws",
        **AGENT_ENV,
    }
    lines = [
        "apiVersion: v1",
        "kind: Secret",
        "metadata:",
        "  name: sedai-smart-agent",
        "  namespace: default",
        "type: Opaque",
        "stringData:",
    ]
    lines += [f"  {k}: {json.dumps(str(v))}" for k, v in data.items()]
    return "\n".join(lines) + "\n"


def _summarise(resource):
    """Pull the identifying fields out of one discovered resource, whatever its subtype."""
    if not isinstance(resource, dict):
        return {"raw": str(resource)[:200]}
    out = {}
    for key in ("id", "name", "namespace", "resourceType", "inferenceType", "@type", "type", "kind"):
        value = resource.get(key)
        if isinstance(value, (str, int, float, bool)):
            out[key] = value
    return out


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "chart-gate-mock-core"

    # ---- plumbing ---------------------------------------------------------------------
    def _send(self, code, payload=None, content_type="application/json"):
        if payload is None:
            body = b""
        elif isinstance(payload, (bytes, bytearray)):
            body = bytes(payload)
        elif isinstance(payload, str):
            body = payload.encode()
        else:
            body = json.dumps(payload).encode()
        try:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass  # client (e.g. a probe) hung up; nothing to answer

    def _ok(self, result=None, **extra):
        self._send(200, {"status": "OK", "message": None, "result": result, **extra})

    def _read_body(self):
        # The agent's HTTP client streams request bodies with Transfer-Encoding: chunked (no
        # Content-Length). Read the whole body either way, so nothing is left on a kept-alive
        # connection to corrupt the next request.
        if "chunked" in self.headers.get("Transfer-Encoding", "").lower():
            raw = bytearray()
            while True:
                size = int(self.rfile.readline().split(b";")[0].strip() or b"0", 16)
                if size == 0:
                    while self.rfile.readline() not in (b"\r\n", b"\n", b""):
                        pass  # trailers
                    break
                raw += self.rfile.read(size)
                self.rfile.readline()  # CRLF closing the chunk
            raw = bytes(raw)
        else:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
        if self.headers.get("Content-Encoding", "").lower() == "gzip" and raw:
            raw = gzip.decompress(raw)
        return raw

    def _json_body(self):
        return json.loads(self._raw) if self._raw else None

    def _authorized(self, expected):
        got = self.headers.get("Authorization", "")
        if got == f"Bearer {expected}":
            return True
        _record("auth_failures", f"{self.command} {self.path}: got {'<none>' if not got else got.split(' ')[0] + ' <redacted>'}")
        self._send(401, {"status": "ERROR", "message": "unauthorized"})
        return False

    def log_message(self, fmt, *args):
        sys.stdout.write("%s %s\n" % (self.command, fmt % args))
        sys.stdout.flush()

    # ---- routing ----------------------------------------------------------------------
    def do_HEAD(self):
        self._route()

    def do_GET(self):
        self._route()

    def do_POST(self):
        self._route()

    def do_PUT(self):
        self._route()

    def do_DELETE(self):
        self._route()

    def _route(self):
        path = urlsplit(self.path).path.rstrip("/") or "/"
        method = self.command
        try:
            self._raw = self._read_body()
            if path == "/" and method in ("HEAD", "GET"):
                return self._send(200, {"status": "OK"})
            if path == "/gate/state" and method == "GET":
                with _lock:
                    return self._send(200, _state)
            if path == "/gate/agent-secret.yaml" and method == "GET":
                secret = _agent_secret_yaml()
                if secret is None:
                    _record("unhandled", f"{method} {path}: agent Secret requested before any account was created")
                    return self._send(409, {"status": "ERROR", "message": "no account created yet"})
                with _lock:
                    _state["secret_downloads"] += 1
                return self._send(200, secret, "application/yaml")
            if path.startswith(OPS):
                return self._agent(method, path)
            if path.startswith("/api/"):
                return self._enroll(method, path)
        except Exception as exc:  # surface handler bugs as 500s and in the state
            _record("unhandled", f"{method} {path}: handler error {exc!r}")
            return self._send(500, {"status": "ERROR", "message": repr(exc)})
        _record("unhandled", f"{method} {path}")
        self._send(404, {"status": "ERROR", "message": "not served by chart-gate mock"})

    # ---- enroll hooks -----------------------------------------------------------------
    def _enroll(self, method, path):
        if not self._authorized(ENROLL_TOKEN):
            return
        if path == "/api/site/accounts/lite" and method == "GET":
            with _lock:
                accounts = [{"id": a["id"], "name": a["name"]} for a in _state["accounts"]]
            return self._ok(accounts)
        if path == "/api/site/accounts" and method == "POST":
            body = self._json_body() or {}
            _record("account_creates", body)
            with _lock:
                if not any(a["id"] == ACCOUNT_ID for a in _state["accounts"]):
                    _state["accounts"].append({"id": ACCOUNT_ID, "name": body.get("name"), **body})
            return self._ok({"accountId": ACCOUNT_ID})
        m = re.fullmatch(r"/api/site/accounts/([^/]+)", path)
        if m and method == "GET":
            with _lock:
                found = [a for a in _state["accounts"] if a["id"] == m.group(1)]
            return self._ok(found)
        if m and method == "DELETE":
            _record("account_deletes", m.group(1))
            with _lock:
                _state["accounts"] = [a for a in _state["accounts"] if a["id"] != m.group(1)]
            return self._ok()
        if re.fullmatch(r"/api/agent/accounts/[^/]+/agent-installation-gitops-commands", path) and method == "GET":
            url = f"{SELF_URL}/gate/agent-secret.yaml"
            return self._ok({"createSecretKubectlCmd": f'kubectl apply -f "{url}"'})
        if re.fullmatch(r"/api/monitoring/monitoringProviders/accounts/[^/]+", path):
            if method == "POST":
                body = self._json_body()
                _record("monitoring_providers", body)
                return self._ok(body)
            if method == "GET":
                with _lock:
                    return self._ok(list(_state["monitoring_providers"]))
        _record("unhandled", f"{method} {path}")
        self._send(404, {"status": "ERROR", "message": "not served by chart-gate mock"})

    # ---- smart agent ------------------------------------------------------------------
    def _agent(self, method, path):
        if not self._authorized(AGENT_TOKEN):
            return
        _count_agent_call(method, path)
        rest = path[len(OPS):]
        if method == "POST" and rest == "clouds/chunks/agent":
            return self._chunk()
        if method == "POST" and re.fullmatch(r"clouds/agent/[^/]+/finalize-refresh", rest):
            ids = self._json_body() or []
            _record("finalize", sorted(str(i) for i in ids))
            return self._ok()
        if method == "GET" and rest.startswith("monitoringProviders/accounts/"):
            return self._ok([])
        if method == "GET" and rest.startswith("config/"):
            return self._ok(None)
        if method == "GET" and rest.startswith("configs/"):
            return self._ok([])
        if method == "GET" and rest.startswith("action/requests/"):
            return self._ok([], hasMorePages=False)
        if not AGENT_MODELLED.match(f"{method} {rest}"):
            _record("agent_unmodelled", f"{method} {OPS}{rest}")
        return self._ok(None)

    def _chunk(self):
        try:
            resources = self._json_body() or []
        except Exception as exc:
            _record("chunk_errors", repr(exc))
            return self._send(400, {"status": "ERROR", "message": repr(exc)})
        if isinstance(resources, dict):  # tolerate an envelope around the list
            resources = next((v for v in resources.values() if isinstance(v, list)), [resources])
        with _lock:
            _state["chunk_posts"] += 1
            _state["resources"].extend(_summarise(r) for r in resources)
            if not _state["chunk_sample"]:
                _state["chunk_sample"] = resources[:3]
        return self._ok()


def main():
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.daemon_threads = True
    print(f"chart-gate mock core listening on :{port} as {SELF_URL}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
