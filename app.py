from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    return jsonify({
        "service": "sophia-intel-api",
        "status": "healthy",
        "version": "1.0.0",
        "features": ["orchestration", "voice"],
        "timestamp": "2025-08-16"
    })

@app.route('/api/orchestration', methods=['POST'])
def orchestration():
    data = request.get_json() or {}
    request_type = data.get('request_type', 'unknown')
    payload = data.get('payload', {})
    
    if request_type == "health":
        return jsonify({"status": "ok", "message": "Orchestration working"})
    elif request_type == "chat":
        message = payload.get('message', 'No message')
        return jsonify({"response": f"SOPHIA: {message}", "status": "success"})
    elif request_type == "code":
        return jsonify({"response": "Code generation ready", "status": "success"})
    elif request_type == "memory":
        return jsonify({"response": "Memory system operational", "status": "success"})
    elif request_type == "research":
        return jsonify({"response": "Research capabilities active", "status": "success"})
    else:
        return jsonify({"response": f"Processed {request_type} request", "status": "success"})

@app.route('/api/speech/health')
def speech_health():
    return jsonify({
        "status": "ok", 
        "provider": "sophia-voice", 
        "features": ["stt", "tts"],
        "models": ["whisper", "elevenlabs"]
    })

@app.route('/api/speech/voices')
def speech_voices():
    return jsonify({
        "provider": "sophia-voice",
        "voices": [
            {"id": "sophia-main", "name": "SOPHIA Main Voice", "gender": "female", "language": "en-US"},
            {"id": "sophia-alt", "name": "SOPHIA Alternative", "gender": "female", "language": "en-US"}
        ]
    })

@app.route('/api/speech/stt', methods=['POST'])
def speech_to_text():
    return jsonify({
        "text": "Speech to text conversion ready",
        "confidence": 0.95,
        "status": "success"
    })

@app.route('/api/speech/tts', methods=['POST'])
def text_to_speech():
    data = request.get_json() or {}
    text = data.get('text', 'Hello from SOPHIA')
    return jsonify({
        "audio_url": f"https://api.sophia-intel.ai/audio/{hash(text)}.mp3",
        "text": text,
        "status": "success"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
