#!/usr/bin/env python3
"""
Quick Server Status Check - No Interruption
"""
import requests
import time

def quick_test():
    print("🔍 QUICK SERVER STATUS CHECK")
    print("=" * 40)
    
    # Test Backend
    try:
        response = requests.get("http://localhost:8000/api/stats", timeout=2)
        if response.status_code == 200:
            print("✅ Backend (Port 8000): WORKING")
            data = response.json()
            print(f"   Model Status: {data.get('model_status', 'unknown')}")
        else:
            print(f"⚠️ Backend: Status {response.status_code}")
    except:
        print("❌ Backend (Port 8000): NOT RESPONDING")
    
    # Test Frontend
    try:
        response = requests.get("http://localhost:3002", timeout=2)
        if response.status_code == 200:
            print("✅ Frontend (Port 3002): WORKING")
        else:
            print(f"⚠️ Frontend: Status {response.status_code}")
    except:
        print("❌ Frontend (Port 3002): NOT RESPONDING")
    
    # Test API Call
    try:
        api_response = requests.post(
            "http://localhost:8000/api/predict",
            json={"amount": 500, "merchant": "Test Store"},
            headers={"Content-Type": "application/json"},
            timeout=3
        )
        if api_response.status_code == 200:
            result = api_response.json()
            print("✅ API Call: WORKING")
            print(f"   Fraud Score: {result.get('fraud_score', 'N/A')}")
            print(f"   Risk Level: {result.get('risk_level', 'N/A')}")
        else:
            print(f"⚠️ API Call: Status {api_response.status_code}")
    except Exception as e:
        print(f"❌ API Call: FAILED - {e}")
    
    print("\n🎯 Access URLs:")
    print("   Backend API: http://localhost:8000")
    print("   Frontend Dashboard: http://localhost:3002")
    print("\n💡 Both servers should be running in separate terminals!")

if __name__ == "__main__":
    quick_test()
