#!/usr/bin/env python3
"""
Alternative HTTP Server using Python's built-in http.server
This should work better on Windows
"""

import json
import os
import pickle
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.error(f"Error loading model: {e}")
        return None, None

# Load model at startup
ml_model, ml_scaler = load_ml_model()

class FraudDetectionHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_json_response({
                'status': 'healthy',
                'service': 'Fraud Detection API',
                'ml_model': 'loaded' if ml_model else 'fallback',
                'version': '1.0.0'
            })
        
        elif parsed_path.path == '/api/stats':
            self.send_json_response({
                'total_transactions': 0,
                'fraud_transactions': 0,
                'fraud_rate': 0.0,
                'model_status': 'active' if ml_model else 'fallback'
            })
        
        else:
            self.send_json_response({'error': 'Endpoint not found'}, status=404)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/predict':
            try:
                # Read request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # Extract features
                amount = float(data.get('amount', 0))
                merchant = data.get('merchant', 'Unknown')
                
                # Predict fraud
                if ml_model and ml_scaler:
                    # Use real ML model
                    features = [amount] + [0] * 29  # Simplified features
                    features_scaled = ml_scaler.transform([features])
                    fraud_prob = ml_model.predict_proba(features_scaled)[0][1]
                    is_fraud = fraud_prob > 0.5
                else:
                    # Fallback rules
                    is_fraud = amount > 10000
                    fraud_prob = 0.8 if is_fraud else 0.1
                
                response = {
                    'transaction_id': 123,
                    'is_fraud': is_fraud,
                    'fraud_score': round(fraud_prob, 4),
                    'risk_level': 'HIGH' if fraud_prob > 0.7 else 'MEDIUM' if fraud_prob > 0.3 else 'LOW',
                    'amount': amount,
                    'merchant': merchant
                }
                
                self.send_json_response(response)
                
            except Exception as e:
                self.send_json_response({'error': str(e)}, status=500)
        
        else:
            self.send_json_response({'error': 'Endpoint not found'}, status=404)
    
    def send_json_response(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")

def run_server():
    """Start the HTTP server"""
    server_address = ('127.0.0.1', 8000)
    httpd = HTTPServer(server_address, FraudDetectionHandler)
    
    logger.info("🚀 Starting Fraud Detection Server...")
    logger.info(f"🔗 Server available at: http://localhost:8000")
    logger.info(f"🤖 ML Model Status: {'Loaded' if ml_model else 'Fallback Rules'}")
    logger.info("Press Ctrl+C to stop the server")
    
    try:
        print("Server starting... Press Ctrl+C to stop")
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        httpd.server_close()
        logger.info("Server shut down complete")

if __name__ == '__main__':
    run_server()
