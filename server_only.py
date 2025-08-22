#!/usr/bin/env python3
"""
Simple server starter for fraud detection API
"""

import sys
sys.path.append('C:/Users/KIIT0001/cursor projects/hackth/backend')

from demo import FraudHandler
from http.server import HTTPServer

def start_server():
    """Start the fraud detection server"""
    print("🚀 Starting Fraud Detection Server...")
    server = HTTPServer(('127.0.0.1', 8000), FraudHandler)
    print("🔗 Server running at: http://localhost:8000")
    print("📡 Ready to receive requests...")
    server.serve_forever()

if __name__ == "__main__":
    start_server()
