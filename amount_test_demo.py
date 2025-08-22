#!/usr/bin/env python3
"""
Fraud Detection Demo with Different Amount Testing
"""

import pickle
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import time
import threading

# Load the trained model and scaler
print("📦 Loading ML model and scaler...")
with open('backend/fraud_model.pkl', 'rb') as f:
    model = pickle.load(f)
with open('backend/scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

print("✅ Model loaded successfully!")

class FraudHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/' or self.path == '/health':
            self.send_json({
                "status": "healthy",
                "service": "Fraud Detection API",
                "ml_model": "loaded"
            })
        elif self.path == '/stats':
            self.send_json({
                "total_transactions": 0,
                "fraud_transactions": 0,
                "model_status": "active"
            })
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        if self.path == '/api/predict':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # Extract features
                amount = float(data.get('amount', 0))
                hour = int(data.get('hour', 12))
                day = int(data.get('day', 15))
                month = int(data.get('month', 6))
                
                # Create feature array
                features = np.array([[amount, hour, day, month]])
                features_scaled = scaler.transform(features)
                
                # Predict
                fraud_prob = model.predict_proba(features_scaled)[0][1]
                is_fraud = fraud_prob > 0.5
                
                # Determine risk level
                if fraud_prob < 0.3:
                    risk_level = "LOW"
                elif fraud_prob < 0.7:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "HIGH"
                
                self.send_json({
                    "transaction_id": 123,
                    "is_fraud": is_fraud,
                    "fraud_score": round(fraud_prob, 4),
                    "risk_level": risk_level,
                    "amount": amount,
                    "merchant": data.get('merchant', 'Unknown')
                })
                
            except Exception as e:
                self.send_json({'error': str(e)}, 500)
        else:
            self.send_json({'error': 'Not found'}, 404)

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = json.dumps(data)
        self.wfile.write(response.encode('utf-8'))

def test_different_amounts():
    """Test fraud detection with different transaction amounts"""
    base_url = "http://localhost:8000"
    
    print("\n🧪 TESTING FRAUD DETECTION ACROSS AMOUNT RANGES")
    print("=" * 55)
    
    # Test cases for Indian market
    test_cases = [
        {"amount": 50, "merchant": "Tea Stall", "type": "LOW (₹50)"},
        {"amount": 1500, "merchant": "Grocery Store", "type": "NORMAL (₹1,500)"},
        {"amount": 25000, "merchant": "Electronics", "type": "HIGH (₹25,000)"},
        {"amount": 150000, "merchant": "Car Dealer", "type": "EXTREME (₹1,50,000)"}
    ]
    
    # Wait for server to be ready
    time.sleep(2)
    
    for i, test in enumerate(test_cases, 1):
        try:
            transaction_data = {
                "amount": test["amount"],
                "merchant": test["merchant"],
                "hour": 14,
                "day": 15,
                "month": 11
            }
            
            print(f"\n{i}. {test['type']} - {test['merchant']}")
            
            response = requests.post(
                f"{base_url}/api/predict",
                json=transaction_data,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                fraud_score = result.get('fraud_score', 0)
                risk_level = result.get('risk_level', 'UNKNOWN')
                is_fraud = result.get('is_fraud', False)
                
                print(f"   Amount: ₹{test['amount']:,}")
                print(f"   Fraud Score: {fraud_score:.4f}")
                print(f"   Risk Level: {risk_level}")
                print(f"   Fraud Flag: {'🚨 YES' if is_fraud else '✅ NO'}")
                
                # Banking decision simulation
                if fraud_score < 0.3:
                    decision = "✅ APPROVE (Low Risk)"
                elif fraud_score < 0.5:
                    decision = "⚠️ REVIEW (Medium Risk)"
                else:
                    decision = "🚨 BLOCK (High Risk)"
                
                print(f"   Bank Decision: {decision}")
                
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Error: {str(e)[:50]}...")
        
        # Small delay between requests
        time.sleep(0.5)
    
    print(f"\n" + "=" * 55)
    print("🎯 FRAUD DETECTION ANALYSIS COMPLETE!")
    print("💡 Higher amounts don't necessarily mean higher fraud scores.")
    print("📊 The ML model considers multiple factors beyond just amount.")

def start_server():
    """Start the HTTP server"""
    server = HTTPServer(('127.0.0.1', 8000), FraudHandler)
    server.serve_forever()

if __name__ == "__main__":
    print("🚀 Starting Fraud Detection Demo with Amount Testing...")
    
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    print("🔗 Server running at: http://localhost:8000")
    
    # Run the amount testing
    test_different_amounts()
    
    print("\n📡 Server is still running. Press Ctrl+C to stop.")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Demo stopped!")
