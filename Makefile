# Sophia Ops Makefile — operator shortcuts

.PHONY: help env:dev fly:sync-secrets deploy:api gpu:provision gpu:teardown

help:
	@echo "Targets:"
	@echo "  env:dev                -> Export ESC sophia/dev to .env.master"
	@echo "  fly:sync-secrets ENV=  -> ESC→dotenv→fly secrets import --stage + deploy"
	@echo "  deploy:api ENV=        -> flyctl deploy apps/api/fly.toml (blue/green)"
	@echo "  gpu:provision REGION= TYPE= -> Provision Lambda GPU (placeholder)"
	@echo "  gpu:teardown ID=       -> Teardown Lambda GPU (placeholder)"

env\:dev:
	@echo "Exporting ESC sophia/dev → .env.master"
	pulumi env select sophia/dev
	pulumi env get --format=dotenv > .env.master
	@echo "Wrote .env.master"

fly\:sync-secrets:
	@if [ -z "$(ENV)" ]; then echo "ENV is required (e.g., sophia/prod)"; exit 2; fi
	@echo "Export ESC $(ENV) → .esc.env and import to Fly (staged)"
	pulumi env select $(ENV)
	pulumi env get --format=dotenv > .esc.env
	@[ -z "$(APP)" ] && echo "APP not set; import only" || flyctl secrets import --stage --app $(APP) < .esc.env
	@[ -z "$(APP)" ] && echo "APP not set; secrets deploy skipped" || flyctl secrets deploy --app $(APP)

deploy\:api:
	@if [ -z "$(ENV)" ]; then echo "ENV is required (e.g., sophia/prod)"; exit 2; fi
	@echo "Deploy API with blue/green"
	make fly:sync-secrets ENV=$(ENV) APP=sophia-api
	flyctl deploy --config apps/api/fly.toml --strategy bluegreen --app sophia-api

gpu\:provision:
	@if [ -z "$(REGION)" ] || [ -z "$(TYPE)" ]; then echo "Provide REGION and TYPE"; exit 2; fi
	@echo "Provisioning GPU (Lambda) REGION=$(REGION) TYPE=$(TYPE)"
	@echo "curl -X POST https://cloud.lambdalabs.com/api/v1/instances ... (placeholder)"

gpu\:teardown:
	@if [ -z "$(ID)" ]; then echo "Provide ID"; exit 2; fi
	@echo "Tearing down GPU ID=$(ID)"
	@echo "curl -X DELETE https://cloud.lambdalabs.com/api/v1/instances/$(ID) (placeholder)"

