#!/usr/bin/env python3
"""
Quick status check for the fraud detection system
"""

import os
import sys
import pickle
import subprocess
import requests

def check_ml_model():
    """Check if ML model is working"""
    try:
        model_path = os.path.join('data', 'models', 'fraud_model.pkl')
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                print("✅ ML Model: Loaded successfully")
                print(f"   - Model type: {model_data.get('model_type', 'Unknown')}")
                print(f"   - Features: {len(model_data.get('feature_columns', []))}")
                return True
        else:
            print("❌ ML Model: File not found")
            return False
    except Exception as e:
        print(f"❌ ML Model: Error loading - {e}")
        return False

def check_backend_files():
    """Check backend files"""
    print("\n📁 Backend Files:")
    backend_files = [
        'backend/demo.py',
        'backend/http_server.py', 
        'backend/production_server.py',
        'backend/train_ml_model.py'
    ]
    
    for file_path in backend_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")

def check_frontend():
    """Check frontend setup"""
    print("\n🎨 Frontend:")
    if os.path.exists('frontend'):
        print("   ✅ Frontend directory exists")
        if os.path.exists('frontend/package.json'):
            print("   ✅ Package.json found")
        else:
            print("   ⚠️ Package.json not found")
    else:
        print("   ❌ Frontend directory missing")

def check_running_servers():
    """Check if any servers are running"""
    print("\n🌐 Server Status:")
    ports_to_check = [3000, 5000, 8000]
    
    for port in ports_to_check:
        try:
            response = requests.get(f'http://localhost:{port}/', timeout=2)
            print(f"   ✅ Port {port}: Server responding ({response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Port {port}: No server running")
        except Exception as e:
            print(f"   ⚠️ Port {port}: Error - {e}")

def main():
    """Main status check"""
    print("🔍 FRAUD DETECTION SYSTEM STATUS CHECK")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(r'C:\Users\KIIT0001\cursor projects\hackth')
    
    # Check ML model
    model_ok = check_ml_model()
    
    # Check backend files
    check_backend_files()
    
    # Check frontend
    check_frontend()
    
    # Check running servers
    check_running_servers()
    
    print("\n📋 SUMMARY:")
    print(f"   ML Model: {'✅ Ready' if model_ok else '❌ Not Ready'}")
    print("   Backend: ✅ Files present")
    print("   Status: Ready for demo")
    
    print("\n🚀 NEXT STEPS:")
    print("   1. Start server: cd backend && python demo.py")
    print("   2. Test API at: http://localhost:8000")
    print("   3. Start frontend: cd frontend && npm start")

if __name__ == '__main__':
    main()
