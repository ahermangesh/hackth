#!/usr/bin/env python3
"""
UPI Fraud Detection Tool - Interactive testing for real UPI transaction data
Supports both command line input and JSON data analysis
"""

import pickle
import pandas as pd
import numpy as np
import json
import sys
from datetime import datetime
import argparse
from pathlib import Path

class UPIFraudDetector:
    def __init__(self, model_path=None):
        """Initialize the UPI fraud detector"""
        if model_path is None:
            model_path = "data/models/fraud_model.pkl"
        
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.load_model()
        
        # Feature mappings for categorical variables
        self.transaction_type_map = {
            'P2M': 0, 'Bill Payment': 1, 'P2P': 2, 'Money Transfer': 3, 'Recharge': 4
        }
        
        self.merchant_map = {
            'Other': 0, 'Grocery': 1, 'Shopping': 2, 'Food': 3, 'Transport': 4, 
            'Entertainment': 5, 'Healthcare': 6, 'Education': 7
        }
        
        self.status_map = {
            'SUCCESS': 1, 'FAILED': 0, 'PENDING': 2
        }
        
        self.age_map = {
            '18-25': 0, '26-35': 1, '36-45': 2, '46-55': 3, '56+': 4
        }
        
        self.device_map = {
            'Android': 0, 'iOS': 1, 'Web': 2
        }
        
        self.network_map = {
            '4G': 0, '5G': 1, 'WiFi': 2, '3G': 3
        }
        
        self.bank_map = {
            'SBI': 0, 'ICICI': 1, 'HDFC': 2, 'Axis': 3, 'PNB': 4, 'Kotak': 5, 
            'IndusInd': 6, 'BOI': 7, 'Canara': 8, 'Union': 9
        }
        
        self.state_map = {
            'Maharashtra': 0, 'Karnataka': 1, 'Tamil Nadu': 2, 'Gujarat': 3,
            'Rajasthan': 4, 'Uttar Pradesh': 5, 'West Bengal': 6, 'Kerala': 7,
            'Andhra Pradesh': 8, 'Telangana': 9, 'Punjab': 10, 'Haryana': 11,
            'Odisha': 12, 'Jharkhand': 13, 'Assam': 14, 'Other': 15
        }
    
    def load_model(self):
        """Load the trained fraud detection model"""
        try:
            if Path(self.model_path).exists():
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    if isinstance(model_data, dict):
                        self.model = model_data['model']
                        self.scaler = model_data.get('scaler')
                    else:
                        self.model = model_data
                print("✅ Fraud detection model loaded successfully!")
            else:
                print(f"❌ Model file not found: {self.model_path}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error loading model: {str(e)}")
            sys.exit(1)
    
    def extract_features(self, transaction):
        """Extract features from a transaction for prediction"""
        try:
            # Parse timestamp if needed
            if isinstance(transaction.get('timestamp'), str):
                timestamp = datetime.strptime(transaction['timestamp'], '%Y-%m-%d %H:%M:%S')
            else:
                timestamp = datetime.now()
            
            # Extract time features
            hour = timestamp.hour
            day = timestamp.day
            month = timestamp.month
            
            # Map categorical features
            transaction_type = self.transaction_type_map.get(transaction.get('transaction_type', 'Other'), 0)
            merchant = self.merchant_map.get(transaction.get('merchant', 'Other'), 0)
            status = self.status_map.get(transaction.get('transaction_status', 'SUCCESS'), 1)
            sender_age = self.age_map.get(transaction.get('sender_age', '26-35'), 1)
            receiver_age = self.age_map.get(transaction.get('receiver_age', '26-35'), 1)
            device_type = self.device_map.get(transaction.get('device_type', 'Android'), 0)
            network_type = self.network_map.get(transaction.get('network_type', '4G'), 0)
            
            sender_bank = self.bank_map.get(transaction.get('sender_bank', 'SBI'), 0)
            receiver_bank = self.bank_map.get(transaction.get('receiver_bank', 'SBI'), 0)
            sender_state = self.state_map.get(transaction.get('sender_state', 'Other'), 15)
            receiver_state = self.state_map.get(transaction.get('receiver_state', 'Other'), 15)
            
            # Amount
            amount = float(transaction.get('amount', 0))
            
            # Create feature vector - adjust based on your model's expected features
            features = [
                amount,
                hour,
                day, 
                month,
                transaction_type,
                merchant,
                status,
                sender_age,
                receiver_age,
                sender_bank,
                receiver_bank,
                sender_state,
                receiver_state,
                device_type,
                network_type
            ]
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            print(f"❌ Error extracting features: {str(e)}")
            return None
    
    def predict_fraud(self, transaction):
        """Predict if a transaction is fraudulent"""
        try:
            features = self.extract_features(transaction)
            if features is None:
                return None
            
            # Scale features if scaler is available
            if self.scaler:
                features = self.scaler.transform(features)
            
            # Get prediction and probability
            prediction = self.model.predict(features)[0]
            fraud_probability = self.model.predict_proba(features)[0]
            
            # Get fraud score (probability of fraud class)
            fraud_score = fraud_probability[1] if len(fraud_probability) > 1 else fraud_probability[0]
            
            # Determine risk level
            if fraud_score >= 0.7:
                risk_level = "VERY HIGH"
            elif fraud_score >= 0.5:
                risk_level = "HIGH"
            elif fraud_score >= 0.3:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            return {
                'transaction_id': transaction.get('transaction_id', 'N/A'),
                'is_fraud': bool(prediction),
                'fraud_score': float(fraud_score),
                'risk_level': risk_level,
                'amount': transaction.get('amount', 0),
                'merchant': transaction.get('merchant', 'Unknown'),
                'transaction_type': transaction.get('transaction_type', 'Unknown')
            }
            
        except Exception as e:
            print(f"❌ Error predicting fraud: {str(e)}")
            return None
    
    def analyze_batch(self, transactions):
        """Analyze a batch of transactions"""
        results = []
        fraud_count = 0
        total_amount = 0
        
        print(f"\n🔍 ANALYZING {len(transactions)} UPI TRANSACTIONS")
        print("=" * 60)
        
        for i, transaction in enumerate(transactions, 1):
            result = self.predict_fraud(transaction)
            if result:
                results.append(result)
                total_amount += result['amount']
                if result['is_fraud']:
                    fraud_count += 1
                
                # Print individual result
                fraud_indicator = "🚨 FRAUD" if result['is_fraud'] else "✅ SAFE"
                print(f"\n{i:2d}. Transaction: {result['transaction_id']}")
                print(f"    Amount: ₹{result['amount']:,}")
                print(f"    Type: {result['transaction_type']} | Merchant: {result['merchant']}")
                print(f"    Fraud Score: {result['fraud_score']:.4f}")
                print(f"    Risk Level: {result['risk_level']}")
                print(f"    Decision: {fraud_indicator}")
        
        # Summary statistics
        print("\n" + "=" * 60)
        print("📊 FRAUD ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total Transactions: {len(results)}")
        print(f"Flagged as Fraud: {fraud_count}")
        print(f"Fraud Rate: {(fraud_count/len(results)*100):.1f}%")
        print(f"Total Amount: ₹{total_amount:,}")
        
        if fraud_count > 0:
            fraud_amount = sum(r['amount'] for r in results if r['is_fraud'])
            print(f"Fraudulent Amount: ₹{fraud_amount:,}")
            print(f"Amount at Risk: {(fraud_amount/total_amount*100):.1f}%")
        
        # Risk distribution
        risk_counts = {}
        for result in results:
            risk_level = result['risk_level']
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        print(f"\n📈 RISK DISTRIBUTION:")
        for risk, count in sorted(risk_counts.items()):
            percentage = (count/len(results)*100)
            print(f"  {risk}: {count} transactions ({percentage:.1f}%)")
        
        return results

def interactive_mode(detector):
    """Interactive mode for single transaction testing"""
    print("\n🎯 INTERACTIVE UPI FRAUD DETECTION")
    print("Enter transaction details (press Enter for defaults)")
    print("-" * 50)
    
    while True:
        try:
            transaction = {}
            
            # Get transaction details
            transaction['transaction_id'] = input("Transaction ID [TXN001]: ") or "TXN001"
            transaction['amount'] = float(input("Amount (₹) [1000]: ") or "1000")
            
            transaction['transaction_type'] = input("Type [P2M/Bill Payment/P2P] [P2M]: ") or "P2M"
            transaction['merchant'] = input("Merchant [Other/Grocery/Shopping] [Other]: ") or "Other"
            transaction['transaction_status'] = input("Status [SUCCESS/FAILED] [SUCCESS]: ") or "SUCCESS"
            
            transaction['sender_age'] = input("Sender Age [18-25/26-35/36-45/46-55/56+] [26-35]: ") or "26-35"
            transaction['receiver_age'] = input("Receiver Age [18-25/26-35/36-45/46-55/56+] [26-35]: ") or "26-35"
            
            transaction['sender_state'] = input("Sender State [Maharashtra]: ") or "Maharashtra"
            transaction['receiver_state'] = input("Receiver State [Karnataka]: ") or "Karnataka"
            
            transaction['sender_bank'] = input("Sender Bank [SBI/ICICI/HDFC/Axis/PNB] [SBI]: ") or "SBI"
            transaction['receiver_bank'] = input("Receiver Bank [SBI/ICICI/HDFC/Axis/PNB] [ICICI]: ") or "ICICI"
            
            transaction['device_type'] = input("Device [Android/iOS/Web] [Android]: ") or "Android"
            transaction['network_type'] = input("Network [4G/5G/WiFi] [4G]: ") or "4G"
            
            transaction['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Analyze transaction
            print("\n🔍 ANALYZING TRANSACTION...")
            result = detector.predict_fraud(transaction)
            
            if result:
                print("\n" + "="*40)
                print("🎯 FRAUD DETECTION RESULT")
                print("="*40)
                print(f"Transaction ID: {result['transaction_id']}")
                print(f"Amount: ₹{result['amount']:,}")
                print(f"Fraud Score: {result['fraud_score']:.4f}")
                print(f"Risk Level: {result['risk_level']}")
                print(f"Decision: {'🚨 POTENTIAL FRAUD' if result['is_fraud'] else '✅ LEGITIMATE'}")
                
                # Banking recommendation
                if result['fraud_score'] >= 0.7:
                    print("🏦 Banking Action: BLOCK TRANSACTION")
                elif result['fraud_score'] >= 0.5:
                    print("🏦 Banking Action: REQUIRE ADDITIONAL VERIFICATION")
                elif result['fraud_score'] >= 0.3:
                    print("🏦 Banking Action: MONITOR CLOSELY")
                else:
                    print("🏦 Banking Action: APPROVE")
            
            # Continue?
            continue_test = input("\nTest another transaction? (y/N): ").lower()
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
    parser.add_argument('--data', type=str, help='JSON file or JSON string with transaction data')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('--model', type=str, help='Path to model file')
    
    args = parser.parse_args()
    
    print("🚀 UPI FRAUD DETECTION SYSTEM")
    print("=" * 50)
    
    # Initialize detector
    detector = UPIFraudDetector(args.model)
    
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
        print("Examples:")
        print("  python upi_fraud_detector.py --interactive")
        print("  python upi_fraud_detector.py --data 'your_json_data'")

if __name__ == "__main__":
    main()
