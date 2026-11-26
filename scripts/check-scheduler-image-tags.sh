#!/usr/bin/env bash
# Fails when a scheduler or compactor tag in tagByK8sMinor is missing from Sedai's public mirror (public.ecr.aws).
# Optional second argument: sedai-core's smartSchedulerImageTags.yaml, to also check both name the same scheduler tags.
set -euo pipefail

VALUES=${1:-charts/sedai-smart-agent/values.yaml}
CORE_LIST=${2:-}
REGISTRY=https://public.ecr.aws

# Prints "<component> <repository> <minor> <tag>" for image.scheduler and image.compactor in values.yaml.
list_tags() {
  awk '
    /^[^ #]/ { top = $1 }
    top == "image:" && /^  [a-z]+:/ { comp = $1; sub(":", "", comp); repo = ""; inmap = 0 }
    top == "image:" && /^    repository:/ { repo = $2 }
    top == "image:" && /^    tagByK8sMinor:/ { inmap = 1; next }
    top == "image:" && inmap && /^      "?[0-9]+"?:/ {
      minor = $1; gsub(/[":]/, "", minor); tag = $2; gsub(/"/, "", tag)
      if (comp == "scheduler" || comp == "compactor") print comp, repo, minor, tag
      next
    }
    top == "image:" && inmap && !/^      / { inmap = 0 }
  ' "$VALUES"
}

TAGS=$(list_tags)
if [ -z "$TAGS" ]; then
  echo "No scheduler/compactor tags found in $VALUES" >&2
  exit 1
fi

failed=0
while read -r comp repo minor tag; do
  token=$(curl -fsS "$REGISTRY/token/?scope=repository:$repo:pull" | sed -E 's/.*"token":"([^"]+)".*/\1/')
  code=$(curl -s -o /dev/null -w '%{http_code}' -I \
    -H "Authorization: Bearer $token" \
    -H "Accept: application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json" \
    "$REGISTRY/v2/$repo/manifests/$tag")
  if [ "$code" = "200" ]; then
    echo "ok       $comp 1.$minor $repo:$tag"
  else
    echo "MISSING  $comp 1.$minor $repo:$tag (HTTP $code)"
    failed=1
  fi
done <<< "$TAGS"

if [ -n "$CORE_LIST" ]; then
  while read -r comp repo minor tag; do
    # Core moves only the scheduler, so only its list is kept in core.
    [ "$comp" = scheduler ] || continue
    core=$(awk -v key="  schedulerTagByK8sMinor:" -v minor="\"$minor\":" '
      $0 == key { inmap = 1; next }
      inmap && /^  [a-zA-Z]/ { inmap = 0 }
      inmap && $1 == minor { t = $2; gsub(/"/, "", t); print t }
    ' "$CORE_LIST")
    if [ "$core" != "$tag" ]; then
      echo "DIFFERS  $comp 1.$minor chart $tag, core ${core:-none}"
      failed=1
    fi
  done <<< "$TAGS"
fi

exit $failed
