SHELL := /bin/bash

.PHONY: env\:dev fly\:sync-secrets deploy\:api cli\:install

ENV ?= sophia/dev
APP ?= sophia-api

env\:dev:
	@echo "Exporting ESC env $(ENV) to .env.master...";
	pulumi env select $(ENV);
	pulumi env get --format=dotenv > .env.master;
	@echo "Done. Source it: 'set -a; source .env.master; set +a'"

fly\:sync-secrets:
	@test -f .esc.env || (echo "Generating .esc.env from ESC $(ENV)..." && pulumi env select $(ENV) && pulumi env get --format=dotenv > .esc.env)
	@echo "Staging secrets to Fly app $(APP)...";
	flyctl secrets import --stage --app $(APP) < .esc.env;
	flyctl secrets deploy --app $(APP);
	@echo "Synced ESC → Fly for $(APP)."

deploy\:api:
	@echo "Deploying API app to Fly...";
	flyctl deploy --config apps/api/fly.toml --strategy bluegreen --app sophia-api;
	@echo "Deployed sophia-api."

cli\:install:
	@chmod +x bin/sophia;
	@echo "CLI installed. Run: ./bin/sophia --help"

.PHONY: clean
clean:
	@echo "Cleaning local artifacts...";
	rm -rf .next || true;
	rm -rf workbench-ui/node_modules || true;
	rm -rf .pytest_cache .ruff_cache __pycache__ || true;
	rm -rf logs/*.log || true;
	find . -name "*.pyc" -delete || true;
	@echo "Done."
