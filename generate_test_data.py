#!/usr/bin/env python3
"""
Generate Test Datasets for UPI and Credit Card Fraud Detection
Creates realistic, challenging test cases to validate our models
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string

class TestDataGenerator:
    """Generate realistic test datasets for fraud detection"""
    
    def __init__(self):
        self.upi_banks = ['paytm', 'phonepe', 'googlepay', 'amazone', 'ibl', 'sbi', 'hdfc', 'icici', 'axis', 'kotak']
        self.merchant_categories = ['grocery', 'fuel', 'restaurant', 'shopping', 'entertainment', 'utilities', 'medical', 'education']
        self.cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune', 'Ahmedabad']
        
    def generate_upi_dataset(self, n_samples=200):
        """Generate realistic UPI transaction dataset with fraud cases"""
        print(f"🏦 Generating {n_samples} UPI transactions...")
        
        data = []
        start_date = datetime.now() - timedelta(days=30)
        
        for i in range(n_samples):
            # Determine if this is fraud (20% fraud rate)
            is_fraud = random.random() < 0.2
            
            # Generate transaction
            transaction = self._generate_upi_transaction(i, start_date, is_fraud)
            data.append(transaction)
        
        df = pd.DataFrame(data)
        
        # Add some challenging fraud patterns
        df = self._add_upi_fraud_patterns(df)
        
        print(f"✅ Generated UPI dataset: {len(df)} transactions, {df['is_fraud'].sum()} fraud cases")
        return df
    
    def generate_credit_card_dataset(self, n_samples=200, format_type='detailed'):
        """Generate realistic Credit Card dataset"""
        print(f"💳 Generating {n_samples} Credit Card transactions ({format_type} format)...")
        
        if format_type == 'pca':
            return self._generate_cc_pca_dataset(n_samples)
        else:
            return self._generate_cc_detailed_dataset(n_samples)
    
    def _generate_upi_transaction(self, transaction_id, start_date, is_fraud):
        """Generate single UPI transaction"""
        
        # Base transaction details
        timestamp = start_date + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Generate VPAs
        payer_name = self._generate_name()
        payee_name = self._generate_name()
        payer_bank = random.choice(self.upi_banks)
        payee_bank = random.choice(self.upi_banks)
        
        payer_vpa = f"{payer_name}@{payer_bank}"
        payee_vpa = f"{payee_name}@{payee_bank}"
        
        # Transaction type
        transaction_types = ['P2P', 'P2M', 'Bill Payment', 'Merchant Payment']
        transaction_type = random.choice(transaction_types)
        
        if is_fraud:
            # Fraud patterns
            amount = self._generate_fraud_amount_upi()
            # Fraudulent transactions often happen at odd hours
            if random.random() < 0.6:
                timestamp = timestamp.replace(hour=random.choice([1, 2, 3, 4, 23]))
            # Often from suspicious VPAs
            if random.random() < 0.4:
                payer_vpa = f"user{random.randint(1000000, 9999999)}@{payer_bank}"
        else:
            # Normal transaction amounts
            amount = round(random.uniform(10, 5000), 2)
        
        return {
            'transaction_id': f"UPI_{transaction_id:06d}",
            'amount (INR)': amount,
            'payer_vpa': payer_vpa,
            'payee_vpa': payee_vpa,
            'transaction_type': transaction_type,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'merchant_id': f"MERCH_{random.randint(1000, 9999)}" if transaction_type in ['P2M', 'Merchant Payment'] else None,
            'merchant_category': random.choice(self.merchant_categories) if transaction_type in ['P2M', 'Merchant Payment'] else None,
            'device_id': f"DEV_{random.randint(100000, 999999)}",
            'ip_address': f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            'location': random.choice(self.cities),
            'is_fraud': 1 if is_fraud else 0
        }
    
    def _generate_cc_detailed_dataset(self, n_samples):
        """Generate detailed credit card dataset"""
        data = []
        start_time = datetime.now() - timedelta(days=30)
        
        for i in range(n_samples):
            is_fraud = random.random() < 0.15  # 15% fraud rate
            
            # Customer info
            customer = self._generate_customer()
            
            # Transaction details
            amount = self._generate_fraud_amount_cc() if is_fraud else round(random.uniform(1, 1000), 2)
            
            # Merchant info
            merchant = self._generate_merchant()
            
            # Geographic info
            if is_fraud and random.random() < 0.7:
                # Fraudulent transactions often from different locations
                lat, long = self._generate_distant_location(customer['lat'], customer['long'])
            else:
                lat, long = self._generate_nearby_location(customer['lat'], customer['long'])
            
            unix_time = int((start_time + timedelta(days=random.randint(0, 30), 
                                                  hours=random.randint(0, 23),
                                                  minutes=random.randint(0, 59))).timestamp())
            
            transaction = {
                'trans_date_trans_time': datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S'),
                'cc_num': customer['cc_num'],
                'merchant': merchant['name'],
                'category': merchant['category'],
                'amt': amount,
                'first': customer['first'],
                'last': customer['last'],
                'gender': customer['gender'],
                'street': customer['street'],
                'city': customer['city'],
                'state': customer['state'],
                'zip': customer['zip'],
                'lat': lat,
                'long': long,
                'city_pop': customer['city_pop'],
                'job': customer['job'],
                'dob': customer['dob'],
                'trans_num': f"CC_{i:06d}",
                'unix_time': unix_time,
                'merch_lat': merchant['lat'],
                'merch_long': merchant['long'],
                'is_fraud': 1 if is_fraud else 0
            }
            
            data.append(transaction)
        
        df = pd.DataFrame(data)
        print(f"✅ Generated Credit Card detailed dataset: {len(df)} transactions, {df['is_fraud'].sum()} fraud cases")
        return df
    
    def _generate_cc_pca_dataset(self, n_samples):
        """Generate PCA-style credit card dataset (V1-V28 anonymized features)"""
        print("🔍 Generating PCA-anonymized credit card dataset...")
        
        data = []
        base_time = 0
        
        for i in range(n_samples):
            is_fraud = random.random() < 0.172  # Similar to real CC fraud rate
            
            # Generate V1-V28 features using realistic distributions
            v_features = {}
            
            if is_fraud:
                # Fraud cases have different statistical patterns in V features
                for j in range(1, 29):
                    if j <= 14:
                        # First 14 V features often show stronger fraud signals
                        v_features[f'V{j}'] = np.random.normal(
                            loc=random.uniform(-2, 2), 
                            scale=random.uniform(0.5, 3)
                        )
                    else:
                        # Later V features are more subtle
                        v_features[f'V{j}'] = np.random.normal(
                            loc=random.uniform(-1, 1), 
                            scale=random.uniform(0.8, 2)
                        )
                
                # Fraud amounts tend to be higher or very specific
                amount = round(random.choice([
                    random.uniform(500, 5000),  # High amounts
                    random.uniform(0.01, 1),    # Micro amounts (testing)
                    random.uniform(100, 200)    # Specific ranges
                ]), 2)
            else:
                # Normal transactions have different V patterns
                for j in range(1, 29):
                    v_features[f'V{j}'] = np.random.normal(
                        loc=random.uniform(-0.5, 0.5), 
                        scale=random.uniform(0.8, 1.5)
                    )
                
                # Normal amounts
                amount = round(random.uniform(1, 300), 2)
            
            # Time feature (seconds from first transaction)
            time_seconds = base_time + random.randint(0, 86400)  # Up to 1 day
            base_time = time_seconds
            
            transaction = {
                'Time': time_seconds,
                'Amount': amount,
                'Class': 1 if is_fraud else 0,
                **v_features
            }
            
            data.append(transaction)
        
        df = pd.DataFrame(data)
        print(f"✅ Generated Credit Card PCA dataset: {len(df)} transactions, {df['Class'].sum()} fraud cases")
        return df
    
    def _generate_name(self):
        """Generate random name for VPA"""
        first_names = ['amit', 'priya', 'rahul', 'sneha', 'arjun', 'kavya', 'vikram', 'anita']
        last_names = ['sharma', 'patel', 'kumar', 'singh', 'gupta', 'joshi', 'mehta', 'reddy']
        return f"{random.choice(first_names)}.{random.choice(last_names)}{random.randint(1, 99)}"
    
    def _generate_fraud_amount_upi(self):
        """Generate typical fraud amounts for UPI"""
        fraud_patterns = [
            lambda: round(random.uniform(50000, 100000), 2),  # High amounts
            lambda: round(random.uniform(0.01, 1), 2),        # Testing amounts
            lambda: round(random.uniform(9999, 10001), 2),    # Round amounts
            lambda: round(random.uniform(4999, 5001), 2),     # Limit testing
        ]
        return random.choice(fraud_patterns)()
    
    def _generate_fraud_amount_cc(self):
        """Generate typical fraud amounts for Credit Cards"""
        fraud_patterns = [
            lambda: round(random.uniform(1000, 5000), 2),     # High amounts
            lambda: round(random.uniform(0.01, 1), 2),        # Micro amounts
            lambda: round(random.uniform(99.99, 100.01), 2),  # Round amounts
            lambda: round(random.uniform(500, 600), 2),       # Common fraud range
        ]
        return random.choice(fraud_patterns)()
    
    def _generate_customer(self):
        """Generate customer details"""
        first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emily', 'Chris', 'Lisa']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
        jobs = ['Engineer', 'Teacher', 'Doctor', 'Lawyer', 'Manager', 'Analyst', 'Consultant', 'Designer']
        
        return {
            'first': random.choice(first_names),
            'last': random.choice(last_names),
            'gender': random.choice(['M', 'F']),
            'street': f"{random.randint(1, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Cedar'])} St",
            'city': random.choice(self.cities),
            'state': random.choice(['CA', 'NY', 'TX', 'FL', 'WA', 'IL', 'PA', 'OH']),
            'zip': random.randint(10000, 99999),
            'lat': round(random.uniform(25, 45), 6),
            'long': round(random.uniform(-125, -70), 6),
            'city_pop': random.randint(10000, 5000000),
            'job': random.choice(jobs),
            'dob': f"{random.randint(1950, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            'cc_num': f"{random.randint(4000, 4999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
        }
    
    def _generate_merchant(self):
        """Generate merchant details"""
        merchant_names = ['Amazon', 'Walmart', 'Starbucks', 'McDonalds', 'Shell', 'Target', 'CVS', 'HomeDepot']
        categories = ['retail', 'restaurant', 'gas', 'grocery', 'pharmacy', 'entertainment', 'online', 'services']
        
        return {
            'name': random.choice(merchant_names),
            'category': random.choice(categories),
            'lat': round(random.uniform(25, 45), 6),
            'long': round(random.uniform(-125, -70), 6)
        }
    
    def _generate_nearby_location(self, base_lat, base_long):
        """Generate location near customer's location"""
        lat_offset = random.uniform(-0.1, 0.1)
        long_offset = random.uniform(-0.1, 0.1)
        return round(base_lat + lat_offset, 6), round(base_long + long_offset, 6)
    
    def _generate_distant_location(self, base_lat, base_long):
        """Generate location far from customer (fraud indicator)"""
        lat_offset = random.uniform(-10, 10)
        long_offset = random.uniform(-10, 10)
        return round(base_lat + lat_offset, 6), round(base_long + long_offset, 6)
    
    def _add_upi_fraud_patterns(self, df):
        """Add sophisticated fraud patterns to UPI dataset"""
        
        # Pattern 1: Multiple transactions from same device in short time
        fraud_indices = df[df['is_fraud'] == 1].index[:5]
        if len(fraud_indices) > 2:
            same_device = f"DEV_{random.randint(100000, 999999)}"
            df.loc[fraud_indices[:3], 'device_id'] = same_device
        
        # Pattern 2: Round amounts in fraud cases
        high_fraud_indices = df[(df['is_fraud'] == 1) & (df['amount (INR)'] > 1000)].index
        if len(high_fraud_indices) > 0:
            df.loc[random.choice(high_fraud_indices), 'amount (INR)'] = 50000.0
        
        return df

def main():
    """Generate test datasets"""
    generator = TestDataGenerator()
    
    # Generate UPI dataset
    upi_df = generator.generate_upi_dataset(200)
    upi_df.to_csv('test_upi_transactions.csv', index=False)
    print("💾 Saved: test_upi_transactions.csv")
    
    # Generate Credit Card detailed dataset
    cc_detailed_df = generator.generate_credit_card_dataset(200, 'detailed')
    cc_detailed_df.to_csv('test_credit_card_detailed.csv', index=False)
    print("💾 Saved: test_credit_card_detailed.csv")
    
    # Generate Credit Card PCA dataset
    cc_pca_df = generator.generate_credit_card_dataset(200, 'pca')
    cc_pca_df.to_csv('test_credit_card_pca.csv', index=False)
    print("💾 Saved: test_credit_card_pca.csv")
    
    print("\n🎯 Test Datasets Summary:")
    print(f"UPI: {len(upi_df)} transactions, {upi_df['is_fraud'].sum()} fraud ({upi_df['is_fraud'].mean()*100:.1f}%)")
    print(f"CC Detailed: {len(cc_detailed_df)} transactions, {cc_detailed_df['is_fraud'].sum()} fraud ({cc_detailed_df['is_fraud'].mean()*100:.1f}%)")
    print(f"CC PCA: {len(cc_pca_df)} transactions, {cc_pca_df['Class'].sum()} fraud ({cc_pca_df['Class'].mean()*100:.1f}%)")

if __name__ == "__main__":
    main()
