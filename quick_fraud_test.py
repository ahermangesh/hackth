#!/usr/bin/env python3
"""
Quick Manual Test - Just test a few amounts to show the system working
"""

import requests
import json
import time

# Test data
tests = [
    {"amount": 50, "merchant": "Coffee Shop", "category": "LOW"},
    {"amount": 1500, "merchant": "Grocery Store", "category": "NORMAL"},
    {"amount": 25000, "merchant": "Electronics", "category": "HIGH"},
    {"amount": 150000, "merchant": "Car Dealer", "category": "EXTREME"}
]

print("🧪 FRAUD DETECTION TEST RESULTS")
print("=" * 45)

for test in tests:
    try:
        # Give server time
        time.sleep(1)
        
        # Make request
        response = requests.post(
            "http://localhost:8000/api/predict",
            json={
                "amount": test["amount"],
                "merchant": test["merchant"],
                "hour": 14,
                "day": 15,
                "month": 11
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            score = result.get('fraud_score', 0)
            is_fraud = result.get('is_fraud', False)
            
            print(f"\n{test['category']} AMOUNT: ₹{test['amount']:,}")
            print(f"Merchant: {test['merchant']}")
            print(f"Fraud Score: {score:.4f}")
            print(f"Risk Level: {'🚨 HIGH' if is_fraud else '✅ LOW'}")
        else:
            print(f"\n❌ {test['category']}: Error {response.status_code}")
            
    except Exception as e:
        print(f"\n💥 {test['category']}: {str(e)[:50]}...")

print("\n" + "=" * 45)
print("🎯 Fraud detection tested across amount ranges!")
