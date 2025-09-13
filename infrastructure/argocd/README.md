# ArgoCD GitOps - Simplified Implementation

## Quick Start

```bash
cd infrastructure/argocd
chmod +x install.sh
./install.sh
```

## Essential Commands (Top 10)

```bash
# 1. Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.9.3/manifests/install.yaml

# 2. Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d

# 3. Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# 4. Login via CLI
argocd login localhost:8080 --username admin --password $(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d)

# 5. List applications
kubectl get applications -n argocd

# 6. Sync an application
argocd app sync keda

# 7. Check application status
argocd app get keda

# 8. Rollback an application (automatic - last successful)
argocd app rollback keda

# 9. View application logs
argocd app logs keda

# 10. Delete an application
kubectl delete application keda -n argocd
```

## Architecture

```
ArgoCD (3 replicas for HA)
├── KEDA → infrastructure/keda/gitops/
├── AlertManager → infrastructure/alertmanager/gitops/
├── Sophia → k8s/sophia/
└── Sophia → k8s/sophia/
```

## Files

- `argocd-install.yaml` - HA configuration (3 replicas)
- `rbac.yaml` - Simple RBAC (admin/readonly)
- `applications/` - 4 Application manifests
- `install.sh` - One-command installation

## Rollback

ArgoCD automatically tracks revision history. To rollback:
```bash
argocd app rollback <app-name> <revision-id>
# or to previous version:
argocd app rollback <app-name>
```

## Access UI

Default: https://localhost:8080 (after port-forward)
Username: admin
Password: See command #2 above