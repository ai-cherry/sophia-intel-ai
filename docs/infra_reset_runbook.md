# SOPHIA Infra Reset Runbook (Lambda Cloud + Pulumi)

This runbook takes you from *messy state* → **clean slate** → **reprovisioned** cluster with CI/CD and health checks.

> **Hard rules:** No placeholders; no manual UI. Everything is scripted. If a required env is missing, the script must stop and tell you what to add.

---

## 0) Verify environment

```bash
bash scripts/check_env.sh
```
Checks for non-empty `LAMBDA_CLOUD_API_KEY` and `GH_API_TOKEN`. If `.env.sophia` exists it is sourced automatically.

---

## 1) Final audit (read-only)

```bash
python scripts/audit_current_infra.py
```
Prints all Lambda Cloud instances (ids, IPs, region, status, attached keys) and all registered SSH keys.

---

## 2) Teardown plan and destruction

**Dry-run first:**
```bash
python scripts/teardown_lambda_infra.py
```

**Burn it down (irreversible):**
```bash
python scripts/teardown_lambda_infra.py --confirm-burn-it-down
```
Confirms zero running instances and zero SSH keys after completion.

---

## 3) Generate the canonical SSH key

```bash
bash scripts/gen_ssh_key.sh
```
Creates (or reuses) `~/.ssh/id_ed25519_sophia_prod(.pub)`. The **public** key is registered via Pulumi; the private key never leaves your workstation.

---

## 4) Initialize Pulumi stack and defaults

```bash
cd infra
pulumi stack select dev || pulumi stack init dev
pulumi config set lambda:region us-south-1
pulumi config set lambda:controlType gpu_1x_a100
pulumi config set lambda:workerType  gpu_1x_a100
pulumi config set firewall:allowedSshCidrs "YOUR.WHITELIST.CIDR/32" --secret=false
cd -
```
> Adjust instance types/region as needed. If invalid, Pulumi will fail with the Lambda API error.

---

## 5) Create infra

```bash
bash scripts/pulumi_snapshot.sh export
(cd infra && pulumi up --yes)
```
Outputs: control/worker IPs and `kubeconfig` (as Pulumi secret). CI will use this for deploy.

---

## 6) Deploy via GitHub Actions

Push to `main` **or** run **Actions → Deploy SOPHIA**. The workflow:
1. Builds & pushes GHCR images
2. Runs `pulumi up`
3. Installs cert-manager + ingress
4. Renders and applies K8s manifests
5. Runs end-to-end verification

---

## 7) Verify live (manually)

```bash
bash scripts/verify_live_deployment.sh
```
Checks rollouts, `/healthz`, and (if configured) HTTPS ingress.

---

## 8) Ongoing hygiene

- **PRs:** Infra diffs previewed by **Infra Preview (Pulumi)** workflow.
- **Nightly:** **Infra Drift Detect** flags config drift and opens/updates an issue labeled `infra:drift`.
- **Snapshots:** Use `scripts/pulumi_snapshot.sh export|import` for state backups.
