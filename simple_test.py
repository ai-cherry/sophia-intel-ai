from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get('/')
def root():
    return {'status': 'WORKING'}

@app.get('/health')
def health():
    return {'status': 'OK'}

uvicorn.run(app, host='0.0.0.0', port=8003)
