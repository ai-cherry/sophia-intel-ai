run:
	uvicorn app.api.main:app --host 0.0.0.0 --port 8000

test:
	pytest -k integration -q

smoke:
	curl -sf http://localhost:8000/health && echo OK
	curl -sf http://localhost:8000/api/models | head -c 120; echo

