#!/usr/bin/env python3
"""Keeps the smart-scheduler image maps in charts/sedai-smart-agent/values.yaml current.

  image.scheduler.tagByK8sMinor  registry.k8s.io/kube-scheduler           -> public.ecr.aws/sedai_io/sedai-kube-scheduler
  image.compactor.tagByK8sMinor  registry.k8s.io/descheduler/descheduler  -> public.ecr.aws/sedai_io/sedai-kube-descheduler

The ECR images are unchanged copies of upstream (same multi-arch index digest), made with `crane copy`.

For each release branch (dev, edge, main) the script:
  * bumps every mapped minor to the newest upstream patch. It never downgrades, and it leaves a pin
    that is not a plain vX.Y.Z of that minor alone;
  * adds a new Kubernetes minor N only once kube-scheduler v1.N and descheduler v0.N both have a GA
    release. The compactor lookup is exact-minor only, so on a minor with no compactor key the chart
    skips the scheduler and the compactor together: a scheduler-only key would install nothing;
  * checks that every tag the maps reference is in public ECR with the upstream digest, and copies
    the missing ones (--apply). A bump whose image could not be copied is dropped from the PR;
  * opens or refreshes one PR per branch from bot/k8s-image-sync-<branch>, and closes it when the
    branch no longer needs it.
It also keeps one issue open (label k8s-image-sync) per Kubernetes minor that has a kube-scheduler GA
release but no descheduler release yet, and closes it once descheduler ships.

Without --apply it only reports the plan: no copies, pushes, PRs or issues.
Needs crane, git, gh and PyYAML. With --apply, crane must already be logged in to public.ecr.aws.

Usage: .github/scripts/k8s_image_sync.py [--apply] [--branches dev,edge,main] [--repo OWNER/NAME]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

VALUES = "charts/sedai-smart-agent/values.yaml"
LABEL = "k8s-image-sync"
BOT_PREFIX = "bot/k8s-image-sync-"
MIRROR_REGISTRY = "public.ecr.aws"

COMPONENTS = {
    "scheduler": {
        "upstream": "registry.k8s.io/kube-scheduler",
        "repository": "sedai_io/sedai-kube-scheduler",
        "major": 1,
        "notes": "https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.{minor}.md",
    },
    "compactor": {
        "upstream": "registry.k8s.io/descheduler/descheduler",
        "repository": "sedai_io/sedai-kube-descheduler",
        "major": 0,
        "notes": "https://github.com/kubernetes-sigs/descheduler/releases/tag/{tag}",
    },
}


# ---------------------------------------------------------------- helpers

def run(cmd, check=True, env=None, cwd=None, input=None):
    res = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd, input=input)
    if check and res.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:4])} ... failed ({res.returncode}): {res.stderr.strip()[-800:]}")
    return res


def git(*args, check=True, cwd=None):
    return run(["git", *args], check=check, cwd=cwd).stdout


def gh(*args, token, check=True, input=None):
    env = dict(os.environ, GH_TOKEN=token)
    return run(["gh", *args], check=check, env=env, input=input).stdout


def tag_of(major, minor, patch):
    return f"v{major}.{minor}.{patch}"


def parse_tag(major, tag):
    m = re.fullmatch(rf"v{major}\.(\d+)\.(\d+)", tag)
    return (int(m.group(1)), int(m.group(2))) if m else None


_DIGESTS: dict[str, str | None] = {}


def digest(ref):
    """The manifest (index) digest of ref, or None when the tag or repository does not exist."""
    if ref not in _DIGESTS:
        res = run(["crane", "digest", ref], check=False)
        if res.returncode == 0:
            _DIGESTS[ref] = res.stdout.strip()
        elif re.search(r"MANIFEST_UNKNOWN|NAME_UNKNOWN|NOT_FOUND|not found", res.stderr, re.I):
            _DIGESTS[ref] = None
        else:
            raise RuntimeError(f"crane digest {ref}: {res.stderr.strip()[-500:]}")
    return _DIGESTS[ref]


def upstream_latest(comp):
    """{minor: newest GA patch} for a component, from the upstream registry's tag list."""
    tags = run(["crane", "ls", comp["upstream"]]).stdout.split()
    latest: dict[int, int] = {}
    for t in tags:
        parsed = parse_tag(comp["major"], t)
        if parsed:
            minor, patch = parsed
            latest[minor] = max(patch, latest.get(minor, -1))
    if not latest:
        raise RuntimeError(f"no GA tags found for {comp['upstream']}")
    return latest


# ---------------------------------------------------------------- values.yaml editing

ENTRY = re.compile(r'^      "(\d+)":\s*"([^"]*)"(.*)$')


def locate_map(lines, name):
    """(start, end, {minor: (tag, trailing)}, repository) of image.<name>.tagByK8sMinor, line based so
    comments and formatting elsewhere stay untouched."""
    try:
        i = next(n for n, l in enumerate(lines) if re.match(r"^image:\s*(#.*)?$", l))
    except StopIteration:
        raise RuntimeError("no top-level image: block in values.yaml")
    comp_start = None
    for n in range(i + 1, len(lines)):
        if re.match(r"^[^\s#]", lines[n]):  # next top-level key (comments don't end the block)
            break
        if re.match(rf"^  {name}:\s*(#.*)?$", lines[n]):
            comp_start = n
            break
    if comp_start is None:
        raise RuntimeError(f"no image.{name} block in values.yaml")
    repository, map_line = None, None
    for n in range(comp_start + 1, len(lines)):
        l = lines[n]
        if re.match(r"^([^\s#]|  [^\s#])", l):  # next top-level key or next image.<component>
            break
        m = re.match(r"^    repository:\s*\"?([^\"#\s]+)", l)
        if m:
            repository = m.group(1)
        if re.match(r"^    tagByK8sMinor:\s*(#.*)?$", l):
            map_line = n
            break
    if map_line is None:
        raise RuntimeError(f"no image.{name}.tagByK8sMinor in values.yaml")
    entries, end = {}, map_line + 1
    while end < len(lines) and ENTRY.match(lines[end]):
        m = ENTRY.match(lines[end])
        entries[int(m.group(1))] = (m.group(2), m.group(3))
        end += 1
    return map_line + 1, end, entries, repository


def read_maps(text):
    lines = text.split("\n")
    out = {}
    for name, comp in COMPONENTS.items():
        _, _, entries, repo = locate_map(lines, name)
        if repo != comp["repository"]:
            raise RuntimeError(f"image.{name}.repository is {repo!r}, expected {comp['repository']!r}: "
                               "update COMPONENTS in this script if the mirror moved")
        out[name] = {minor: tag for minor, (tag, _) in entries.items()}
    return out


def write_maps(text, maps):
    """text with image.<name>.tagByK8sMinor replaced by maps[name], verified with a YAML parse."""
    lines = text.split("\n")
    for name in COMPONENTS:  # same line count per entry kept or grown, so locate again each time
        start, end, entries, _ = locate_map(lines, name)
        new = [f'      "{minor}": "{tag}"{entries.get(minor, ("", ""))[1]}'
               for minor, tag in sorted(maps[name].items())]
        lines[start:end] = new
    new_text = "\n".join(lines)
    before, after = yaml.safe_load(text), yaml.safe_load(new_text)
    for name in COMPONENTS:
        want = {str(k): v for k, v in maps[name].items()}
        if after["image"][name]["tagByK8sMinor"] != want:
            raise RuntimeError(f"edit check failed for image.{name}.tagByK8sMinor")
        before["image"][name]["tagByK8sMinor"] = after["image"][name]["tagByK8sMinor"] = None
    if before != after:
        raise RuntimeError("edit check failed: values.yaml changed outside the two tag maps")
    return new_text


# ---------------------------------------------------------------- planning

def plan_branch(current, latest):
    """Proposed maps and a change list for one branch: patch bumps, plus new minors that both
    components have released."""
    proposed = {name: dict(m) for name, m in current.items()}
    changes = []  # (component, minor, old_tag or None, new_tag)
    for name, comp in COMPONENTS.items():
        for minor, tag in sorted(current[name].items()):
            parsed = parse_tag(comp["major"], tag)
            if not parsed or parsed[0] != minor or minor not in latest[name]:
                continue  # custom pin, or a minor upstream no longer lists: leave it
            newest = latest[name][minor]
            if newest > parsed[1]:
                new_tag = tag_of(comp["major"], minor, newest)
                proposed[name][minor] = new_tag
                changes.append((name, minor, tag, new_tag))
    # New minors above the lower of the two maps' tops, so a map left one minor behind catches up too.
    floor = min(max(current["scheduler"]), max(current["compactor"]))
    for minor in sorted(m for m in latest["scheduler"] if m > floor and m in latest["compactor"]):
        for name, comp in COMPONENTS.items():
            if minor not in proposed[name]:
                new_tag = tag_of(comp["major"], minor, latest[name][minor])
                proposed[name][minor] = new_tag
                changes.append((name, minor, None, new_tag))
    return proposed, changes


def mirror_ref(name, tag):
    return f"{MIRROR_REGISTRY}/{COMPONENTS[name]['repository']}:{tag}"


def upstream_ref(name, tag):
    return f"{COMPONENTS[name]['upstream']}:{tag}"


# ---------------------------------------------------------------- GitHub side

def pick_token(repo):
    """GHPAT when it can push (its PRs start the PR checks, GITHUB_TOKEN's do not), else GITHUB_TOKEN."""
    pat, default = os.environ.get("GHPAT", ""), os.environ.get("GITHUB_TOKEN", "")
    if pat:
        res = run(["gh", "api", f"repos/{repo}", "--jq", ".permissions.push"], check=False,
                  env=dict(os.environ, GH_TOKEN=pat))
        if res.returncode == 0 and res.stdout.strip() == "true":
            return pat, True
        print("::warning::GHPAT cannot push to this repo; using GITHUB_TOKEN, so the bot PRs' checks will not "
              "start on their own (close and reopen a PR to run them)")
    if not default:
        sys.exit("no GITHUB_TOKEN or GHPAT in the environment")
    return default, False


def pr_body(base, changes, digests, run_url, checks_start):
    rows = []
    for name, minor, old, new in sorted(changes, key=lambda c: (c[0], c[1])):
        notes = COMPONENTS[name]["notes"].format(minor=minor, tag=new)
        what = "new minor" if old is None else "patch"
        rows.append(f"| {name} | 1.{minor} | {old or '—'} | [{new}]({notes}) | {what} | `{digests[(name, new)][:19]}…` |")
    new_minors = sorted({minor for _, minor, old, _ in changes if old is None})
    lines = [
        f"Automated update of the smart-scheduler image maps on `{base}` "
        f"(`image.scheduler.tagByK8sMinor` / `image.compactor.tagByK8sMinor`).",
        "",
        "| Component | k8s | Current | New | Change | Digest |",
        "|---|---|---|---|---|---|",
        *rows,
        "",
        "Every new tag is already in `public.ecr.aws/sedai_io` as an unchanged copy of `registry.k8s.io` "
        "(the digest above is the same on both). Read the linked release notes before approving.",
    ]
    if new_minors:
        lines += ["", "New minors " + ", ".join(f"1.{m}" for m in new_minors) +
                  ": until this merges and ships, the chart skips the smart scheduler and compactor on those "
                  "clusters (the compactor lookup is exact-minor only)."]
    lines += ["", "Values-only: no `Chart.yaml` bump, so nothing publishes until the next chart release on this "
                  "channel."]
    if not checks_start:
        lines += ["", "> **Opened with GITHUB_TOKEN, so the PR checks did not start: close and reopen this PR "
                      "to run them.**"]
    lines += ["", f"Opened by the [k8s-image-sync workflow]({run_url}) "
                  "(`.github/workflows/k8s-image-sync.yaml`). It force-pushes this branch when the upstream "
                  "versions move again; don't push to it by hand."]
    return "\n".join(lines) + "\n"


def sync_branch_pr(repo, token, base, old_text, new_text, changes, digests, run_url, checks_start, report):
    bot = BOT_PREFIX + base
    prs = json.loads(gh("pr", "list", "--repo", repo, "--head", bot, "--base", base, "--state", "open",
                        "--json", "number,url,mergeable", token=token))
    pr = prs[0] if prs else None
    if new_text == old_text:
        if pr:
            gh("pr", "close", str(pr["number"]), "--repo", repo, "--delete-branch", "--comment",
               f"Closing: `{base}` already has the newest tags, so this update is no longer needed.", token=token)
            report.append(f"- `{base}`: up to date; closed {pr['url']}")
        else:
            report.append(f"- `{base}`: up to date")
        return
    remote_text = run(["git", "show", f"origin/{bot}:{VALUES}"], check=False).stdout
    needs_push = remote_text != new_text or not pr or pr.get("mergeable") == "CONFLICTING"
    if needs_push:
        with tempfile.TemporaryDirectory() as tmp:
            wt = Path(tmp) / "wt"
            git("worktree", "add", "-q", "--detach", str(wt), f"origin/{base}")
            try:
                (wt / VALUES).write_text(new_text)
                summary = "\n".join(f"{n} 1.{m}: {o or 'new'} -> {t}" for n, m, o, t in sorted(changes))
                git("-c", "user.name=github-actions[bot]",
                    "-c", "user.email=41898283+github-actions[bot]@users.noreply.github.com",
                    "commit", "-q", "-am", f"chore(smart-scheduler): sync Kubernetes image maps\n\n{summary}",
                    cwd=str(wt))
                git("push", "-q", "--force", "origin", f"HEAD:refs/heads/{bot}", cwd=str(wt))
            finally:
                git("worktree", "remove", "--force", str(wt))
    title = f"chore(smart-scheduler): sync Kubernetes image maps ({base})"
    body = pr_body(base, changes, digests, run_url, checks_start)
    if pr:
        gh("pr", "edit", str(pr["number"]), "--repo", repo, "--title", title, "--body-file", "-",
           token=token, input=body)
        report.append(f"- `{base}`: {'updated' if needs_push else 'unchanged'} {pr['url']}")
    else:
        url = gh("pr", "create", "--repo", repo, "--base", base, "--head", bot, "--title", title,
                 "--body-file", "-", token=token, input=body).strip()
        report.append(f"- `{base}`: opened {url}")


def sync_issues(repo, token, latest, mapped_top, run_url, report):
    """One open issue per scheduler minor above every mapped minor that descheduler has not released."""
    gh("label", "create", LABEL, "--repo", repo, "--color", "C5DEF5", "--force",
       "--description", "Opened by the k8s-image-sync workflow", token=token)
    issues = json.loads(gh("issue", "list", "--repo", repo, "--label", LABEL, "--state", "open",
                           "--json", "number,title", "--limit", "100", token=token))
    open_by_minor = {}
    for i in issues:
        m = re.match(r"Kubernetes 1\.(\d+):", i["title"])
        if m:
            open_by_minor[int(m.group(1))] = i["number"]
    waiting = sorted(m for m in latest["scheduler"] if m > mapped_top and m not in latest["compactor"])
    for minor in waiting:
        if minor in open_by_minor:
            continue
        body = (f"kube-scheduler v1.{minor} has a GA release (newest `v1.{minor}.{latest['scheduler'][minor]}`), "
                f"but descheduler has not released v0.{minor} yet.\n\n"
                f"The chart's compactor lookup is exact-minor only, so on Kubernetes 1.{minor} clusters with the "
                f"compactor enabled the chart skips the smart scheduler **and** the compactor. The "
                f"k8s-image-sync workflow adds 1.{minor} to both maps (and mirrors both images) in the first "
                f"run after descheduler v0.{minor}.x appears on registry.k8s.io, and closes this issue then.\n\n"
                f"Until then, a customer on 1.{minor} who needs the smart scheduler can disable the compactor "
                f"(the scheduler then runs v1.{minor - 1} under the N-1 skew rule).\n\n"
                f"Opened by the [k8s-image-sync workflow]({run_url}).\n")
        url = gh("issue", "create", "--repo", repo, "--label", LABEL,
                 "--title", f"Kubernetes 1.{minor}: waiting for descheduler v0.{minor} (smart scheduler skipped "
                            f"on 1.{minor})", "--body-file", "-", token=token, input=body).strip()
        report.append(f"- opened {url}")
    for minor, number in sorted(open_by_minor.items()):
        if minor not in waiting:
            gh("issue", "close", str(number), "--repo", repo, "--comment",
               f"descheduler v0.{minor} is out (or 1.{minor} is already mapped): the image-map PRs from "
               f"[this run]({run_url}) add it.", token=token)
            report.append(f"- closed #{number} (1.{minor})")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="copy images, push branches, open PRs and issues")
    ap.add_argument("--branches", default="dev,edge,main")
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "SedaiEngineering/helm-charts"))
    args = ap.parse_args()
    branches = [b for b in args.branches.split(",") if b]
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    run_url = (f"{server}/{args.repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
               if os.environ.get("GITHUB_RUN_ID") else f"{server}/{args.repo}/actions")
    errors, warnings, out = [], [], []

    token, checks_start = (None, True)
    if args.apply:
        token, checks_start = pick_token(args.repo)
        git("remote", "set-url", "origin", f"https://x-access-token:{token}@github.com/{args.repo}.git")
    git("fetch", "-q", "--prune", "origin", "+refs/heads/*:refs/remotes/origin/*")
    latest = {name: upstream_latest(comp) for name, comp in COMPONENTS.items()}
    texts, current, plans = {}, {}, {}
    for base in branches:
        texts[base] = git("show", f"origin/{base}:{VALUES}")
        current[base] = read_maps(texts[base])
        plans[base] = plan_branch(current[base], latest)

    # Every tag any proposed map references must be in our ECR with the upstream digest.
    refs = sorted({(name, tag) for _, (proposed, _) in plans.items() for name, m in proposed.items()
                   for tag in m.values()})
    changed = {(name, new) for _, (_, changes) in plans.items() for name, _, _, new in changes}
    with ThreadPoolExecutor(max_workers=8) as pool:  # warm the digest cache; ~2 lookups per tag
        list(pool.map(lambda r: digest(r), [f(n, t) for n, t in refs for f in (upstream_ref, mirror_ref)]))
    status, digests, unusable = {}, {}, set()
    for name, tag in refs:
        up, ours = digest(upstream_ref(name, tag)), digest(mirror_ref(name, tag))
        digests[(name, tag)] = up or ours or "?"
        if ours and up and ours != up:
            msg = f"{mirror_ref(name, tag)} differs from upstream ({ours[:19]}… vs {up[:19]}…); not overwriting"
            (errors if (name, tag) in changed else warnings).append(msg)
            status[(name, tag)] = "differs from upstream"
            if (name, tag) in changed:
                unusable.add((name, tag))
        elif ours:
            status[(name, tag)] = "in ECR"
        elif not up:
            errors.append(f"{mirror_ref(name, tag)} is missing and {upstream_ref(name, tag)} does not exist")
            status[(name, tag)] = "missing everywhere"
            unusable.add((name, tag))
        elif not args.apply:
            status[(name, tag)] = "would copy"
        else:
            res = run(["crane", "copy", upstream_ref(name, tag), mirror_ref(name, tag)], check=False)
            _DIGESTS.pop(mirror_ref(name, tag), None)
            if res.returncode == 0 and digest(mirror_ref(name, tag)) == up:
                status[(name, tag)] = "copied"
            else:
                errors.append(f"copy to {mirror_ref(name, tag)} failed: {res.stderr.strip()[-400:]}")
                status[(name, tag)] = "copy failed"
                unusable.add((name, tag))

    # Drop changes whose image is not usable, then build each branch's new values.yaml.
    new_texts, final_changes = {}, {}
    for base, (proposed, changes) in plans.items():
        keep = []
        for name, minor, old, new in changes:
            if (name, new) in unusable:
                if old is None:
                    proposed[name].pop(minor, None)
                else:
                    proposed[name][minor] = old
            else:
                keep.append((name, minor, old, new))
        # A new minor goes in only if both maps end up with it (a scheduler-only key installs nothing).
        for minor in {m for _, m, o, _ in keep if o is None}:
            if not all(minor in proposed[name] for name in COMPONENTS):
                for name, m, o, _ in keep:
                    if m == minor and o is None:
                        proposed[name].pop(minor, None)
                keep = [c for c in keep if not (c[1] == minor and c[2] is None)]
        final_changes[base] = keep
        new_texts[base] = write_maps(texts[base], proposed) if keep else texts[base]

    # Report.
    out.append(f"## Smart-scheduler image sync ({'apply' if args.apply else 'plan only'})\n")
    out.append("Newest upstream GA per minor: kube-scheduler " +
               ", ".join(tag_of(1, m, p) for m, p in sorted(latest["scheduler"].items())[-4:]) +
               "; descheduler " + ", ".join(tag_of(0, m, p) for m, p in sorted(latest["compactor"].items())[-4:]) +
               "\n")
    for base in branches:
        changes = final_changes[base]
        out.append(f"### `{base}`: {len(changes)} change(s)")
        for name, minor, old, new in sorted(changes):
            out.append(f"- {name} 1.{minor}: {old or '(new minor)'} → {new} ({status[(name, new)]})")
        out.append("")
    mapped_top = max(max(p[0]["scheduler"]) for p in plans.values())
    waiting = sorted(m for m in latest["scheduler"] if m > mapped_top and m not in latest["compactor"])
    if waiting:
        out.append("Waiting for descheduler: " + ", ".join(f"1.{m} (no v0.{m})" for m in waiting) + "\n")
    counts = {}
    for s in status.values():
        counts[s] = counts.get(s, 0) + 1
    out.append(f"Mirror check over {len(status)} referenced tags: " +
               ", ".join(f"{v} {k}" for k, v in sorted(counts.items())) + "\n")

    if args.apply:
        actions = []
        for base in branches:
            changes = final_changes[base]
            try:
                sync_branch_pr(args.repo, token, base, texts[base], new_texts[base], changes,
                               digests, run_url, checks_start, actions)
            except RuntimeError as e:
                errors.append(f"{base}: {e}")
        try:
            sync_issues(args.repo, token, latest, mapped_top, run_url, actions)
        except RuntimeError as e:
            errors.append(f"issues: {e}")
        out.append("### Actions\n" + ("\n".join(actions) or "- none") + "\n")

    for w in warnings:
        out.append(f"> warning: {w}")
        print(f"::warning::{w}")
    for e in errors:
        out.append(f"> **error:** {e}")
        print(f"::error::{e}")
    text = "\n".join(out) + "\n"
    print(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(text)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
