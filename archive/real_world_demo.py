#!/usr/bin/env python3
"""
Real-World UPI Transaction Demo
Shows how the fraud detection system works with actual transaction scenarios
"""

import requests
import json
import time
import random

def demo_real_world_transactions():
    """Demo real-world transaction scenarios"""
    print("🏦 REAL-WORLD UPI FRAUD DETECTION DEMO")
    print("=" * 50)
    
    api_url = "http://localhost:8000/api/predict"
    
    # Real-world transaction scenarios
    scenarios = [
        {
            "name": "☕ Morning Coffee Purchase",
            "amount": 120,
            "merchant": "Starbucks",
            "context": "Normal daily expense, low risk",
            "expected": "LEGITIMATE"
        },
        {
            "name": "🛒 Grocery Shopping",
            "amount": 2500,
            "merchant": "BigBasket",
            "context": "Weekly grocery shopping",
            "expected": "LEGITIMATE"
        },
        {
            "name": "🏥 Medical Emergency",
            "amount": 25000,
            "merchant": "Apollo Hospital",
            "context": "High amount but legitimate medical expense",
            "expected": "LEGITIMATE (but flagged for review)"
        },
        {
            "name": "💰 Suspicious Large Transfer",
            "amount": 99999,
            "merchant": "Unknown Merchant XYZ",
            "context": "Very high amount to unknown merchant",
            "expected": "SUSPICIOUS"
        },
        {
            "name": "🎮 Gaming Purchase",
            "amount": 1500,
            "merchant": "Steam",
            "context": "Digital game purchase",
            "expected": "LEGITIMATE"
        },
        {
            "name": "🚗 Fuel Payment",
            "amount": 3000,
            "merchant": "Indian Oil",
            "context": "Fuel payment at petrol pump",
            "expected": "LEGITIMATE"
        },
        {
            "name": "📱 Mobile Recharge",
            "amount": 599,
            "merchant": "Airtel",
            "context": "Monthly mobile recharge",
            "expected": "LEGITIMATE"
        },
        {
            "name": "🔴 Micro Fraud Attempt",
            "amount": 1,
            "merchant": "Test Fraud",
            "context": "Micro transaction to test card validity",
            "expected": "POTENTIALLY SUSPICIOUS"
        }
    ]
    
    print(f"🧪 Testing {len(scenarios)} real-world scenarios...\n")
    
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"📋 Scenario {i}: {scenario['name']}")
        print(f"   💵 Amount: ₹{scenario['amount']}")
        print(f"   🏪 Merchant: {scenario['merchant']}")
        print(f"   📝 Context: {scenario['context']}")
        print(f"   🎯 Expected: {scenario['expected']}")
        
        try:
            # Make API call
            response = requests.post(
                api_url,
                json={
                    "amount": scenario["amount"],
                    "merchant": scenario["merchant"],
                    "transaction_type": "UPI"
                },
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                fraud_score = result.get('fraud_score', 0)
                risk_level = result.get('risk_level', 'UNKNOWN')
                is_fraud = result.get('is_fraud', False)
                
                # Determine status
                if is_fraud:
                    status = "🚨 FLAGGED AS SUSPICIOUS"
                    color = "🔴"
                elif fraud_score > 0.5:
                    status = "⚠️ REQUIRES REVIEW"
                    color = "🟡"
                else:
                    status = "✅ APPROVED"
                    color = "🟢"
                
                print(f"   {color} Result: {status}")
                print(f"   📊 Fraud Score: {fraud_score:.1%}")
                print(f"   📈 Risk Level: {risk_level}")
                
                # Bank decision logic
                if fraud_score > 0.7:
                    decision = "TRANSACTION BLOCKED - HIGH RISK"
                elif fraud_score > 0.3:
                    decision = "ADDITIONAL VERIFICATION REQUIRED"
                else:
                    decision = "TRANSACTION APPROVED"
                
                print(f"   🏦 Bank Decision: {decision}")
                
                results.append({
                    "scenario": scenario["name"],
                    "amount": scenario["amount"],
                    "fraud_score": fraud_score,
                    "risk_level": risk_level,
                    "decision": decision
                })
                
            else:
                print(f"   ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("-" * 50)
        time.sleep(0.5)  # Small delay for readability
    
    # Summary
    print(f"\n📊 FRAUD DETECTION SUMMARY")
    print("=" * 50)
    
    approved = sum(1 for r in results if "APPROVED" in r["decision"])
    blocked = sum(1 for r in results if "BLOCKED" in r["decision"])
    review = sum(1 for r in results if "VERIFICATION" in r["decision"])
    
    print(f"✅ Approved Transactions: {approved}")
    print(f"⚠️ Require Review: {review}")
    print(f"🚨 Blocked Transactions: {blocked}")
    print(f"📈 Total Processed: {len(results)}")
    
    # High-risk transactions
    high_risk = [r for r in results if r["fraud_score"] > 0.3]
    if high_risk:
        print(f"\n🔍 HIGH-RISK TRANSACTIONS DETECTED:")
        for transaction in high_risk:
            print(f"   • {transaction['scenario']}: ₹{transaction['amount']} ({transaction['fraud_score']:.1%} risk)")

def demo_bulk_processing():
    """Demo bulk transaction processing like banks would use"""
    print(f"\n\n🏦 BULK TRANSACTION PROCESSING DEMO")
    print("=" * 50)
    print("📋 Simulating bank's end-of-day fraud check...")
    
    # Sample batch of transactions
    batch_transactions = [
        {"amount": 500, "merchant": "Amazon", "user_id": "USER001"},
        {"amount": 75000, "merchant": "Car Dealer", "user_id": "USER002"},
        {"amount": 25, "merchant": "Tea Stall", "user_id": "USER003"},
        {"amount": 150000, "merchant": "Property Deal", "user_id": "USER004"},
        {"amount": 800, "merchant": "Restaurant", "user_id": "USER005"},
        {"amount": 99999, "merchant": "Unknown", "user_id": "USER006"},
        {"amount": 2000, "merchant": "Medical Store", "user_id": "USER007"},
        {"amount": 300, "merchant": "Book Store", "user_id": "USER008"},
    ]
    
    print(f"📊 Processing batch of {len(batch_transactions)} transactions...")
    
    api_url = "http://localhost:8000/api/predict"
    flagged_transactions = []
    
    for i, transaction in enumerate(batch_transactions, 1):
        try:
            response = requests.post(
                api_url,
                json=transaction,
                headers={"Content-Type": "application/json"},
                timeout=3
            )
            
            if response.status_code == 200:
                result = response.json()
                fraud_score = result.get('fraud_score', 0)
                
                # Flag high-risk transactions
                if fraud_score > 0.2:  # Lower threshold for bulk processing
                    flagged_transactions.append({
                        **transaction,
                        "fraud_score": fraud_score,
                        "risk_level": result.get('risk_level', 'UNKNOWN')
                    })
                    
                print(f"   ✓ Processed transaction {i}/{len(batch_transactions)}")
            
        except Exception as e:
            print(f"   ❌ Failed to process transaction {i}: {e}")
    
    # Report flagged transactions
    print(f"\n🚨 FLAGGED TRANSACTIONS REPORT:")
    print("=" * 50)
    
    if flagged_transactions:
        print(f"⚠️ {len(flagged_transactions)} transactions require review:")
        for transaction in flagged_transactions:
            print(f"   • User: {transaction['user_id']}")
            print(f"     Amount: ₹{transaction['amount']}")
            print(f"     Merchant: {transaction['merchant']}")
            print(f"     Risk Score: {transaction['fraud_score']:.1%}")
            print(f"     Action: {'IMMEDIATE REVIEW' if transaction['fraud_score'] > 0.5 else 'MONITOR'}")
            print()
    else:
        print("✅ No suspicious transactions detected in this batch.")

if __name__ == "__main__":
    print("🚀 FRAUD DETECTION SYSTEM - REAL-WORLD DEMO")
    print("🇮🇳 Indian UPI Transaction Patterns")
    print("🏦 Banking Industry Use Cases")
    print("=" * 60)
    
    # Check if API is available
    try:
        response = requests.get("http://localhost:8000/", timeout=3)
        if response.status_code == 200:
            print("✅ Backend API is running\n")
            
            # Run demos
            demo_real_world_transactions()
            demo_bulk_processing()
            
            print(f"\n🎉 DEMO COMPLETED!")
            print(f"💡 The system successfully analyzed real-world transaction patterns")
            print(f"🏦 Banks can integrate this API for live fraud detection")
            print(f"🌐 Dashboard available at: http://localhost:3002")
            
        else:
            print("❌ Backend API not responding properly")
            
    except Exception as e:
        print(f"❌ Cannot connect to backend API: {e}")
        print("💡 Make sure the backend server is running on port 8000")
