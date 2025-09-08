#!/usr/bin/env python3
"""
Simple Flask Application

This is a simple Flask application that can be built into a Docker image
and run as a container using our container manager.
"""

from flask import Flask, jsonify
import socket
import os
import platform
import datetime

app = Flask(__name__)

@app.route('/')
def index():
    """Return basic system information as JSON."""
    info = {
        'hostname': socket.gethostname(),
        'ip': socket.gethostbyname(socket.gethostname()),
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'timestamp': datetime.datetime.now().isoformat(),
        'environment': dict(os.environ)
    }
    return jsonify(info)

if __name__ == '__main__':
    app.run(host='${BIND_IP}', port=5000)
