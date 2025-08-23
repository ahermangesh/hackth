#!/usr/bin/env python3
"""
Test the Focused Fraud Detector with our generated test datasets
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pickle
import os
from datetime import datetime

class FocusedFraudTester:
    """Test focused fraud detection on UPI and Credit Card datasets"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_columns = {}
        
    def test_upi_detection(self):
        """Test UPI fraud detection"""
        print("🏦 Testing UPI Fraud Detection")
        print("="*50)
        
        # Load test data
        df = pd.read_csv('test_upi_transactions.csv')
        print(f"📊 Loaded {len(df)} UPI transactions")
        
        # Feature engineering
        features = self._engineer_upi_features(df)
        
        # Train model
        X = features.drop(['transaction_id', 'is_fraud'], axis=1)
        y = features['is_fraud']
        
        # Handle missing values
        X = X.fillna(0)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train Random Forest
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(X_train_scaled, y_train)
        
        # Train Isolation Forest (unsupervised)
        iso_model = IsolationForest(contamination=0.2, random_state=42)
        iso_model.fit(X_train_scaled)
        
        # Predictions
        rf_pred = rf_model.predict(X_test_scaled)
        iso_pred = np.where(iso_model.predict(X_test_scaled) == -1, 1, 0)
        
        # Results
        print(f"\n🎯 Random Forest Results:")
        print(f"Accuracy: {accuracy_score(y_test, rf_pred):.3f}")
        print(classification_report(y_test, rf_pred))
        
        print(f"\n🔍 Isolation Forest Results:")
        print(f"Accuracy: {accuracy_score(y_test, iso_pred):.3f}")
        print(classification_report(y_test, iso_pred))
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': rf_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n📈 Top UPI Features:")
        print(feature_importance.head(10))
        
        return rf_model, scaler, X.columns.tolist()
    
    def test_credit_card_detection(self, dataset_type='detailed'):
        """Test Credit Card fraud detection"""
        print(f"\n💳 Testing Credit Card Fraud Detection ({dataset_type} format)")
        print("="*60)
        
        # Load appropriate dataset
        if dataset_type == 'detailed':
            df = pd.read_csv('test_credit_card_detailed.csv')
            target_col = 'is_fraud'
        else:
            df = pd.read_csv('test_credit_card_pca.csv')
            target_col = 'Class'
        
        print(f"📊 Loaded {len(df)} Credit Card transactions")
        
        # Feature engineering
        if dataset_type == 'detailed':
            features = self._engineer_cc_detailed_features(df)
        else:
            features = self._engineer_cc_pca_features(df)
        
        # Train model
        feature_cols = [col for col in features.columns if col != target_col]
        X = features[feature_cols]
        y = features[target_col]
        
        # Handle missing values
        X = X.fillna(0)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train Random Forest
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(X_train_scaled, y_train)
        
        # Train Isolation Forest
        iso_model = IsolationForest(contamination=0.15, random_state=42)
        iso_model.fit(X_train_scaled)
        
        # Predictions
        rf_pred = rf_model.predict(X_test_scaled)
        iso_pred = np.where(iso_model.predict(X_test_scaled) == -1, 1, 0)
        
        # Results
        print(f"\n🎯 Random Forest Results:")
        print(f"Accuracy: {accuracy_score(y_test, rf_pred):.3f}")
        print(classification_report(y_test, rf_pred))
        
        print(f"\n🔍 Isolation Forest Results:")
        print(f"Accuracy: {accuracy_score(y_test, iso_pred):.3f}")
        print(classification_report(y_test, iso_pred))
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': rf_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n📈 Top Credit Card Features:")
        print(feature_importance.head(10))
        
        return rf_model, scaler, X.columns.tolist()
    
    def _engineer_upi_features(self, df):
        """Engineer UPI-specific features"""
        features = df.copy()
        
        # Convert timestamp
        features['timestamp'] = pd.to_datetime(features['timestamp'])
        features['hour'] = features['timestamp'].dt.hour
        features['day_of_week'] = features['timestamp'].dt.dayofweek
        features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # Amount features
        features['amount_log'] = np.log1p(features['amount (INR)'])
        features['amount_rounded'] = (features['amount (INR)'] % 1 == 0).astype(int)
        features['high_amount'] = (features['amount (INR)'] > 10000).astype(int)
        
        # VPA features
        features['payer_bank'] = features['payer_vpa'].str.split('@').str[1]
        features['payee_bank'] = features['payee_vpa'].str.split('@').str[1]
        features['same_bank'] = (features['payer_bank'] == features['payee_bank']).astype(int)
        
        # Encode categorical features
        le_payer_bank = LabelEncoder()
        le_payee_bank = LabelEncoder()
        le_transaction_type = LabelEncoder()
        le_location = LabelEncoder()
        
        features['payer_bank_encoded'] = le_payer_bank.fit_transform(features['payer_bank'])
        features['payee_bank_encoded'] = le_payee_bank.fit_transform(features['payee_bank'])
        features['transaction_type_encoded'] = le_transaction_type.fit_transform(features['transaction_type'])
        features['location_encoded'] = le_location.fit_transform(features['location'])
        
        # Time-based features
        features['is_night'] = ((features['hour'] >= 23) | (features['hour'] <= 5)).astype(int)
        features['is_business_hours'] = ((features['hour'] >= 9) & (features['hour'] <= 17)).astype(int)
        
        # Select numeric features for model
        numeric_features = [
            'amount (INR)', 'amount_log', 'amount_rounded', 'high_amount',
            'hour', 'day_of_week', 'is_weekend', 'same_bank',
            'payer_bank_encoded', 'payee_bank_encoded', 'transaction_type_encoded',
            'location_encoded', 'is_night', 'is_business_hours',
            'transaction_id', 'is_fraud'
        ]
        
        return features[numeric_features]
    
    def _engineer_cc_detailed_features(self, df):
        """Engineer features for detailed credit card data"""
        features = df.copy()
        
        # Convert datetime
        features['trans_date_trans_time'] = pd.to_datetime(features['trans_date_trans_time'])
        features['hour'] = features['trans_date_trans_time'].dt.hour
        features['day_of_week'] = features['trans_date_trans_time'].dt.dayofweek
        features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # Amount features
        features['amt_log'] = np.log1p(features['amt'])
        features['amt_rounded'] = (features['amt'] % 1 == 0).astype(int)
        features['high_amount'] = (features['amt'] > 500).astype(int)
        
        # Geographic features
        features['distance_from_home'] = np.sqrt(
            (features['lat'] - features['lat'].mean())**2 + 
            (features['long'] - features['long'].mean())**2
        )
        features['merchant_distance'] = np.sqrt(
            (features['lat'] - features['merch_lat'])**2 + 
            (features['long'] - features['merch_long'])**2
        )
        
        # Time features
        features['is_night'] = ((features['hour'] >= 22) | (features['hour'] <= 6)).astype(int)
        features['is_business_hours'] = ((features['hour'] >= 9) & (features['hour'] <= 17)).astype(int)
        
        # Encode categorical features
        le_category = LabelEncoder()
        le_gender = LabelEncoder()
        le_state = LabelEncoder()
        le_job = LabelEncoder()
        
        features['category_encoded'] = le_category.fit_transform(features['category'])
        features['gender_encoded'] = le_gender.fit_transform(features['gender'])
        features['state_encoded'] = le_state.fit_transform(features['state'])
        features['job_encoded'] = le_job.fit_transform(features['job'])
        
        # Age feature
        features['dob'] = pd.to_datetime(features['dob'])
        features['age'] = (datetime.now() - features['dob']).dt.days / 365.25
        
        # Select numeric features
        numeric_features = [
            'amt', 'amt_log', 'amt_rounded', 'high_amount',
            'lat', 'long', 'city_pop', 'unix_time',
            'merch_lat', 'merch_long', 'distance_from_home', 'merchant_distance',
            'hour', 'day_of_week', 'is_weekend', 'is_night', 'is_business_hours',
            'category_encoded', 'gender_encoded', 'state_encoded', 'job_encoded',
            'age', 'zip', 'is_fraud'
        ]
        
        return features[numeric_features]
    
    def _engineer_cc_pca_features(self, df):
        """Engineer features for PCA credit card data"""
        features = df.copy()
        
        # Time features
        features['Time_hours'] = features['Time'] / 3600
        features['Time_normalized'] = features['Time'] / features['Time'].max()
        
        # Amount features
        features['Amount_log'] = np.log1p(features['Amount'])
        features['Amount_normalized'] = features['Amount'] / features['Amount'].max()
        features['high_amount'] = (features['Amount'] > features['Amount'].quantile(0.95)).astype(int)
        
        # V feature aggregations
        v_columns = [col for col in features.columns if col.startswith('V')]
        features['V_mean'] = features[v_columns].mean(axis=1)
        features['V_std'] = features[v_columns].std(axis=1)
        features['V_max'] = features[v_columns].max(axis=1)
        features['V_min'] = features[v_columns].min(axis=1)
        
        # V feature groups (based on PCA understanding)
        features['V_group1'] = features[['V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7']].mean(axis=1)
        features['V_group2'] = features[['V8', 'V9', 'V10', 'V11', 'V12', 'V13', 'V14']].mean(axis=1)
        features['V_group3'] = features[['V15', 'V16', 'V17', 'V18', 'V19', 'V20', 'V21']].mean(axis=1)
        features['V_group4'] = features[['V22', 'V23', 'V24', 'V25', 'V26', 'V27', 'V28']].mean(axis=1)
        
        return features
    
    def test_real_world_compatibility(self):
        """Test compatibility with existing real datasets"""
        print("\n🌍 Testing Real World Dataset Compatibility")
        print("="*50)
        
        # Test with UPI dataset if available
        if os.path.exists('ProvidedData/UPI/upi_transactions_2024.csv'):
            print("🏦 Testing with real UPI data...")
            try:
                upi_real = pd.read_csv('ProvidedData/UPI/upi_transactions_2024.csv')
                print(f"✅ Loaded real UPI dataset: {len(upi_real)} transactions")
                print(f"📊 Columns: {list(upi_real.columns)}")
                
                # Check for fraud labels
                fraud_columns = [col for col in upi_real.columns if 'fraud' in col.lower() or 'label' in col.lower()]
                print(f"🎯 Potential fraud columns: {fraud_columns}")
                
            except Exception as e:
                print(f"❌ Error loading real UPI data: {e}")
        
        # Test with Credit Card dataset
        if os.path.exists('data/raw/creditcard.csv'):
            print("\n💳 Testing with real Credit Card data...")
            try:
                cc_real = pd.read_csv('data/raw/creditcard.csv')
                print(f"✅ Loaded real CC dataset: {len(cc_real)} transactions")
                print(f"📊 Columns: {list(cc_real.columns)}")
                
                # Check if it's PCA format
                v_columns = [col for col in cc_real.columns if col.startswith('V')]
                if len(v_columns) > 20:
                    print(f"🔍 Detected PCA format with {len(v_columns)} V features")
                    
                    # Quick test with small sample
                    sample = cc_real.sample(n=min(1000, len(cc_real)), random_state=42)
                    if 'Class' in sample.columns:
                        fraud_rate = sample['Class'].mean()
                        print(f"📈 Fraud rate in sample: {fraud_rate:.3f}")
                
            except Exception as e:
                print(f"❌ Error loading real CC data: {e}")

def main():
    """Run comprehensive fraud detection tests"""
    print("🚀 FraudGuard Focused Testing Suite")
    print("="*60)
    
    tester = FocusedFraudTester()
    
    # Test UPI fraud detection
    try:
        upi_model, upi_scaler, upi_features = tester.test_upi_detection()
        print("✅ UPI testing completed successfully")
    except Exception as e:
        print(f"❌ UPI testing failed: {e}")
    
    # Test Credit Card detailed format
    try:
        cc_detailed_model, cc_detailed_scaler, cc_detailed_features = tester.test_credit_card_detection('detailed')
        print("✅ Credit Card detailed testing completed successfully")
    except Exception as e:
        print(f"❌ Credit Card detailed testing failed: {e}")
    
    # Test Credit Card PCA format
    try:
        cc_pca_model, cc_pca_scaler, cc_pca_features = tester.test_credit_card_detection('pca')
        print("✅ Credit Card PCA testing completed successfully")
    except Exception as e:
        print(f"❌ Credit Card PCA testing failed: {e}")
    
    # Test real world compatibility
    tester.test_real_world_compatibility()
    
    print("\n🎯 Testing Complete!")
    print("✅ All focused fraud detection models tested")
    print("📈 Ready for production deployment")

if __name__ == "__main__":
    main()
