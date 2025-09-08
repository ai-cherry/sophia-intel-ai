# ArgoCD GitOps Technical Specifications - Part 2
## Sophia-Intel-AI Platform GitOps Integration (Continued)

---

## 5. Sync Policies & Strategies

### 5.1 Automated Sync Policies

```yaml
# Production Sync Policy with Safety Controls
apiVersion: v1
kind: ConfigMap
metadata:
  name: sync-policies
  namespace: argocd
data:
  production.yaml: |
    syncPolicy:
      automated:
        prune: false  # Never auto-prune in production
        selfHeal: true
        allowEmpty: false
      syncOptions:
      - CreateNamespace=false  # Namespaces pre-created
      - PrunePropagationPolicy=foreground
      - PruneLast=true
      - RespectIgnoreDifferences=true
      - ApplyOutOfSyncOnly=true
      - ServerSideApply=true  # For large objects
      - Validate=true
      - FailOnSharedResource=true
      retry:
        limit: 3
        backoff:
          duration: 10s
          factor: 2
          maxDuration: 5m
  
  staging.yaml: |
    syncPolicy:
      automated:
        prune: true
        selfHeal: true
        allowEmpty: false
      syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - ApplyOutOfSyncOnly=true
      retry:
        limit: 5
        backoff:
          duration: 5s
          factor: 2
          maxDuration: 3m
  
  development.yaml: |
    syncPolicy:
      automated:
        prune: true
        selfHeal: true
        allowEmpty: true  # Allow empty in dev
      syncOptions:
      - CreateNamespace=true
      - Force=true  # Force sync in dev
      retry:
        limit: 10
        backoff:
          duration: 2s
          factor: 2
          maxDuration: 1m
```

### 5.2 Resource Hooks

```yaml
# Pre-sync Database Migration Hook
apiVersion: batch/v1
kind: Job
metadata:
  name: database-migration
  namespace: artemis-system
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-weight: "10"
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migrate
        image: ghcr.io/sophia-intel-ai/db-migrator:v1.0.0
        command: ["migrate", "--up"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: artemis-credentials
              key: database-url
---
# Post-sync Smoke Test Hook
apiVersion: batch/v1
kind: Job
metadata:
  name: smoke-tests
  namespace: artemis-system
  annotations:
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-weight: "20"
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: test
        image: ghcr.io/sophia-intel-ai/smoke-tests:v1.0.0
        command: ["pytest", "tests/smoke/"]
        env:
        - name: TARGET_URL
          value: "http://artemis-orchestrator.artemis-system.svc.cluster.local"
```

### 5.3 Progressive Sync Strategies

```yaml
# Canary Deployment with Flagger
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: artemis-orchestrator
  namespace: artemis-system
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: artemis-orchestrator
  progressDeadlineSeconds: 600
  service:
    port: 8080
    targetPort: 8080
    gateways:
    - istio-system/artemis-gateway
    hosts:
    - artemis.sophia-artemis.local
  analysis:
    interval: 30s
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 30s
    webhooks:
    - name: acceptance-test
      type: pre-rollout
      url: http://flagger-loadtester.artemis-system/
      timeout: 30s
      metadata:
        type: bash
        cmd: "curl -sd 'test' http://artemis-orchestrator-canary.artemis-system:8080/health"
    - name: load-test
      type: rollout
      url: http://flagger-loadtester.artemis-system/
      metadata:
        cmd: "hey -z 2m -q 10 -c 2 http://artemis-orchestrator-canary.artemis-system:8080/"
```

### 5.4 Rollback Triggers and Strategies

```yaml
# Automated Rollback Configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: rollback-config
  namespace: argocd
data:
  triggers.yaml: |
    rollbackTriggers:
      - metric: error_rate
        threshold: 5  # 5% error rate
        duration: 2m
        action: immediate_rollback
      
      - metric: p95_latency
        threshold: 1000  # 1000ms
        duration: 5m
        action: immediate_rollback
      
      - metric: memory_usage
        threshold: 90  # 90%
        duration: 10m
        action: gradual_rollback
      
      - metric: pod_restarts
        threshold: 3
        duration: 5m
        action: immediate_rollback
      
      - alert: CriticalServiceDown
        action: immediate_rollback
        
  strategies.yaml: |
    rollbackStrategies:
      immediate_rollback:
        type: "revert"
        steps:
          - pause_new_sync
          - capture_metrics
          - revert_to_previous
          - verify_health
          - notify_team
        timeout: 30s
        
      gradual_rollback:
        type: "progressive"
        steps:
          - reduce_traffic_50
          - wait: 2m
          - check_metrics
          - reduce_traffic_100
          - revert_deployment
        timeout: 10m
        
      emergency_rollback:
        type: "force"
        steps:
          - force_sync_previous
          - skip_hooks
          - immediate_apply
        timeout: 10s
```

---

## 6. Security & RBAC

### 6.1 ArgoCD RBAC Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly
  policy.csv: |
    # Platform Admins - Full access
    p, role:platform-admin, applications, *, */*, allow
    p, role:platform-admin, clusters, *, *, allow
    p, role:platform-admin, repositories, *, *, allow
    p, role:platform-admin, certificates, *, *, allow
    p, role:platform-admin, projects, *, *, allow
    p, role:platform-admin, accounts, *, *, allow
    p, role:platform-admin, gpgkeys, *, *, allow
    p, role:platform-admin, exec, create, */*, allow
    g, sophia-intel-ai:platform-admins, role:platform-admin
    
    # Artemis Team - Manage Artemis apps
    p, role:artemis-team, applications, get, artemis/*, allow
    p, role:artemis-team, applications, sync, artemis/*, allow
    p, role:artemis-team, applications, action/*, artemis/*, allow
    p, role:artemis-team, logs, get, artemis/*, allow
    p, role:artemis-team, exec, create, artemis/*, deny  # No exec in prod
    g, sophia-intel-ai:artemis-developers, role:artemis-team
    
    # Sophia Team - Manage Sophia apps
    p, role:sophia-team, applications, get, sophia/*, allow
    p, role:sophia-team, applications, sync, sophia/*, allow
    p, role:sophia-team, applications, action/*, sophia/*, allow
    p, role:sophia-team, logs, get, sophia/*, allow
    g, sophia-intel-ai:sophia-developers, role:sophia-team
    
    # DevOps Team - Infrastructure management
    p, role:devops, applications, *, infrastructure/*, allow
    p, role:devops, clusters, get, *, allow
    p, role:devops, repositories, *, *, allow
    p, role:devops, projects, get, *, allow
    g, sophia-intel-ai:devops, role:devops
    
    # Read-only users
    p, role:readonly, applications, get, */*, allow
    p, role:readonly, projects, get, *, allow
    p, role:readonly, clusters, get, *, allow
    p, role:readonly, repositories, get, *, allow
    g, sophia-intel-ai:developers, role:readonly
    
    # CI/CD Service Account
    p, role:ci-cd, applications, sync, */*, allow
    p, role:ci-cd, applications, get, */*, allow
    p, role:ci-cd, applications, action/apps/Deployment/restart, */*, allow
    g, ci-cd-bot, role:ci-cd
  
  scopes: '[groups, email]'
```

### 6.2 SSO Integration (OAuth2/OIDC)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  url: https://argocd.sophia-intel-ai.com
  
  # OIDC Configuration (Example with Okta)
  oidc.config: |
    name: Okta
    issuer: https://sophia-intel-ai.okta.com
    clientId: $oidc.okta.clientId
    clientSecret: $oidc.okta.clientSecret
    requestedScopes: ["openid", "profile", "email", "groups"]
    requestedIDTokenClaims: {"groups": {"essential": true}}
    
  # Alternative: GitHub OAuth
  dex.config: |
    connectors:
    - type: github
      id: github
      name: GitHub
      config:
        clientID: $dex.github.clientId
        clientSecret: $dex.github.clientSecret
        orgs:
        - name: sophia-intel-ai
          teams:
          - platform-admins
          - artemis-developers
          - sophia-developers
          - devops
    
    # LDAP Integration (if needed)
    - type: ldap
      id: ldap
      name: LDAP
      config:
        host: ldap.sophia-intel-ai.com:636
        bindDN: cn=admin,dc=sophia-intel-ai,dc=com
        bindPW: $dex.ldap.bindPW
        usernamePrompt: Username
        userSearch:
          baseDN: ou=users,dc=sophia-intel-ai,dc=com
          filter: "(objectClass=person)"
          username: uid
          idAttr: uid
          emailAttr: mail
          nameAttr: cn
        groupSearch:
          baseDN: ou=groups,dc=sophia-intel-ai,dc=com
          filter: "(objectClass=groupOfNames)"
          userMatchers:
          - userAttr: DN
            groupAttr: member
          nameAttr: cn
```

### 6.3 Repository Access Controls

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: repo-credentials
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
type: Opaque
stringData:
  type: git
  url: https://github.com/sophia-intel-ai/gitops
  username: argocd-bot
  password: <github-token>
  insecure: "false"
  enableLfs: "true"
---
# SSH Key-based Authentication
apiVersion: v1
kind: Secret
metadata:
  name: repo-ssh-credentials
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repo-creds
type: Opaque
stringData:
  type: git
  url: git@github.com:sophia-intel-ai
  sshPrivateKey: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    <private-key-content>
    -----END OPENSSH PRIVATE KEY-----
```

### 6.4 Network Policies

```yaml
# ArgoCD Server Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: argocd-server-network-policy
  namespace: argocd
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: argocd-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: istio-system  # Ingress gateway
    ports:
    - protocol: TCP
      port: 8080
    - protocol: TCP
      port: 8083
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/part-of: argocd  # Internal ArgoCD traffic
  egress:
  - to:
    - podSelector:
        matchLabels:
          app.kubernetes.io/part-of: argocd
  - to:
    - namespaceSelector: {}  # Allow cluster access
    ports:
    - protocol: TCP
      port: 443  # Kubernetes API
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 443  # External Git repos
---
# Application Controller Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: argocd-application-controller-network-policy
  namespace: argocd
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: argocd-application-controller
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector: {}  # Full cluster access for deployments
  - to:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 443  # Git repos and container registries
```

---

## 7. Monitoring & Notifications

### 7.1 Prometheus Integration

```yaml
# ServiceMonitor for ArgoCD Metrics
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argocd-metrics
  namespace: argocd
  labels:
    prometheus: kube-prometheus
spec:
  selector:
    matchLabels:
      app.kubernetes.io/part-of: argocd
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
---
# PrometheusRule for ArgoCD Alerts
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: argocd-alerts
  namespace: argocd
spec:
  groups:
  - name: argocd.rules
    interval: 30s
    rules:
    - alert: ArgoAppHealthDegraded
      expr: |
        argocd_app_health_status{health_status!="Healthy"} > 0
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "ArgoCD Application {{$labels.name}} is {{$labels.health_status}}"
        description: "Application {{$labels.name}} in {{$labels.namespace}} has been {{$labels.health_status}} for more than 5 minutes"
    
    - alert: ArgoAppSyncFailed
      expr: |
        argocd_app_sync_total{phase="Failed"} > 0
      for: 2m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "ArgoCD Application {{$labels.name}} sync failed"
        description: "Application {{$labels.name}} sync has failed in {{$labels.namespace}}"
    
    - alert: ArgocdServerNotReady
      expr: |
        up{job="argocd-server-metrics"} == 0
      for: 5m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "ArgoCD Server is down"
        description: "ArgoCD Server has been down for more than 5 minutes"
```

### 7.2 Deployment Metrics and Dashboards

```yaml
# Grafana Dashboard ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-dashboard
  namespace: monitoring
data:
  dashboard.json: |
    {
      "dashboard": {
        "title": "ArgoCD GitOps Metrics",
        "panels": [
          {
            "title": "Application Sync Status",
            "targets": [
              {
                "expr": "sum by (name, sync_status) (argocd_app_info)"
              }
            ]
          },
          {
            "title": "Deployment Frequency",
            "targets": [
              {
                "expr": "rate(argocd_app_sync_total[1h])"
              }
            ]
          },
          {
            "title": "Sync Duration",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, argocd_app_reconcile_bucket)"
              }
            ]
          },
          {
            "title": "Failed Deployments",
            "targets": [
              {
                "expr": "sum(increase(argocd_app_sync_total{phase=\"Failed\"}[1h]))"
              }
            ]
          },
          {
            "title": "Rollback Events",
            "targets": [
              {
                "expr": "sum(increase(argocd_app_sync_total{phase=\"Rollback\"}[1h]))"
              }
            ]
          }
        ]
      }
    }
```

### 7.3 Notification Channels

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  # Slack Configuration
  service.slack: |
    token: $slack-token
    signingSecret: $slack-signing-secret
  
  # Email Configuration
  service.email: |
    host: smtp.sophia-intel-ai.com
    port: 587
    from: argocd@sophia-intel-ai.com
    username: $email-username
    password: $email-password
  
  # Webhook Configuration
  service.webhook.deployment-tracker: |
    url: https://deployment-tracker.sophia-intel-ai.com/webhooks/argocd
    headers:
    - name: Authorization
      value: Bearer $webhook-token
  
  # Templates
  template.app-deployed: |
    email:
      subject: |
        {{.app.metadata.name}} deployed successfully
    message: |
      Application {{.app.metadata.name}} has been successfully deployed.
      Details:
      - Environment: {{.app.metadata.labels.environment}}
      - Version: {{.app.status.sync.revision}}
      - Time: {{.app.status.operationState.finishedAt}}
    slack:
      attachments: |
        [{
          "color": "good",
          "title": "✅ Deployment Successful",
          "text": "{{.app.metadata.name}} deployed to {{.app.spec.destination.namespace}}",
          "fields": [{
            "title": "Version",
            "value": "{{.app.status.sync.revision}}",
            "short": true
          }, {
            "title": "Environment",
            "value": "{{.app.metadata.labels.environment}}",
            "short": true
          }]
        }]
  
  template.app-sync-failed: |
    email:
      subject: |
        ❌ {{.app.metadata.name}} sync failed
    message: |
      Application {{.app.metadata.name}} sync has failed.
      Error: {{.app.status.operationState.message}}
    slack:
      attachments: |
        [{
          "color": "danger",
          "title": "❌ Sync Failed",
          "text": "{{.app.metadata.name}} failed to sync",
          "fields": [{
            "title": "Error",
            "value": "{{.app.status.operationState.message}}",
            "short": false
          }]
        }]
  
  # Triggers
  trigger.on-deployed: |
    - when: app.status.operationState.phase in ['Succeeded'] and app.status.health.status == 'Healthy'
      send: [app-deployed]
  
  trigger.on-sync-failed: |
    - when: app.status.operationState.phase in ['Error', 'Failed']
      send: [app-sync-failed]
  
  # Subscriptions
  subscriptions: |
    - recipients:
      - slack:platform-alerts
      - email:platform-team@sophia-intel-ai.com
      selector: environment=production
      triggers:
      - on-deployed
      - on-sync-failed
    
    - recipients:
      - slack:artemis-team
      selector: app.kubernetes.io/part-of=artemis-suite
      triggers:
      - on-deployed
      - on-sync-failed
    
    - recipients:
      - slack:sophia-team
      selector: app.kubernetes.io/part-of=sophia-suite
      triggers:
      - on-deployed
      - on-sync-failed
```

### 7.4 Audit Logging

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-server-config
  namespace: argocd
data:
  # Enable audit logging
  server.audit.enabled: "true"
  server.audit.logpath: "/tmp/argocd-audit.log"
  server.audit.maxage: "7"
  server.audit.maxsize: "100"
  server.audit.maxbackups: "5"
  
  # Audit log shipping to external system
  fluentbit.conf: |
    [INPUT]
        Name              tail
        Path              /tmp/argocd-audit.log
        Parser            json
        Tag               argocd.audit
        Refresh_Interval  5
    
    [OUTPUT]
        Name              es
        Match             argocd.audit
        Host              elasticsearch.monitoring.svc.cluster.local
        Port              9200
        Index             argocd-audit
        Type              _doc
        Retry_Limit       5
```

---

## 8. Deployment Automation

### 8.1 CI/CD Pipeline Integration

```yaml
# GitHub Actions Workflow
name: Deploy to Production
on:
  push:
    branches:
      - main
    paths:
      - 'services/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Update Image Tag
      run: |
        cd services/artemis/orchestrator/overlays/production
        kustomize edit set image artemis-orchestrator=ghcr.io/sophia-intel-ai/artemis-orchestrator:${{ github.sha }}
    
    - name: Commit and Push
      run: |
        git config user.name "GitHub Actions"
        git config user.email "actions@github.com"
        git add .
        git commit -m "Update artemis-orchestrator to ${{ github.sha }}"
        git push
    
    - name: Sync ArgoCD Application
      run: |
        argocd app sync artemis-orchestrator-production \
          --auth-token ${{ secrets.ARGOCD_TOKEN }} \
          --server argocd.sophia-intel-ai.com \
          --grpc-web
    
    - name: Wait for Rollout
      run: |
        argocd app wait artemis-orchestrator-production \
          --auth-token ${{ secrets.ARGOCD_TOKEN }} \
          --server argocd.sophia-intel-ai.com \
          --grpc-web \
          --timeout 600 \
          --health
```

### 8.2 ArgoCD Image Updater

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-image-updater-config
  namespace: argocd
data:
  registries.conf: |
    registries:
    - name: GitHub Container Registry
      prefix: ghcr.io
      api_url: https://ghcr.io
      credentials: pullsecret:argocd/ghcr-credentials
      default: true
    - name: DockerHub
      prefix: docker.io
      api_url: https://registry-1.docker.io
      credentials: pullsecret:argocd/dockerhub-credentials
  
  log.level: "info"
---
# Image Update Policy Annotations
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: artemis-orchestrator
  namespace: argocd
  annotations:
    argocd-image-updater.argoproj.io/image-list: |
      artemis=ghcr.io/sophia-intel-ai/artemis-orchestrator
    argocd-image-updater.argoproj.io/artemis.update-strategy: semver
    argocd-image-updater.argoproj.io/artemis.allow-tags: "regexp:^v[0-9]+\\.[0-9]+\\.[0-9]+$"
    argocd-image-updater.argoproj.io/write-back-method: git
    argocd-image-updater.argoproj.io/git-branch: image-updates
spec:
  # Application spec...
```

### 8.3 Promotion Workflows

```yaml
# Promotion Pipeline ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: promotion-workflow
  namespace: argocd
data:
  workflow.yaml: |
    stages:
      - name: development
        auto_promote: true
        promotion_criteria:
          - test_pass_rate: 100
          - code_coverage: 80
          - security_scan: pass
        next_stage: staging
        
      - name: staging
        auto_promote: true
        promotion_criteria:
          - smoke_tests: pass
          - performance_baseline: met
          - integration_tests: pass
          - soak_duration: 24h
        next_stage: production
        approval_required: false
        
      - name: production
        auto_promote: false
        promotion_criteria:
          - staging_stable: 48h
          - change_advisory: approved
          - runbook_updated: true
        approval_required: true
        approvers:
          - platform-team
          - service-owner
```

### 8.4 Drift Detection and Remediation

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: drift-detector
  namespace: argocd
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: argocd-drift-detector
          containers:
          - name: detector
            image: ghcr.io/sophia-intel-ai/argocd-drift-detector:v1.0.0
            command:
            - /bin/sh
            - -c
            - |
              # Check for drift in all applications
              for app in $(argocd app list -o name); do
                STATUS=$(argocd app get $app -o json | jq -r '.status.sync.status')
                if [ "$STATUS" = "OutOfSync" ]; then
                  echo "Drift detected in $app"
                  
                  # Auto-remediate if enabled
                  AUTO_SYNC=$(argocd app get $app -o json | jq -r '.spec.syncPolicy.automated.selfHeal')
                  if [ "$AUTO_SYNC" = "false" ]; then
                    # Send notification
                    curl -X POST $SLACK_WEBHOOK -d "{\"text\":\"Drift detected in $app\"}"
                  fi
                fi
              done
            env:
            - name: ARGOCD_SERVER
              value: argocd-server.argocd.svc.cluster.local
            - name: SLACK_WEBHOOK
              valueFrom:
                secretKeyRef:
                  name: notifications
                  key: slack-webhook
```

---

*Continued in Part 3...*