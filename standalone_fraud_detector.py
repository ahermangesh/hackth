#!/usr/bin/env python3
"""
Standalone UPI Fraud Detection - Rule-based analysis for UPI transactions
Works without needing a running server
"""

import json
import sys
import argparse
from datetime import datetime
import math

class StandaloneUPIFraudDetector:
    def __init__(self):
        """Initialize the rule-based fraud detector"""
        self.fraud_rules = {
            'high_amount_threshold': 50000,  # ₹50,000+
            'very_high_amount_threshold': 200000,  # ₹2,00,000+
            'night_hours': [22, 23, 0, 1, 2, 3, 4, 5],  # 10 PM to 5 AM
            'failed_transaction_risk': 0.3,  # Additional risk for failed transactions
            'cross_state_risk': 0.1,  # Additional risk for cross-state transactions
            'weekend_risk': 0.05,  # Additional risk for weekend transactions
        }
        
        # Risk patterns for different transaction types
        self.transaction_risk = {
            'P2M': 0.1,  # Person to Merchant - generally safe
            'Bill Payment': 0.05,  # Very safe
            'P2P': 0.15,  # Person to Person - slightly riskier
            'Money Transfer': 0.2,  # Higher risk
            'Recharge': 0.02,  # Very safe
        }
        
        # Risk patterns for merchants
        self.merchant_risk = {
            'Grocery': 0.02,
            'Shopping': 0.05,
            'Food': 0.03,
            'Transport': 0.04,
            'Other': 0.1,  # Unknown merchants are riskier
            'Entertainment': 0.06,
            'Healthcare': 0.03,
            'Education': 0.02,
        }
        
        # Device risk patterns
        self.device_risk = {
            'Android': 0.05,
            'iOS': 0.03,
            'Web': 0.08,  # Web transactions slightly riskier
        }
        
        # Bank risk patterns (simplified)
        self.bank_risk = {
            'SBI': 0.02,
            'ICICI': 0.03,
            'HDFC': 0.03,
            'Axis': 0.04,
            'PNB': 0.03,
            'Kotak': 0.04,
            'IndusInd': 0.05,
            'BOI': 0.04,
            'Canara': 0.04,
            'Union': 0.05,
        }
    
    def calculate_amount_risk(self, amount):
        """Calculate risk based on transaction amount"""
        if amount >= self.fraud_rules['very_high_amount_threshold']:
            return 0.6  # Very high amount
        elif amount >= self.fraud_rules['high_amount_threshold']:
            return 0.3  # High amount
        elif amount >= 20000:
            return 0.15  # Medium-high amount
        elif amount >= 10000:
            return 0.1  # Medium amount
        elif amount >= 5000:
            return 0.05  # Slightly elevated
        else:
            return 0.0  # Normal amounts
    
    def calculate_time_risk(self, timestamp_str):
        """Calculate risk based on transaction time"""
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            hour = timestamp.hour
            weekday = timestamp.weekday()  # 0 = Monday, 6 = Sunday
            
            risk = 0.0
            
            # Night time risk
            if hour in self.fraud_rules['night_hours']:
                risk += 0.2
            
            # Very late night (1-4 AM) extra risk
            if hour in [1, 2, 3, 4]:
                risk += 0.1
            
            # Weekend risk
            if weekday >= 5:  # Saturday = 5, Sunday = 6
                risk += self.fraud_rules['weekend_risk']
            
            return min(risk, 0.4)  # Cap at 0.4
            
        except:
            return 0.0
    
    def calculate_geographic_risk(self, sender_state, receiver_state):
        """Calculate risk based on geographic factors"""
        if sender_state == receiver_state:
            return 0.0  # Same state, lower risk
        else:
            return self.fraud_rules['cross_state_risk']  # Cross-state transaction
    
    def analyze_transaction(self, transaction):
        """Analyze a single transaction for fraud risk"""
        try:
            # Base risk score
            fraud_score = 0.0
            
            # Amount-based risk
            amount = float(transaction.get('amount', 0))
            amount_risk = self.calculate_amount_risk(amount)
            fraud_score += amount_risk
            
            # Time-based risk
            timestamp = transaction.get('timestamp', '')
            if timestamp:
                time_risk = self.calculate_time_risk(timestamp)
                fraud_score += time_risk
            
            # Transaction type risk
            tx_type = transaction.get('transaction_type', 'Other')
            type_risk = self.transaction_risk.get(tx_type, 0.1)
            fraud_score += type_risk
            
            # Merchant risk
            merchant = transaction.get('merchant', 'Other')
            merchant_risk = self.merchant_risk.get(merchant, 0.1)
            fraud_score += merchant_risk
            
            # Device risk
            device = transaction.get('device_type', 'Android')
            device_risk = self.device_risk.get(device, 0.05)
            fraud_score += device_risk
            
            # Geographic risk
            sender_state = transaction.get('sender_state', '')
            receiver_state = transaction.get('receiver_state', '')
            geo_risk = self.calculate_geographic_risk(sender_state, receiver_state)
            fraud_score += geo_risk
            
            # Transaction status risk
            if transaction.get('transaction_status') == 'FAILED':
                fraud_score += self.fraud_rules['failed_transaction_risk']
            
            # Bank risk (simplified - using sender bank)
            sender_bank = transaction.get('sender_bank', 'SBI')
            bank_risk = self.bank_risk.get(sender_bank, 0.05)
            fraud_score += bank_risk
            
            # Normalize score to 0-1 range
            fraud_score = min(fraud_score, 1.0)
            
            # Determine fraud flag and risk level
            is_fraud = fraud_score >= 0.5  # Threshold for fraud detection
            
            if fraud_score >= 0.8:
                risk_level = "VERY HIGH"
            elif fraud_score >= 0.6:
                risk_level = "HIGH"
            elif fraud_score >= 0.4:
                risk_level = "MEDIUM"
            elif fraud_score >= 0.2:
                risk_level = "LOW"
            else:
                risk_level = "VERY LOW"
            
            return {
                'transaction_id': transaction.get('transaction_id', 'N/A'),
                'amount': amount,
                'transaction_type': transaction.get('transaction_type', 'Unknown'),
                'merchant': transaction.get('merchant', 'Unknown'),
                'sender_bank': transaction.get('sender_bank', 'Unknown'),
                'receiver_bank': transaction.get('receiver_bank', 'Unknown'),
                'sender_state': transaction.get('sender_state', 'Unknown'),
                'receiver_state': transaction.get('receiver_state', 'Unknown'),
                'device_type': transaction.get('device_type', 'Unknown'),
                'transaction_status': transaction.get('transaction_status', 'Unknown'),
                'fraud_score': round(fraud_score, 4),
                'is_fraud': is_fraud,
                'risk_level': risk_level,
                'risk_factors': {
                    'amount_risk': round(amount_risk, 3),
                    'time_risk': round(self.calculate_time_risk(timestamp) if timestamp else 0, 3),
                    'type_risk': round(type_risk, 3),
                    'merchant_risk': round(merchant_risk, 3),
                    'geographic_risk': round(geo_risk, 3),
                    'device_risk': round(device_risk, 3),
                    'bank_risk': round(bank_risk, 3)
                }
            }
            
        except Exception as e:
            print(f"❌ Error analyzing transaction: {str(e)}")
            return None
    
    def analyze_batch(self, transactions):
        """Analyze a batch of transactions"""
        results = []
        fraud_count = 0
        total_amount = 0
        
        print(f"\n🔍 ANALYZING {len(transactions)} UPI TRANSACTIONS")
        print("Using Rule-Based Fraud Detection Engine")
        print("=" * 70)
        
        for i, transaction in enumerate(transactions, 1):
            result = self.analyze_transaction(transaction)
            if result:
                results.append(result)
                total_amount += result['amount']
                if result['is_fraud']:
                    fraud_count += 1
                
                # Print detailed result
                fraud_indicator = "🚨 FRAUD DETECTED" if result['is_fraud'] else "✅ LEGITIMATE"
                print(f"\n{i:2d}. Transaction Analysis: {result['transaction_id']}")
                print(f"    Amount: ₹{result['amount']:,}")
                print(f"    Type: {result['transaction_type']} | Status: {result['transaction_status']}")
                print(f"    Merchant: {result['merchant']} | Device: {result['device_type']}")
                print(f"    Banks: {result['sender_bank']} → {result['receiver_bank']}")
                print(f"    States: {result['sender_state']} → {result['receiver_state']}")
                print(f"    🎯 Fraud Score: {result['fraud_score']:.4f}")
                print(f"    📊 Risk Level: {result['risk_level']}")
                print(f"    🏛️  Decision: {fraud_indicator}")
                
                # Show risk factor breakdown
                print(f"    📋 Risk Breakdown:")
                factors = result['risk_factors']
                for factor, value in factors.items():
                    if value > 0:
                        print(f"        • {factor.replace('_', ' ').title()}: +{value}")
                
                # Banking decision
                score = result['fraud_score']
                if score >= 0.8:
                    decision = "🛑 BLOCK IMMEDIATELY"
                elif score >= 0.6:
                    decision = "⚠️ REQUIRE STRONG AUTHENTICATION"
                elif score >= 0.4:
                    decision = "👀 ENHANCED MONITORING"
                elif score >= 0.2:
                    decision = "📊 STANDARD MONITORING"
                else:
                    decision = "✅ APPROVE NORMALLY"
                print(f"    🏦 Banking Action: {decision}")
        
        # Print comprehensive summary
        self.print_summary(results, fraud_count, total_amount)
        return results
    
    def print_summary(self, results, fraud_count, total_amount):
        """Print comprehensive analysis summary"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE UPI FRAUD ANALYSIS REPORT")
        print("=" * 70)
        
        total_transactions = len(results)
        
        print(f"✅ Total Transactions Analyzed: {total_transactions}")
        print(f"🚨 Transactions Flagged as Fraud: {fraud_count}")
        
        if total_transactions > 0:
            fraud_rate = (fraud_count / total_transactions) * 100
            print(f"📈 Overall Fraud Rate: {fraud_rate:.1f}%")
            print(f"💰 Total Transaction Value: ₹{total_amount:,}")
            
            if fraud_count > 0:
                fraud_amount = sum(r['amount'] for r in results if r['is_fraud'])
                clean_amount = total_amount - fraud_amount
                print(f"⚠️ Potentially Fraudulent Value: ₹{fraud_amount:,}")
                print(f"✅ Clean Transaction Value: ₹{clean_amount:,}")
                print(f"💸 Percentage at Risk: {(fraud_amount/total_amount*100):.1f}%")
            
            # Risk level distribution
            risk_distribution = {}
            for result in results:
                risk_level = result['risk_level']
                risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
            
            print(f"\n📊 RISK LEVEL DISTRIBUTION:")
            risk_order = ['VERY LOW', 'LOW', 'MEDIUM', 'HIGH', 'VERY HIGH']
            for risk in risk_order:
                if risk in risk_distribution:
                    count = risk_distribution[risk]
                    percentage = (count / total_transactions) * 100
                    print(f"  {risk}: {count} transactions ({percentage:.1f}%)")
            
            # Transaction type analysis
            type_analysis = {}
            for result in results:
                tx_type = result['transaction_type']
                if tx_type not in type_analysis:
                    type_analysis[tx_type] = {'count': 0, 'fraud_count': 0, 'total_amount': 0}
                type_analysis[tx_type]['count'] += 1
                type_analysis[tx_type]['total_amount'] += result['amount']
                if result['is_fraud']:
                    type_analysis[tx_type]['fraud_count'] += 1
            
            print(f"\n💳 TRANSACTION TYPE ANALYSIS:")
            for tx_type, data in sorted(type_analysis.items()):
                fraud_rate_type = (data['fraud_count'] / data['count'] * 100) if data['count'] > 0 else 0
                print(f"  {tx_type}:")
                print(f"    • Count: {data['count']} transactions")
                print(f"    • Fraud Rate: {fraud_rate_type:.1f}%")
                print(f"    • Total Value: ₹{data['total_amount']:,}")
            
            # Banking recommendations
            print(f"\n🏦 BANKING RECOMMENDATIONS:")
            high_risk_count = sum(1 for r in results if r['fraud_score'] >= 0.6)
            medium_risk_count = sum(1 for r in results if 0.4 <= r['fraud_score'] < 0.6)
            
            if high_risk_count > 0:
                print(f"  🛑 IMMEDIATE ACTION: {high_risk_count} high-risk transactions need review")
            if medium_risk_count > 0:
                print(f"  ⚠️ ENHANCED MONITORING: {medium_risk_count} medium-risk transactions")
            
            clean_count = total_transactions - high_risk_count - medium_risk_count
            print(f"  ✅ NORMAL PROCESSING: {clean_count} low-risk transactions")

def interactive_mode(detector):
    """Interactive mode for single transaction testing"""
    print("\n🎯 INTERACTIVE UPI FRAUD DETECTION")
    print("Enter UPI transaction details for real-time analysis")
    print("-" * 60)
    
    while True:
        try:
            print("\n📝 Enter transaction details (press Enter for defaults):")
            
            transaction = {}
            transaction['transaction_id'] = input("Transaction ID [TXN001]: ") or "TXN001"
            transaction['amount'] = float(input("Amount (₹) [5000]: ") or "5000")
            transaction['transaction_type'] = input("Type [P2M/Bill Payment/P2P] [P2M]: ") or "P2M"
            transaction['merchant'] = input("Merchant [Other/Grocery/Shopping] [Other]: ") or "Other"
            transaction['transaction_status'] = input("Status [SUCCESS/FAILED] [SUCCESS]: ") or "SUCCESS"
            transaction['sender_bank'] = input("Sender Bank [SBI]: ") or "SBI"
            transaction['receiver_bank'] = input("Receiver Bank [ICICI]: ") or "ICICI"
            transaction['sender_state'] = input("Sender State [Maharashtra]: ") or "Maharashtra"
            transaction['receiver_state'] = input("Receiver State [Karnataka]: ") or "Karnataka"
            transaction['device_type'] = input("Device [Android/iOS/Web] [Android]: ") or "Android"
            transaction['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            print("\n🔍 ANALYZING TRANSACTION...")
            result = detector.analyze_transaction(transaction)
            
            if result:
                print("\n" + "="*60)
                print("🎯 FRAUD DETECTION ANALYSIS RESULT")
                print("="*60)
                print(f"Transaction ID: {result['transaction_id']}")
                print(f"Amount: ₹{result['amount']:,}")
                print(f"Type: {result['transaction_type']} | Status: {result['transaction_status']}")
                print(f"Banks: {result['sender_bank']} → {result['receiver_bank']}")
                print(f"States: {result['sender_state']} → {result['receiver_state']}")
                print(f"Device: {result['device_type']}")
                print(f"\n🎯 Fraud Score: {result['fraud_score']:.4f}")
                print(f"📊 Risk Level: {result['risk_level']}")
                print(f"🔍 Decision: {'🚨 POTENTIAL FRAUD' if result['is_fraud'] else '✅ LEGITIMATE TRANSACTION'}")
                
                # Show risk factors
                print(f"\n📋 Risk Factor Analysis:")
                factors = result['risk_factors']
                for factor, value in factors.items():
                    status = "⚠️" if value > 0.1 else "✅" if value > 0 else "➖"
                    print(f"  {status} {factor.replace('_', ' ').title()}: {value}")
                
                # Banking recommendation
                score = result['fraud_score']
                if score >= 0.8:
                    action = "🛑 BLOCK TRANSACTION IMMEDIATELY"
                    detail = "Extremely high fraud risk detected"
                elif score >= 0.6:
                    action = "⚠️ REQUIRE ADDITIONAL VERIFICATION"
                    detail = "High fraud risk - needs manual review"
                elif score >= 0.4:
                    action = "👀 APPLY ENHANCED MONITORING"
                    detail = "Medium risk - increased scrutiny recommended"
                elif score >= 0.2:
                    action = "📊 STANDARD PROCESSING WITH MONITORING"
                    detail = "Low risk - routine monitoring sufficient"
                else:
                    action = "✅ APPROVE WITH NORMAL PROCESSING"
                    detail = "Very low risk - standard approval"
                
                print(f"\n🏦 Banking Recommendation:")
                print(f"  Action: {action}")
                print(f"  Reason: {detail}")
            
            # Continue?
            print("\n" + "-"*60)
            continue_test = input("Analyze another transaction? (y/N): ").lower()
            if continue_test != 'y':
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 Thank you for using UPI Fraud Detection!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Standalone UPI Fraud Detection Tool')
    parser.add_argument('--data', type=str, help='JSON file or JSON string with UPI transaction data')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    args = parser.parse_args()
    
    print("🚀 STANDALONE UPI FRAUD DETECTION SYSTEM")
    print("🤖 Rule-Based AI Fraud Detection Engine")
    print("=" * 60)
    
    # Initialize detector
    detector = StandaloneUPIFraudDetector()
    
    if args.data:
        # Batch mode - analyze provided data
        try:
            # Try to parse as JSON string first
            if args.data.startswith('[') or args.data.startswith('{'):
                transactions = json.loads(args.data)
            else:
                # Try to read as file
                with open(args.data, 'r') as f:
                    transactions = json.load(f)
            
            if isinstance(transactions, dict):
                transactions = [transactions]
            
            detector.analyze_batch(transactions)
            
        except Exception as e:
            print(f"❌ Error processing data: {str(e)}")
            
    elif args.interactive:
        # Interactive mode
        interactive_mode(detector)
        
    else:
        print("Please specify --data or --interactive mode")
        print("\nExamples:")
        print("  python standalone_fraud_detector.py --interactive")
        print("  python standalone_fraud_detector.py --data test_transactions.json")
        print("  python standalone_fraud_detector.py --data 'your_json_data'")

if __name__ == "__main__":
    main()
