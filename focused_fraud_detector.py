#!/usr/bin/env python3
"""
Analysis of Current Fraud Detection Issues and Solutions

PROBLEMS IDENTIFIED:
1. Universal system is too complex and affecting accuracy
2. Model confusion between different data formats
3. Feature engineering inconsistencies
4. Loss of domain-specific expertise

SOLUTION: Focused UPI + Credit Card System
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

class FocusedFraudDetector:
    """
    Focused fraud detector for UPI and Credit Card transactions only
    Handles feature variations within each domain properly
    """
    
    def __init__(self):
        self.upi_model = None
        self.cc_model = None
        self.upi_scaler = StandardScaler()
        self.cc_scaler = StandardScaler()
        self.upi_encoders = {}
        self.cc_encoders = {}
        
    def analyze_upi_features(self, df):
        """Analyze UPI dataset features and understand their meaning"""
        print("🔍 UPI Feature Analysis:")
        print(f"Dataset shape: {df.shape}")
        print("\n📋 UPI Columns detected:")
        
        upi_feature_map = {
            'amount (INR)': 'Transaction amount in Indian Rupees',
            'payer_vpa': 'Virtual Payment Address of sender',
            'payee_vpa': 'Virtual Payment Address of receiver', 
            'transaction_type': 'Type of UPI transaction (P2P, P2M, etc.)',
            'timestamp': 'Transaction timestamp',
            'merchant_id': 'Merchant identifier for P2M transactions',
            'merchant_category': 'Category of merchant business',
            'device_id': 'Device used for transaction',
            'ip_address': 'IP address of transaction origin',
            'location': 'Geographic location of transaction',
            'is_fraud': 'Fraud label (target variable)'
        }
        
        for col in df.columns:
            description = upi_feature_map.get(col, 'Unknown UPI feature')
            print(f"  - {col}: {description}")
            
        return upi_feature_map
    
    def analyze_credit_card_features(self, df):
        """Analyze Credit Card features including V1-V28 anonymized features"""
        print("🔍 Credit Card Feature Analysis:")
        print(f"Dataset shape: {df.shape}")
        print("\n📋 Credit Card Columns detected:")
        
        # V1-V28 are PCA-transformed features from the original credit card dataset
        # These represent anonymized financial behavior patterns
        v_features_meaning = {
            'V1-V28': 'PCA-transformed anonymized features representing:',
            'details': [
                'Customer spending patterns',
                'Transaction frequency patterns', 
                'Merchant interaction history',
                'Geographic spending patterns',
                'Temporal spending behavior',
                'Account age and history factors',
                'Risk indicators from past transactions',
                'Statistical aggregations of account behavior'
            ]
        }
        
        cc_feature_map = {
            'Time': 'Seconds elapsed since first transaction in dataset',
            'Amount': 'Transaction amount',
            'Class': 'Fraud label (0=normal, 1=fraud)',
            # V features
            **{f'V{i}': f'PCA component {i} - anonymized behavioral feature' for i in range(1, 29)}
        }
        
        # Extended credit card features (if present)
        extended_cc_features = {
            'amt': 'Transaction amount',
            'merchant': 'Merchant name or ID',
            'category': 'Merchant category code',
            'city': 'Transaction city',
            'state': 'Transaction state',
            'zip': 'ZIP code of transaction',
            'lat': 'Latitude of transaction',
            'long': 'Longitude of transaction',
            'city_pop': 'Population of transaction city',
            'job': 'Cardholder job category',
            'dob': 'Date of birth',
            'trans_date_trans_time': 'Transaction timestamp',
            'cc_num': 'Credit card number (masked)',
            'first': 'First name',
            'last': 'Last name',
            'street': 'Street address',
            'unix_time': 'Unix timestamp',
            'merch_lat': 'Merchant latitude',
            'merch_long': 'Merchant longitude',
            'is_fraud': 'Fraud indicator'
        }
        
        for col in df.columns:
            if col.startswith('V') and col[1:].isdigit():
                description = cc_feature_map.get(col, 'PCA anonymized feature')
            else:
                description = extended_cc_features.get(col, cc_feature_map.get(col, 'Unknown CC feature'))
            print(f"  - {col}: {description}")
            
        print(f"\n🧠 V1-V28 Features Explained:")
        print(f"These are the result of Principal Component Analysis (PCA) applied to:")
        for detail in v_features_meaning['details']:
            print(f"  • {detail}")
        print(f"\nThey capture complex patterns in financial behavior that are highly predictive of fraud.")
            
        return cc_feature_map, extended_cc_features
    
    def engineer_upi_features(self, df):
        """Engineer features specifically for UPI transactions"""
        features = pd.DataFrame()
        
        # Amount features
        if 'amount (INR)' in df.columns:
            features['amount'] = df['amount (INR)'].fillna(0)
            features['amount_log'] = np.log1p(features['amount'])
            features['is_round_amount'] = (features['amount'] % 100 == 0).astype(int)
            features['is_high_amount'] = (features['amount'] > features['amount'].quantile(0.95)).astype(int)
            features['amount_zscore'] = np.abs((features['amount'] - features['amount'].mean()) / features['amount'].std())
        
        # VPA features (critical for UPI fraud detection)
        if 'payer_vpa' in df.columns:
            # Extract domain from VPA
            payer_domains = df['payer_vpa'].str.split('@').str[-1].fillna('unknown')
            features['payer_domain_encoded'] = self._encode_categorical('payer_domain', payer_domains, 'upi')
            
            # VPA complexity (fraudulent VPAs often have patterns)
            features['payer_vpa_length'] = df['payer_vpa'].str.len().fillna(0)
            features['payer_has_numbers'] = df['payer_vpa'].str.contains('\d', na=False).astype(int)
        
        if 'payee_vpa' in df.columns:
            payee_domains = df['payee_vpa'].str.split('@').str[-1].fillna('unknown')
            features['payee_domain_encoded'] = self._encode_categorical('payee_domain', payee_domains, 'upi')
            features['payee_vpa_length'] = df['payee_vpa'].str.len().fillna(0)
        
        # Transaction type features
        if 'transaction_type' in df.columns:
            features['transaction_type_encoded'] = self._encode_categorical('transaction_type', df['transaction_type'], 'upi')
        
        # Temporal features
        if 'timestamp' in df.columns:
            timestamps = pd.to_datetime(df['timestamp'], errors='coerce')
            features['hour'] = timestamps.dt.hour
            features['day_of_week'] = timestamps.dt.dayofweek
            features['is_weekend'] = (timestamps.dt.dayofweek >= 5).astype(int)
            features['is_night'] = ((timestamps.dt.hour < 6) | (timestamps.dt.hour > 22)).astype(int)
        
        # Device and location features
        if 'device_id' in df.columns:
            features['device_id_encoded'] = self._encode_categorical('device_id', df['device_id'], 'upi')
        
        if 'location' in df.columns:
            features['location_encoded'] = self._encode_categorical('location', df['location'], 'upi')
        
        return features.fillna(0)
    
    def engineer_credit_card_features(self, df):
        """Engineer features for credit card transactions (handles both PCA and detailed formats)"""
        features = pd.DataFrame()
        
        # Check if this is PCA format (V1-V28) or detailed format
        v_columns = [col for col in df.columns if col.startswith('V') and col[1:].isdigit()]
        is_pca_format = len(v_columns) > 10
        
        if is_pca_format:
            print("🔍 Detected PCA format - using V1-V28 features")
            # Use V features directly (they're already optimized)
            for col in v_columns:
                if col in df.columns:
                    features[f'{col}_normalized'] = df[col].fillna(0)
            
            # Time and Amount features
            if 'Time' in df.columns:
                features['time'] = df['Time'].fillna(0)
                features['time_hour'] = (df['Time'] % 86400) // 3600  # Convert to hour of day
                features['time_day'] = df['Time'] // 86400  # Day number
            
            if 'Amount' in df.columns:
                features['amount'] = df['Amount'].fillna(0)
                features['amount_log'] = np.log1p(features['amount'])
                features['is_zero_amount'] = (features['amount'] == 0).astype(int)
        
        else:
            print("🔍 Detected detailed format - engineering comprehensive features")
            # Detailed credit card format
            amount_cols = ['amt', 'Amount']
            amount_col = None
            for col in amount_cols:
                if col in df.columns:
                    amount_col = col
                    break
            
            if amount_col:
                features['amount'] = df[amount_col].fillna(0)
                features['amount_log'] = np.log1p(features['amount'])
                features['is_round_amount'] = (features['amount'] % 1 == 0).astype(int)
                features['amount_zscore'] = np.abs((features['amount'] - features['amount'].mean()) / features['amount'].std())
            
            # Merchant features
            if 'merchant' in df.columns:
                features['merchant_encoded'] = self._encode_categorical('merchant', df['merchant'], 'cc')
            
            if 'category' in df.columns:
                features['category_encoded'] = self._encode_categorical('category', df['category'], 'cc')
            
            # Geographic features
            geo_features = ['lat', 'long', 'merch_lat', 'merch_long']
            for geo_col in geo_features:
                if geo_col in df.columns:
                    features[f'{geo_col}_normalized'] = df[geo_col].fillna(0)
            
            # Distance between customer and merchant
            if all(col in df.columns for col in ['lat', 'long', 'merch_lat', 'merch_long']):
                features['distance_to_merchant'] = np.sqrt(
                    (df['lat'] - df['merch_lat'])**2 + (df['long'] - df['merch_long'])**2
                ).fillna(0)
            
            # Temporal features
            if 'unix_time' in df.columns:
                timestamps = pd.to_datetime(df['unix_time'], unit='s', errors='coerce')
                features['hour'] = timestamps.dt.hour
                features['day_of_week'] = timestamps.dt.dayofweek
                features['is_weekend'] = (timestamps.dt.dayofweek >= 5).astype(int)
            
            # Population and demographic features
            if 'city_pop' in df.columns:
                features['city_pop_log'] = np.log1p(df['city_pop'].fillna(0))
                features['is_high_pop_city'] = (df['city_pop'] > df['city_pop'].quantile(0.8)).astype(int)
        
        return features.fillna(0)
    
    def _encode_categorical(self, feature_name, data, model_type):
        """Encode categorical features with proper handling"""
        encoder_key = f"{model_type}_{feature_name}"
        encoders_dict = self.upi_encoders if model_type == 'upi' else self.cc_encoders
        
        if encoder_key not in encoders_dict:
            encoders_dict[encoder_key] = LabelEncoder()
            return encoders_dict[encoder_key].fit_transform(data.astype(str))
        else:
            try:
                return encoders_dict[encoder_key].transform(data.astype(str))
            except ValueError:
                # Handle unseen categories
                return np.zeros(len(data))
    
    def detect_transaction_type(self, df):
        """Detect whether dataset is UPI or Credit Card"""
        columns = set(df.columns)
        
        # UPI indicators
        upi_indicators = {'amount (INR)', 'payer_vpa', 'payee_vpa', 'transaction_type'}
        upi_score = len(upi_indicators.intersection(columns))
        
        # Credit Card PCA indicators
        v_columns = len([col for col in df.columns if col.startswith('V') and col[1:].isdigit()])
        cc_pca_score = 1 if (v_columns > 10 and ('Amount' in columns or 'Time' in columns)) else 0
        
        # Credit Card detailed indicators
        cc_detailed_indicators = {'amt', 'merchant', 'city', 'lat', 'long'}
        cc_detailed_score = len(cc_detailed_indicators.intersection(columns))
        
        print(f"🎯 Detection Scores:")
        print(f"UPI: {upi_score}/4 indicators")
        print(f"CC PCA: {cc_pca_score} (V columns: {v_columns})")
        print(f"CC Detailed: {cc_detailed_score}/5 indicators")
        
        if upi_score >= 2:
            return 'upi'
        elif cc_pca_score > 0 or cc_detailed_score >= 3:
            return 'credit_card'
        else:
            return 'unknown'
    
    def train_models(self, df, fraud_column):
        """Train specialized models for the detected transaction type"""
        transaction_type = self.detect_transaction_type(df)
        
        if transaction_type == 'upi':
            print("🏦 Training UPI Fraud Detection Model")
            self.analyze_upi_features(df)
            features = self.engineer_upi_features(df)
            
            if fraud_column in df.columns:
                y = df[fraud_column]
                X_train, X_test, y_train, y_test = train_test_split(features, y, test_size=0.2, random_state=42)
                
                X_train_scaled = self.upi_scaler.fit_transform(X_train)
                X_test_scaled = self.upi_scaler.transform(X_test)
                
                self.upi_model = RandomForestClassifier(n_estimators=100, random_state=42)
                self.upi_model.fit(X_train_scaled, y_train)
                
                y_pred = self.upi_model.predict(X_test_scaled)
                print("\n📊 UPI Model Performance:")
                print(classification_report(y_test, y_pred))
                
                return 'upi', features.columns.tolist()
        
        elif transaction_type == 'credit_card':
            print("💳 Training Credit Card Fraud Detection Model")
            self.analyze_credit_card_features(df)
            features = self.engineer_credit_card_features(df)
            
            if fraud_column in df.columns:
                y = df[fraud_column]
                X_train, X_test, y_train, y_test = train_test_split(features, y, test_size=0.2, random_state=42)
                
                X_train_scaled = self.cc_scaler.fit_transform(X_train)
                X_test_scaled = self.cc_scaler.transform(X_test)
                
                self.cc_model = RandomForestClassifier(n_estimators=100, random_state=42)
                self.cc_model.fit(X_train_scaled, y_train)
                
                y_pred = self.cc_model.predict(X_test_scaled)
                print("\n📊 Credit Card Model Performance:")
                print(classification_report(y_test, y_pred))
                
                return 'credit_card', features.columns.tolist()
        
        else:
            print("❌ Unknown transaction type - cannot train model")
            return None, []

if __name__ == "__main__":
    print("🎯 Focused Fraud Detector Analysis")
    print("This system handles UPI and Credit Card fraud detection with proper feature understanding")
    
    # Test with existing datasets
    detector = FocusedFraudDetector()
    
    # You can test this with your datasets:
    # df = pd.read_csv('your_upi_dataset.csv')
    # detector.train_models(df, 'is_fraud')
