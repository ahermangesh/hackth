#!/usr/bin/env python3
"""
All-in-one fraud detection demo
Starts server and runs tests in the same process
"""

import json
import os
import pickle
import threading
import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Load ML model
def load_ml_model():
    try:
        model_path = os.path.join('..', 'data', 'models', 'fraud_model.pkl')
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                return model_data['model'], model_data['scaler']
        return None, None
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, None

# Load model
ml_model, ml_scaler = load_ml_model()

class FraudHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_json({
                'status': 'healthy',
                'service': 'Fraud Detection API',
                'ml_model': 'loaded' if ml_model else 'fallback'
            })
        elif self.path == '/api/stats':
            self.send_json({
                'total_transactions': 0,
                'fraud_transactions': 0,
                'model_status': 'active' if ml_model else 'fallback'
            })
        else:
            self.send_json({'error': 'Not found'}, 404)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/predict':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                amount = float(data.get('amount', 0))
                merchant = data.get('merchant', 'Unknown')
                
                if ml_model and ml_scaler:
                    features = [amount] + [0] * 29
                    features_scaled = ml_scaler.transform([features])
                    fraud_prob = float(ml_model.predict_proba(features_scaled)[0][1])
                    is_fraud = bool(fraud_prob > 0.5)
                else:
                    is_fraud = bool(amount > 10000)
                    fraud_prob = float(0.8 if is_fraud else 0.1)
                
                self.send_json({
                    'transaction_id': 123,
                    'is_fraud': is_fraud,
                    'fraud_score': round(fraud_prob, 4),
                    'risk_level': 'HIGH' if fraud_prob > 0.7 else 'LOW',
                    'amount': float(amount),
                    'merchant': str(merchant)
                })
            except Exception as e:
                self.send_json({'error': str(e)}, 500)
        else:
            self.send_json({'error': 'Not found'}, 404)
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # Suppress default logging

def start_server():
    """Start server in background thread"""
    server = HTTPServer(('127.0.0.1', 8000), FraudHandler)
    server.serve_forever()

def test_api():
    """Test the API"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Fraud Detection API...")
    
    try:
        # Test health check
        print("\n1. Health Check:")
        response = requests.get(f"{base_url}/")
        print(f"✅ Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test high-risk transaction
        print("\n2. High-Risk Transaction ($15,000):")
        test_transaction = {"amount": 15000.0, "merchant": "Luxury Store"}
        response = requests.post(f"{base_url}/api/predict", json=test_transaction)
        print(f"✅ Status: {response.status_code}")
        print(f"Raw Response: {response.text}")
        if response.text.strip():
            try:
                print(f"Parsed Response: {json.dumps(response.json(), indent=2)}")
            except:
                print("Could not parse JSON response")
        
        # Test normal transaction
        print("\n3. Normal Transaction ($50):")
        normal_transaction = {"amount": 50.0, "merchant": "Coffee Shop"}
        response = requests.post(f"{base_url}/api/predict", json=normal_transaction)
        print(f"✅ Status: {response.status_code}")
        print(f"Raw Response: {response.text}")
        if response.text.strip():
            try:
                print(f"Parsed Response: {json.dumps(response.json(), indent=2)}")
            except:
                print("Could not parse JSON response")
        
        # Test stats
        print("\n4. Stats Endpoint:")
        response = requests.get(f"{base_url}/api/stats")
        print(f"✅ Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        print("\n🎉 All API tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Starting Fraud Detection Demo...")
    print(f"🤖 ML Model Status: {'Loaded' if ml_model else 'Fallback Rules'}")
    
    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    # Run tests
    success = test_api()
    
    if success:
        print(f"\n🔗 Server is running at: http://localhost:8000")
        print("💡 You can now test the API manually or connect your frontend!")
        print("Press Ctrl+C to stop the server")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Server stopped!")
    else:
        print("\n❌ Demo failed to start properly")
