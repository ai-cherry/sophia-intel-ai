import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def monitoring_dashboard():
    return {
        "status": "active",
        "port": 8002,
        "components": {
            "prometheus": "active",
            "grafana": "active",
            "alerting": "active"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
