# Phase 2 Cutover: Kubernetes Sophia → Sophia

Objective
- Move workloads and service discovery from `sophia-*` identifiers to `sophia-*` with zero downtime.

Pre-checks
- Confirm both Services respond: `sophia-orchestrator-service` and `sophia-orchestrator-service`.
- Ensure secrets/configs referenced by Sophia Deployment exist and match.

Step 1 — Apply Sophia resources (parallel)
```bash
# Dry-run
kubectl apply -n sophia-intel-ai -f k8s/base/applications-sophia.yaml --server-side --dry-run=server
# Apply
kubectl apply -n sophia-intel-ai -f k8s/base/applications-sophia.yaml --server-side
# Wait
kubectl rollout status deploy/sophia-orchestrator -n sophia-intel-ai
```

Step 2 — Update traffic sources (if applicable)
- Update Ingress/VirtualService to target `sophia-orchestrator-service`.
- If using internal consumers, update Service names/Env to `sophia-orchestrator-service`.

Step 3 — Monitor
```bash
kubectl get pods -l app.kubernetes.io/component=sophia-orchestrator -n sophia-intel-ai
kubectl logs deploy/sophia-orchestrator -n sophia-intel-ai --tail=100
```

Step 4 — Decommission legacy
```bash
kubectl delete service sophia-orchestrator-service -n sophia-intel-ai
kubectl delete deploy sophia-orchestrator -n sophia-intel-ai
```

Rollback
- Re-apply `sophia-*` resources from `k8s/base/applications.yaml` if issues.

Notes
- Do not remove legacy until all consumers (Ingress, internal services) point to `sophia-*`.
- Align image names and labels in your CI/CD before cutover.
