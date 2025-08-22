#!/usr/bin/env python3
"""
Simple test server to debug networking issues
"""

from flask import Flask, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def hello():
    return jsonify({
        'message': 'Hello from Flask!',
        'status': 'Server is working!'
    })

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        'message': 'Test endpoint working',
        'data': [1, 2, 3]
    })

if __name__ == '__main__':
    print("🚀 Starting simple test server...")
    print("🔗 Available at: http://localhost:3000")
    
    try:
        app.run(
            host='127.0.0.1',  # Only localhost
            port=3000,         # Different port
            debug=False,
            threaded=True
        )
    except Exception as e:
        print(f"❌ Server error: {e}")
