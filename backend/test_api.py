#!/usr/bin/env python3
"""
Test client to verify the API is working
"""

import requests
import json

def test_api():
    """Test the fraud detection API"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Fraud Detection API...")
    
    try:
        # Test health check
        print("\n1. Testing health check...")
        response = requests.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test stats endpoint
        print("\n2. Testing stats endpoint...")
        response = requests.get(f"{base_url}/api/stats")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test fraud prediction
        print("\n3. Testing fraud prediction...")
        test_transaction = {
            "amount": 15000.0,
            "merchant": "Test Store",
            "card_type": "credit"
        }
        
        response = requests.post(
            f"{base_url}/api/predict",
            json=test_transaction,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Request: {test_transaction}")
        print(f"Response: {response.json()}")
        
        # Test normal transaction
        print("\n4. Testing normal transaction...")
        normal_transaction = {
            "amount": 50.0,
            "merchant": "Coffee Shop",
            "card_type": "debit"
        }
        
        response = requests.post(
            f"{base_url}/api/predict",
            json=normal_transaction,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Request: {normal_transaction}")
        print(f"Response: {response.json()}")
        
        print("\n✅ All API tests completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure it's running on port 8000.")
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == '__main__':
    test_api()
