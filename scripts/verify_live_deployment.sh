#!/usr/bin/env bash
set -euo pipefail

NS=${NS:-sophia}
TIMEOUT=${TIMEOUT:-300}

echo "==> Verifying Kubernetes connectivity"
kubectl get ns "$NS" >/dev/null

echo "==> Waiting for deployments to be available"
kubectl -n "$NS" rollout status deploy/api --timeout=${TIMEOUT}s
kubectl -n "$NS" rollout status deploy/dashboard --timeout=${TIMEOUT}s
kubectl -n "$NS" rollout status deploy/mcp-code-context --timeout=${TIMEOUT}s

echo "==> Checking /healthz for api and dashboard (cluster-internal)"
kubectl -n "$NS" run curl-test --rm -i --tty --restart=Never --image=curlimages/curl:8.10.1 -- \
  sh -lc 'curl -sSf http://api/healthz && curl -sSf http://dashboard/healthz' >/dev/null

if [[ -n "${INGRESS_DOMAIN:-}" ]]; then
  echo "==> Checking HTTPS via ingress: https://${INGRESS_DOMAIN}/healthz"
  curl -fsS --retry 10 --retry-all-errors --retry-delay 3 "https://${INGRESS_DOMAIN}/healthz" >/dev/null || {
    echo "::error::Ingress HTTPS check failed"
    exit 1
  }
fi

echo "✅ Verification passed"
