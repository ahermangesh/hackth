#!/usr/bin/env python3
"""
Simple Fraud Detection Test - Tests a few key transactions across different risk levels
"""

import requests
import json
import time

def simple_fraud_test():
    base_url = "http://localhost:8000"
    
    print("🎯 SIMPLE FRAUD DETECTION TEST")
    print("=" * 40)
    
    # Test cases representing different risk levels
    test_transactions = [
        {"amount": 50, "merchant": "Coffee Shop", "category": "LOW (₹50)"},
        {"amount": 1500, "merchant": "Grocery Store", "category": "NORMAL (₹1,500)"},
        {"amount": 25000, "merchant": "Electronics", "category": "HIGH (₹25,000)"},
        {"amount": 150000, "merchant": "Car Dealer", "category": "EXTREME (₹1,50,000)"}
    ]
    
    # Wait for server to fully start
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Test health check first
    try:
        health_response = requests.get(f"{base_url}/stats", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is healthy and ready!")
        else:
            print(f"⚠️ Server health check returned: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return
    
    print("\n🧪 Testing different transaction amounts:")
    print("-" * 40)
    
    for i, tx in enumerate(test_transactions, 1):
        try:
            # Prepare transaction data
            transaction_data = {
                "amount": tx["amount"],
                "merchant": tx["merchant"],
                "hour": 14,  # Afternoon
                "day": 15,   # Mid-month
                "month": 11  # November
            }
            
            print(f"\n{i}. {tx['category']} - {tx['merchant']}")
            print(f"   Amount: ₹{tx['amount']:,}")
            
            response = requests.post(
                f"{base_url}/predict",
                json=transaction_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                fraud_score = result.get('fraud_score', 0)
                risk_level = result.get('risk_level', 'UNKNOWN')
                is_fraud = result.get('is_fraud', False)
                
                print(f"   Fraud Score: {fraud_score:.4f}")
                print(f"   Risk Level: {risk_level}")
                print(f"   Fraud Flag: {'🚨 YES' if is_fraud else '✅ NO'}")
                
                # Risk interpretation
                if fraud_score < 0.3:
                    interpretation = "Very Low Risk"
                elif fraud_score < 0.5:
                    interpretation = "Low Risk"
                elif fraud_score < 0.7:
                    interpretation = "Medium Risk"
                else:
                    interpretation = "High Risk"
                
                print(f"   Bank Decision: {interpretation}")
                
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timeout")
        except Exception as e:
            print(f"   💥 Error: {str(e)}")
        
        # Wait between requests to avoid overwhelming server
        if i < len(test_transactions):
            time.sleep(1)
    
    print("\n" + "=" * 40)
    print("🏁 Testing completed!")
    print("💡 This demonstrates fraud detection across different amount ranges")

if __name__ == "__main__":
    simple_fraud_test()
