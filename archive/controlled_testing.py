#!/usr/bin/env python3
"""
Controlled Fraud Detection Testing - Tests low, high, and normal transaction amounts
with rate limiting to prevent server overload
"""

import requests
import json
import time
from datetime import datetime

def test_fraud_api():
    base_url = "http://localhost:8000"
    
    print("🔍 CONTROLLED FRAUD DETECTION TESTING")
    print("=" * 50)
    
    # Test categories with realistic amounts for Indian market
    test_cases = [
        {
            "category": "LOW AMOUNT TRANSACTIONS (₹1-100)",
            "transactions": [
                {"amount": 10, "merchant": "Tea Stall", "description": "Chai purchase"},
                {"amount": 25, "merchant": "Auto Rickshaw", "description": "Short ride"},
                {"amount": 50, "merchant": "Street Food", "description": "Lunch"},
                {"amount": 75, "merchant": "Bus Ticket", "description": "Local transport"},
                {"amount": 100, "merchant": "Grocery Store", "description": "Small items"}
            ]
        },
        {
            "category": "NORMAL AMOUNT TRANSACTIONS (₹500-5000)",
            "transactions": [
                {"amount": 500, "merchant": "Restaurant", "description": "Dinner for two"},
                {"amount": 1200, "merchant": "Grocery Supermarket", "description": "Weekly shopping"},
                {"amount": 2500, "merchant": "Clothing Store", "description": "Shirt purchase"},
                {"amount": 3500, "merchant": "Electronics Store", "description": "Mobile accessories"},
                {"amount": 4800, "merchant": "Medical Store", "description": "Medicine"}
            ]
        },
        {
            "category": "HIGH AMOUNT TRANSACTIONS (₹15000-80000)",
            "transactions": [
                {"amount": 15000, "merchant": "Furniture Store", "description": "Home appliance"},
                {"amount": 25000, "merchant": "Electronics", "description": "Laptop purchase"},
                {"amount": 45000, "merchant": "Gold Jewelry", "description": "Festival purchase"},
                {"amount": 65000, "merchant": "Travel Agency", "description": "Vacation booking"},
                {"amount": 80000, "merchant": "Bike Showroom", "description": "Two-wheeler"}
            ]
        },
        {
            "category": "EXTREME AMOUNT TRANSACTIONS (₹100000+)",
            "transactions": [
                {"amount": 100000, "merchant": "Real Estate", "description": "Property deposit"},
                {"amount": 150000, "merchant": "Car Dealer", "description": "Car down payment"},
                {"amount": 200000, "merchant": "Investment Firm", "description": "Mutual fund"},
                {"amount": 350000, "merchant": "Education Loan", "description": "Course fees"},
                {"amount": 500000, "merchant": "Medical Hospital", "description": "Surgery payment"}
            ]
        }
    ]
    
    all_results = []
    
    for category_data in test_cases:
        category = category_data["category"]
        transactions = category_data["transactions"]
        
        print(f"\n🧪 Testing: {category}")
        print("-" * 40)
        
        category_results = []
        
        for i, tx in enumerate(transactions, 1):
            # Rate limiting - wait between requests
            if i > 1:
                time.sleep(0.5)  # 500ms delay between requests
            
            try:
                # Prepare transaction data
                transaction_data = {
                    "amount": tx["amount"],
                    "merchant": tx["merchant"],
                    "hour": 14,  # Afternoon transaction
                    "day": 15,   # Mid-month
                    "month": 11  # November
                }
                
                print(f"  {i}. Testing ₹{tx['amount']:,} at {tx['merchant']}")
                
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
                    
                    print(f"     ✅ Fraud Score: {fraud_score:.3f} | Risk: {risk_level} | Fraud: {is_fraud}")
                    
                    category_results.append({
                        "amount": tx["amount"],
                        "merchant": tx["merchant"],
                        "description": tx["description"],
                        "fraud_score": fraud_score,
                        "risk_level": risk_level,
                        "is_fraud": is_fraud
                    })
                else:
                    print(f"     ❌ HTTP Error: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"     ⏰ Request timeout for ₹{tx['amount']:,}")
            except Exception as e:
                print(f"     💥 Error: {str(e)}")
        
        # Calculate category statistics
        if category_results:
            avg_fraud_score = sum(r['fraud_score'] for r in category_results) / len(category_results)
            max_fraud_score = max(r['fraud_score'] for r in category_results)
            min_fraud_score = min(r['fraud_score'] for r in category_results)
            fraud_count = sum(1 for r in category_results if r['is_fraud'])
            
            print(f"\n📊 {category} SUMMARY:")
            print(f"    • Average Fraud Score: {avg_fraud_score:.3f}")
            print(f"    • Score Range: {min_fraud_score:.3f} - {max_fraud_score:.3f}")
            print(f"    • Flagged as Fraud: {fraud_count}/{len(category_results)}")
        
        all_results.append({
            "category": category,
            "results": category_results
        })
    
    # Overall analysis
    print("\n" + "=" * 50)
    print("🎯 OVERALL FRAUD DETECTION ANALYSIS")
    print("=" * 50)
    
    for category_data in all_results:
        category = category_data["category"]
        results = category_data["results"]
        
        if results:
            amounts = [r['amount'] for r in results]
            scores = [r['fraud_score'] for r in results]
            
            print(f"\n{category}:")
            print(f"  Amount Range: ₹{min(amounts):,} - ₹{max(amounts):,}")
            print(f"  Fraud Score Range: {min(scores):.3f} - {max(scores):.3f}")
            print(f"  Average Risk Score: {sum(scores)/len(scores):.3f}")
    
    # Banking decision simulation
    print(f"\n🏦 BANKING DECISION SIMULATION:")
    print("-" * 30)
    
    thresholds = {
        "Low Risk": 0.3,
        "Medium Risk": 0.5,
        "High Risk": 0.7
    }
    
    all_transactions = []
    for category_data in all_results:
        all_transactions.extend(category_data["results"])
    
    if all_transactions:
        for threshold_name, threshold_value in thresholds.items():
            flagged = [t for t in all_transactions if t['fraud_score'] >= threshold_value]
            print(f"  {threshold_name} Threshold ({threshold_value}): {len(flagged)} transactions flagged")
    
    print(f"\n✅ Testing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔍 Review the fraud scores across different amount ranges!")

if __name__ == "__main__":
    test_fraud_api()
