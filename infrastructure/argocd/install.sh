#!/bin/bash
# Simple ArgoCD Installation Script
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.9.3/manifests/install.yaml
kubectl apply -f argocd-install.yaml
kubectl apply -f rbac.yaml
kubectl apply -f applications/
echo "ArgoCD installed! Get admin password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
