#!/usr/bin/env python3
"""
Test script to upload real fraudTest.csv and get fraud detection results
"""

import requests
import json
import time
import os

def test_real_fraud_upload():
    """Upload real fraudTest.csv and get fraud detection results"""
    
    # File path
    csv_file_path = "C:/Users/KIIT0001/cursor projects/hackth/ProvidedData/6/fraudTest.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return
    
    file_size = os.path.getsize(csv_file_path)
    print(f"📁 File size: {file_size / (1024*1024):.2f} MB")
    
    # Upload URL (assuming server is running on localhost:5000)
    upload_url = "http://localhost:5000/api/enterprise/upload"
    
    try:
        print("🚀 Starting upload of real fraud test data...")
        
        # Upload the file
        with open(csv_file_path, 'rb') as f:
            files = {'file': ('fraudTest.csv', f, 'text/csv')}
            data = {'customer_id': 'test_customer_001'}
            
            print("⏳ Uploading file...")
            response = requests.post(upload_url, files=files, data=data, timeout=300)
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"📊 Analysis ID: {result.get('analysis_id', 'N/A')}")
            
            # Get detailed results
            if 'analysis_id' in result:
                print("\n📈 FRAUD DETECTION RESULTS:")
                print(f"Total Transactions: {result.get('total_transactions', 'N/A')}")
                print(f"Fraud Detected: {result.get('fraud_count', 'N/A')}")
                print(f"Fraud Rate: {result.get('fraud_rate', 0)*100:.2f}%")
                print(f"Risk Assessment: {result.get('risk_assessment', 'N/A')}")
                
                # Show fraud cases if any
                if 'fraud_cases' in result and result['fraud_cases']:
                    print(f"\n🚨 DETECTED FRAUD CASES (showing first 10):")
                    for i, case in enumerate(result['fraud_cases'][:10]):
                        print(f"  {i+1}. Transaction ID: {case.get('transaction_id', 'N/A')}")
                        print(f"     Amount: ${case.get('amount', 'N/A')}")
                        print(f"     Risk Score: {case.get('risk_score', 'N/A')}")
                        print(f"     Reason: {case.get('fraud_reason', 'N/A')}")
                        print()
                
                # Summary
                total_amount = result.get('total_amount', 0)
                fraud_amount = result.get('fraud_amount', 0)
                if total_amount > 0:
                    print(f"💰 Total Transaction Amount: ${total_amount:,.2f}")
                    print(f"🔴 Fraudulent Amount: ${fraud_amount:,.2f}")
                    print(f"💸 Fraud Impact: {(fraud_amount/total_amount)*100:.2f}% of total value")
                
            else:
                print("📄 Raw response:")
                print(json.dumps(result, indent=2))
                
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the fraud detection server is running on localhost:5000")
        print("💡 Start server with: python fraudguard_enterprise.py")
        
    except requests.exceptions.Timeout:
        print("⏰ Upload timed out. File might be too large or server is processing slowly.")
        
    except Exception as e:
        print(f"❌ Error during upload: {str(e)}")

def check_server_status():
    """Check if fraud detection server is running"""
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        print("✅ Server is running!")
        return True
    except:
        print("❌ Server is not running. Starting server...")
        return False

if __name__ == "__main__":
    print("🕵️ Real Fraud Detection Test")
    print("=" * 50)
    
    # Check server status
    if not check_server_status():
        print("Please start the server first:")
        print("python fraudguard_enterprise.py")
        exit(1)
    
    # Run the test
    test_real_fraud_upload()
