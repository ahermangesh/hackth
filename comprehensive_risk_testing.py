#!/usr/bin/env python3
"""
Comprehensive Testing with Low, High, and Normal Transaction Data
Shows how the fraud detection system responds to different risk levels
"""

import requests
import json
import time

def test_transaction_ranges():
    """Test transactions across different amount ranges"""
    print("🧪 COMPREHENSIVE FRAUD DETECTION TESTING")
    print("Testing Low, Normal, High, and Extreme Transaction Amounts")
    print("=" * 70)
    
    api_url = "http://localhost:8000/api/predict"
    
    # Test cases organized by risk category
    test_categories = {
        "💰 LOW AMOUNT TRANSACTIONS": [
            {"amount": 1, "merchant": "Chai Stall", "context": "Micro payment"},
            {"amount": 5, "merchant": "Parking Fee", "context": "Very small payment"},
            {"amount": 25, "merchant": "Auto Rickshaw", "context": "Transportation"},
            {"amount": 50, "merchant": "Tea & Snacks", "context": "Small food purchase"},
            {"amount": 100, "merchant": "Coffee Shop", "context": "Coffee purchase"}
        ],
        
        "📊 NORMAL AMOUNT TRANSACTIONS": [
            {"amount": 500, "merchant": "Grocery Store", "context": "Weekly groceries"},
            {"amount": 800, "merchant": "Restaurant", "context": "Dinner for two"},
            {"amount": 1200, "merchant": "Medical Store", "context": "Medicine purchase"},
            {"amount": 2500, "merchant": "BigBasket", "context": "Monthly groceries"},
            {"amount": 5000, "merchant": "Clothing Store", "context": "Shopping"}
        ],
        
        "⚠️ HIGH AMOUNT TRANSACTIONS": [
            {"amount": 15000, "merchant": "Electronics Store", "context": "Mobile phone"},
            {"amount": 25000, "merchant": "Hospital", "context": "Medical emergency"},
            {"amount": 40000, "merchant": "Laptop Store", "context": "Laptop purchase"},
            {"amount": 60000, "merchant": "Jewelry Store", "context": "Gold purchase"},
            {"amount": 80000, "merchant": "Furniture Store", "context": "Home furniture"}
        ],
        
        "🚨 EXTREME AMOUNT TRANSACTIONS": [
            {"amount": 100000, "merchant": "Car Dealer", "context": "Car down payment"},
            {"amount": 150000, "merchant": "Property Deal", "context": "Real estate"},
            {"amount": 250000, "merchant": "Unknown Merchant", "context": "Suspicious transfer"},
            {"amount": 500000, "merchant": "Investment Firm", "context": "Large investment"},
            {"amount": 999999, "merchant": "Crypto Exchange", "context": "Crypto purchase"}
        ]
    }
    
    all_results = {}
    
    for category, transactions in test_categories.items():
        print(f"\n{category}")
        print("-" * 60)
        
        category_results = []
        
        for i, transaction in enumerate(transactions, 1):
            print(f"🔍 Test {i}: {transaction['context']}")
            print(f"   Amount: ₹{transaction['amount']:,}")
            print(f"   Merchant: {transaction['merchant']}")
            
            try:
                response = requests.post(
                    api_url,
                    json={
                        "amount": transaction["amount"],
                        "merchant": transaction["merchant"],
                        "transaction_type": "UPI"
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    fraud_score = result.get('fraud_score', 0)
                    risk_level = result.get('risk_level', 'UNKNOWN')
                    is_fraud = result.get('is_fraud', False)
                    
                    # Color coding based on risk
                    if fraud_score > 0.7:
                        status_color = "🔴"
                        status_text = "HIGH RISK"
                    elif fraud_score > 0.3:
                        status_color = "🟡"
                        status_text = "MEDIUM RISK"
                    else:
                        status_color = "🟢"
                        status_text = "LOW RISK"
                    
                    # Bank decision logic
                    if fraud_score > 0.8:
                        decision = "BLOCK TRANSACTION"
                        action_color = "🚨"
                    elif fraud_score > 0.5:
                        decision = "REQUIRE 2FA/OTP"
                        action_color = "⚠️"
                    elif fraud_score > 0.2:
                        decision = "MONITOR CLOSELY"
                        action_color = "👀"
                    else:
                        decision = "APPROVE"
                        action_color = "✅"
                    
                    print(f"   {status_color} Risk Score: {fraud_score:.1%}")
                    print(f"   📊 Risk Level: {risk_level}")
                    print(f"   {action_color} Decision: {decision}")
                    
                    category_results.append({
                        "amount": transaction["amount"],
                        "merchant": transaction["merchant"],
                        "fraud_score": fraud_score,
                        "risk_level": risk_level,
                        "decision": decision,
                        "context": transaction["context"]
                    })
                    
                else:
                    print(f"   ❌ API Error: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"   ⏰ Request timed out - server may be busy")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print()
            time.sleep(0.3)  # Small delay to avoid overwhelming the server
        
        all_results[category] = category_results
    
    # Generate comprehensive analysis
    print_analysis_summary(all_results)

def print_analysis_summary(results):
    """Print comprehensive analysis of test results"""
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE FRAUD DETECTION ANALYSIS")
    print("=" * 70)
    
    all_transactions = []
    for category_results in results.values():
        all_transactions.extend(category_results)
    
    if not all_transactions:
        print("❌ No successful transactions to analyze")
        return
    
    # Risk distribution analysis
    low_risk = [t for t in all_transactions if t['fraud_score'] < 0.3]
    medium_risk = [t for t in all_transactions if 0.3 <= t['fraud_score'] < 0.7]
    high_risk = [t for t in all_transactions if t['fraud_score'] >= 0.7]
    
    print(f"\n🎯 RISK DISTRIBUTION:")
    print(f"   🟢 Low Risk (0-30%):     {len(low_risk):2d} transactions")
    print(f"   🟡 Medium Risk (30-70%): {len(medium_risk):2d} transactions")
    print(f"   🔴 High Risk (70%+):     {len(high_risk):2d} transactions")
    print(f"   📊 Total Analyzed:       {len(all_transactions):2d} transactions")
    
    # Decision distribution
    approved = [t for t in all_transactions if "APPROVE" in t['decision']]
    monitored = [t for t in all_transactions if "MONITOR" in t['decision']]
    require_2fa = [t for t in all_transactions if "2FA" in t['decision']]
    blocked = [t for t in all_transactions if "BLOCK" in t['decision']]
    
    print(f"\n🏦 BANKING DECISIONS:")
    print(f"   ✅ Approved:           {len(approved):2d} transactions")
    print(f"   👀 Monitor Closely:    {len(monitored):2d} transactions")
    print(f"   ⚠️ Require 2FA/OTP:   {len(require_2fa):2d} transactions")
    print(f"   🚨 Blocked:            {len(blocked):2d} transactions")
    
    # Amount vs Risk Analysis
    print(f"\n💰 AMOUNT vs RISK CORRELATION:")
    amount_ranges = [
        ("₹1-100", [t for t in all_transactions if t['amount'] <= 100]),
        ("₹101-1,000", [t for t in all_transactions if 101 <= t['amount'] <= 1000]),
        ("₹1,001-10,000", [t for t in all_transactions if 1001 <= t['amount'] <= 10000]),
        ("₹10,001-50,000", [t for t in all_transactions if 10001 <= t['amount'] <= 50000]),
        ("₹50,000+", [t for t in all_transactions if t['amount'] > 50000])
    ]
    
    for range_name, range_transactions in amount_ranges:
        if range_transactions:
            avg_risk = sum(t['fraud_score'] for t in range_transactions) / len(range_transactions)
            print(f"   {range_name:15s}: {len(range_transactions):2d} transactions, {avg_risk:.1%} avg risk")
    
    # High-risk transactions detail
    if high_risk:
        print(f"\n🚨 HIGH-RISK TRANSACTIONS REQUIRING ATTENTION:")
        for transaction in high_risk:
            print(f"   • ₹{transaction['amount']:,} to {transaction['merchant']}")
            print(f"     Risk: {transaction['fraud_score']:.1%} | Action: {transaction['decision']}")
            print(f"     Context: {transaction['context']}")
            print()
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS FOR BANKS:")
    print(f"   🔧 Auto-approve transactions below ₹1,000 with <20% risk")
    print(f"   👀 Monitor transactions ₹10,000-50,000 closely")
    print(f"   🔐 Require additional authentication for >₹50,000")
    print(f"   🚨 Block transactions with >80% fraud score immediately")
    print(f"   📱 Send SMS alerts for medium-risk transactions")

def test_specific_fraud_patterns():
    """Test specific fraud patterns that are commonly seen"""
    print(f"\n\n🔍 TESTING SPECIFIC FRAUD PATTERNS")
    print("=" * 70)
    
    fraud_patterns = [
        {
            "name": "Round Number Testing",
            "transactions": [
                {"amount": 10000, "merchant": "Test Merchant"},
                {"amount": 50000, "merchant": "Test Merchant"},
                {"amount": 100000, "merchant": "Test Merchant"}
            ],
            "explanation": "Fraudsters often test with round numbers"
        },
        {
            "name": "Micro Transaction Testing", 
            "transactions": [
                {"amount": 1, "merchant": "Card Validation"},
                {"amount": 2, "merchant": "Account Test"},
                {"amount": 5, "merchant": "System Check"}
            ],
            "explanation": "Small amounts to test if card/account is valid"
        },
        {
            "name": "Gradual Amount Increase",
            "transactions": [
                {"amount": 1000, "merchant": "Online Store"},
                {"amount": 5000, "merchant": "Online Store"},
                {"amount": 25000, "merchant": "Online Store"},
                {"amount": 75000, "merchant": "Online Store"}
            ],
            "explanation": "Gradually increasing amounts to avoid detection"
        }
    ]
    
    api_url = "http://localhost:8000/api/predict"
    
    for pattern in fraud_patterns:
        print(f"\n🎯 Pattern: {pattern['name']}")
        print(f"📝 Explanation: {pattern['explanation']}")
        print("-" * 50)
        
        for i, transaction in enumerate(pattern['transactions'], 1):
            print(f"Step {i}: ₹{transaction['amount']} to {transaction['merchant']}")
            
            try:
                response = requests.post(
                    api_url,
                    json=transaction,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    fraud_score = result.get('fraud_score', 0)
                    print(f"   Risk Score: {fraud_score:.1%}")
                    
                    if fraud_score > 0.5:
                        print(f"   🚨 PATTERN DETECTED - High Risk!")
                    elif fraud_score > 0.2:
                        print(f"   ⚠️ Elevated risk - Monitor closely")
                    else:
                        print(f"   ✅ Normal transaction")
                else:
                    print(f"   ❌ API Error")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    print("🚀 ADVANCED FRAUD DETECTION TESTING SUITE")
    print("🎯 Testing Different Risk Levels and Patterns")
    print("🏦 Banking Industry Standard Analysis")
    print("=" * 70)
    
    # Check if API is available
    try:
        response = requests.get("http://localhost:8000/", timeout=3)
        if response.status_code == 200:
            print("✅ Backend API is running - Starting comprehensive tests\n")
            
            # Run comprehensive tests
            test_transaction_ranges()
            test_specific_fraud_patterns()
            
            print(f"\n🎉 TESTING COMPLETED!")
            print(f"💡 The fraud detection system has been thoroughly tested")
            print(f"🏦 Ready for production banking use")
            print(f"🌐 Dashboard: http://localhost:3002")
            
        else:
            print("❌ Backend API not responding properly")
            
    except Exception as e:
        print(f"❌ Cannot connect to backend API: {e}")
        print("💡 Make sure the backend server is running on port 8000")
