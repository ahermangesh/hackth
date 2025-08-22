#!/usr/bin/env python3
"""
UPI Fraud Detection Tool - Using existing API for real UPI transaction analysis
"""

import requests
import json
import sys
import argparse
from datetime import datetime
import time

class UPIFraudAnalyzer:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.check_server()
    
    def check_server(self):
        """Check if the fraud detection server is running"""
        try:
            response = requests.get(f"{self.api_url}/stats", timeout=5)
            if response.status_code == 200:
                print("✅ Fraud detection server is online!")
            else:
                print("⚠️ Server responded but may have issues")
        except:
            print("❌ Fraud detection server is not running!")
            print("Please start the server first: python backend/demo.py")
            sys.exit(1)
    
    def convert_upi_to_api_format(self, upi_transaction):
        """Convert UPI transaction format to API format"""
        try:
            # Extract timestamp features
            if 'timestamp' in upi_transaction:
                timestamp = datetime.strptime(upi_transaction['timestamp'], '%Y-%m-%d %H:%M:%S')
                hour = timestamp.hour
                day = timestamp.day
                month = timestamp.month
            else:
                now = datetime.now()
                hour = now.hour
                day = now.day
                month = now.month
            
            # Convert to API format (simple mapping)
            api_transaction = {
                "amount": float(upi_transaction.get('amount', 0)),
                "merchant": upi_transaction.get('merchant', 'Unknown'),
                "hour": hour,
                "day": day,
                "month": month
            }
            
            return api_transaction
            
        except Exception as e:
            print(f"❌ Error converting transaction: {str(e)}")
            return None
    
    def analyze_transaction(self, upi_transaction):
        """Analyze a single UPI transaction"""
        try:
            # Convert to API format
            api_transaction = self.convert_upi_to_api_format(upi_transaction)
            if not api_transaction:
                return None
            
            # Make API call
            response = requests.post(
                f"{self.api_url}/api/predict",
                json=api_transaction,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Enhance result with UPI transaction details
                enhanced_result = {
                    'transaction_id': upi_transaction.get('transaction_id', 'N/A'),
                    'original_amount': upi_transaction.get('amount', 0),
                    'transaction_type': upi_transaction.get('transaction_type', 'Unknown'),
                    'merchant': upi_transaction.get('merchant', 'Unknown'),
                    'sender_bank': upi_transaction.get('sender_bank', 'Unknown'),
                    'receiver_bank': upi_transaction.get('receiver_bank', 'Unknown'),
                    'device_type': upi_transaction.get('device_type', 'Unknown'),
                    'transaction_status': upi_transaction.get('transaction_status', 'Unknown'),
                    'fraud_score': result.get('fraud_score', 0),
                    'is_fraud': result.get('is_fraud', False),
                    'risk_level': result.get('risk_level', 'UNKNOWN'),
                    'api_response': result
                }
                
                return enhanced_result
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error analyzing transaction: {str(e)}")
            return None
    
    def analyze_batch(self, transactions):
        """Analyze a batch of UPI transactions"""
        results = []
        fraud_count = 0
        total_amount = 0
        failed_count = 0
        
        print(f"\n🔍 ANALYZING {len(transactions)} UPI TRANSACTIONS")
        print("=" * 70)
        
        for i, transaction in enumerate(transactions, 1):
            print(f"Processing transaction {i}/{len(transactions)}...", end=" ")
            
            result = self.analyze_transaction(transaction)
            if result:
                results.append(result)
                total_amount += result['original_amount']
                if result['is_fraud']:
                    fraud_count += 1
                
                # Print result
                fraud_indicator = "🚨 FRAUD" if result['is_fraud'] else "✅ SAFE"
                print(f"{fraud_indicator}")
                
                print(f"    ID: {result['transaction_id']}")
                print(f"    Amount: ₹{result['original_amount']:,}")
                print(f"    Type: {result['transaction_type']} | Status: {result['transaction_status']}")
                print(f"    Banks: {result['sender_bank']} → {result['receiver_bank']}")
                print(f"    Device: {result['device_type']} | Merchant: {result['merchant']}")
                print(f"    Fraud Score: {result['fraud_score']:.4f} | Risk: {result['risk_level']}")
                
                # Banking decision
                if result['fraud_score'] >= 0.7:
                    decision = "🛑 BLOCK TRANSACTION"
                elif result['fraud_score'] >= 0.5:
                    decision = "⚠️ REQUIRE VERIFICATION"
                elif result['fraud_score'] >= 0.3:
                    decision = "👀 MONITOR CLOSELY"
                else:
                    decision = "✅ APPROVE"
                print(f"    Banking Decision: {decision}")
                print()
            else:
                failed_count += 1
                print("❌ FAILED")
            
            # Rate limiting to avoid overwhelming the server
            if i < len(transactions):
                time.sleep(0.5)
        
        # Summary
        self.print_summary(results, fraud_count, total_amount, failed_count)
        return results
    
    def print_summary(self, results, fraud_count, total_amount, failed_count):
        """Print analysis summary"""
        print("=" * 70)
        print("📊 UPI FRAUD ANALYSIS SUMMARY")
        print("=" * 70)
        
        total_processed = len(results)
        
        print(f"✅ Successfully Processed: {total_processed}")
        print(f"❌ Failed to Process: {failed_count}")
        print(f"🚨 Flagged as Fraud: {fraud_count}")
        
        if total_processed > 0:
            fraud_rate = (fraud_count / total_processed) * 100
            print(f"📈 Fraud Rate: {fraud_rate:.1f}%")
            print(f"💰 Total Transaction Value: ₹{total_amount:,}")
            
            if fraud_count > 0:
                fraud_amount = sum(r['original_amount'] for r in results if r['is_fraud'])
                print(f"⚠️ Fraudulent Transaction Value: ₹{fraud_amount:,}")
                print(f"💸 Amount at Risk: {(fraud_amount/total_amount*100):.1f}%")
            
            # Risk distribution
            risk_counts = {}
            for result in results:
                risk_level = result['risk_level']
                risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
            
            print(f"\n📊 RISK LEVEL DISTRIBUTION:")
            for risk, count in sorted(risk_counts.items()):
                percentage = (count / total_processed) * 100
                print(f"  {risk}: {count} transactions ({percentage:.1f}%)")
            
            # Transaction type analysis
            type_counts = {}
            for result in results:
                tx_type = result['transaction_type']
                type_counts[tx_type] = type_counts.get(tx_type, 0) + 1
            
            print(f"\n💳 TRANSACTION TYPE BREAKDOWN:")
            for tx_type, count in sorted(type_counts.items()):
                percentage = (count / total_processed) * 100
                print(f"  {tx_type}: {count} transactions ({percentage:.1f}%)")
            
            # Device analysis
            device_counts = {}
            for result in results:
                device = result['device_type']
                device_counts[device] = device_counts.get(device, 0) + 1
            
            print(f"\n📱 DEVICE TYPE ANALYSIS:")
            for device, count in sorted(device_counts.items()):
                percentage = (count / total_processed) * 100
                print(f"  {device}: {count} transactions ({percentage:.1f}%)")

def interactive_mode(analyzer):
    """Interactive mode for single transaction testing"""
    print("\n🎯 INTERACTIVE UPI FRAUD DETECTION")
    print("Enter UPI transaction details:")
    print("-" * 50)
    
    while True:
        try:
            transaction = {}
            
            print("\nEnter transaction details (press Enter for defaults):")
            transaction['transaction_id'] = input("Transaction ID [TXN001]: ") or "TXN001"
            transaction['amount'] = float(input("Amount (₹) [1000]: ") or "1000")
            transaction['transaction_type'] = input("Type [P2M/Bill Payment/P2P] [P2M]: ") or "P2M"
            transaction['merchant'] = input("Merchant [Other/Grocery/Shopping] [Other]: ") or "Other"
            transaction['transaction_status'] = input("Status [SUCCESS/FAILED] [SUCCESS]: ") or "SUCCESS"
            transaction['sender_bank'] = input("Sender Bank [SBI]: ") or "SBI"
            transaction['receiver_bank'] = input("Receiver Bank [ICICI]: ") or "ICICI"
            transaction['device_type'] = input("Device [Android/iOS/Web] [Android]: ") or "Android"
            transaction['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            print("\n🔍 ANALYZING UPI TRANSACTION...")
            result = analyzer.analyze_transaction(transaction)
            
            if result:
                print("\n" + "="*50)
                print("🎯 FRAUD DETECTION RESULT")
                print("="*50)
                print(f"Transaction ID: {result['transaction_id']}")
                print(f"Amount: ₹{result['original_amount']:,}")
                print(f"Type: {result['transaction_type']}")
                print(f"Banks: {result['sender_bank']} → {result['receiver_bank']}")
                print(f"Device: {result['device_type']}")
                print(f"Fraud Score: {result['fraud_score']:.4f}")
                print(f"Risk Level: {result['risk_level']}")
                print(f"Decision: {'🚨 POTENTIAL FRAUD' if result['is_fraud'] else '✅ LEGITIMATE'}")
                
                # Banking recommendation
                if result['fraud_score'] >= 0.7:
                    print("🏦 Banking Action: 🛑 BLOCK TRANSACTION")
                elif result['fraud_score'] >= 0.5:
                    print("🏦 Banking Action: ⚠️ REQUIRE ADDITIONAL VERIFICATION")
                elif result['fraud_score'] >= 0.3:
                    print("🏦 Banking Action: 👀 MONITOR CLOSELY")
                else:
                    print("🏦 Banking Action: ✅ APPROVE")
            
            # Continue?
            continue_test = input("\nAnalyze another transaction? (y/N): ").lower()
            if continue_test != 'y':
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='UPI Fraud Detection Tool')
    parser.add_argument('--data', type=str, help='JSON file or JSON string with UPI transaction data')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('--server', type=str, default='http://localhost:8000', help='Fraud detection server URL')
    
    args = parser.parse_args()
    
    print("🚀 UPI FRAUD DETECTION ANALYZER")
    print("Using AI-powered fraud detection API")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = UPIFraudAnalyzer(args.server)
    
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
            
            analyzer.analyze_batch(transactions)
            
        except Exception as e:
            print(f"❌ Error processing data: {str(e)}")
            
    elif args.interactive:
        # Interactive mode
        interactive_mode(analyzer)
        
    else:
        print("Please specify --data or --interactive mode")
        print("\nExamples:")
        print("  python upi_fraud_analyzer.py --interactive")
        print("  python upi_fraud_analyzer.py --data test_transactions.json")
        print("  python upi_fraud_analyzer.py --data 'your_json_data'")

if __name__ == "__main__":
    main()
