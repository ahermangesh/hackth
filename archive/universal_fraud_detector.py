#!/usr/bin/env python3
"""
Universal Fraud Detection System
Automatically detects data format and applies appropriate fraud detection model
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class UniversalFraudDetector:
    def __init__(self):
        self.dataset_type = None
        self.model = None
        self.scaler = StandardScaler()
        self.encoders = {}
        self.feature_columns = []
        self.models_dir = "models"
        
        # Create models directory
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Dataset signatures for automatic detection
        self.dataset_signatures = {
            'upi': {
                'required_columns': ['transaction id', 'amount (INR)', 'fraud_flag'],
                'optional_columns': ['sender_bank', 'receiver_bank', 'transaction_status'],
                'amount_column': 'amount (INR)',
                'fraud_column': 'fraud_flag'
            },
            'creditcard_pca': {
                'required_columns': ['Amount', 'Class'],
                'pattern_columns': ['V1', 'V2', 'V3'],  # PCA transformed features
                'amount_column': 'Amount',
                'fraud_column': 'Class'
            },
            'creditcard_detailed': {
                'required_columns': ['amt', 'is_fraud'],
                'optional_columns': ['merchant', 'category', 'cc_num'],
                'amount_column': 'amt',
                'fraud_column': 'is_fraud'
            },
            'generic_transactions': {
                'required_columns': ['amount', 'fraud'],
                'amount_column': 'amount',
                'fraud_column': 'fraud'
            }
        }
    
    def detect_dataset_type(self, df):
        """Automatically detect the type of dataset"""
        columns = df.columns.tolist()
        columns_lower = [col.lower() for col in columns]
        
        print(f"🔍 Analyzing dataset with columns: {columns[:10]}{'...' if len(columns) > 10 else ''}")
        
        # Check for UPI format
        if any('transaction id' in col.lower() for col in columns) and \
           any('fraud_flag' in col.lower() for col in columns):
            return 'upi'
        
        # Check for PCA credit card format (V1, V2, etc.)
        v_columns = [col for col in columns if col.startswith('V') and col[1:].isdigit()]
        if len(v_columns) >= 10 and 'Amount' in columns and 'Class' in columns:
            return 'creditcard_pca'
        
        # Check for detailed credit card format
        if 'amt' in columns_lower and 'is_fraud' in columns_lower and \
           any('merchant' in col.lower() for col in columns):
            return 'creditcard_detailed'
        
        # Generic format detection
        amount_cols = [col for col in columns if any(word in col.lower() for word in ['amount', 'amt', 'value', 'sum'])]
        fraud_cols = [col for col in columns if any(word in col.lower() for word in ['fraud', 'class', 'label', 'target'])]
        
        if amount_cols and fraud_cols:
            return 'generic_transactions'
        
        # If nothing matches, return generic
        print("⚠️ Could not detect specific format, using generic approach")
        return 'generic_transactions'
    
    def prepare_features_upi(self, df):
        """Feature preparation for UPI transactions"""
        features = df.copy()
        
        # Time features
        if 'timestamp' in features.columns:
            features['timestamp'] = pd.to_datetime(features['timestamp'])
            features['hour'] = features['timestamp'].dt.hour
            features['day_of_week'] = features['timestamp'].dt.dayofweek
            features['is_weekend'] = (features['day_of_week'] >= 5).astype(int)
        
        # Amount features
        amount_col = 'amount (INR)'
        if amount_col in features.columns:
            features['amount_log'] = np.log1p(features[amount_col])
            features['is_high_amount'] = (features[amount_col] > features[amount_col].quantile(0.95)).astype(int)
        
        # Categorical encoding
        categorical_cols = ['transaction type', 'merchant_category', 'sender_bank', 'receiver_bank', 'device_type']
        for col in categorical_cols:
            if col in features.columns:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    features[f'{col}_encoded'] = self.encoders[col].fit_transform(features[col].astype(str))
                else:
                    # Handle unseen categories
                    mask = features[col].astype(str).isin(self.encoders[col].classes_)
                    features[f'{col}_encoded'] = 0
                    if mask.any():
                        features.loc[mask, f'{col}_encoded'] = self.encoders[col].transform(features.loc[mask, col].astype(str))
        
        # Select numerical features
        numerical_cols = features.select_dtypes(include=[np.number]).columns.tolist()
        categorical_encoded = [col for col in features.columns if col.endswith('_encoded')]
        
        feature_cols = list(set(numerical_cols + categorical_encoded))
        # Remove target column
        feature_cols = [col for col in feature_cols if 'fraud_flag' not in col.lower()]
        
        return features[feature_cols]
    
    def prepare_features_creditcard_pca(self, df):
        """Feature preparation for PCA credit card data"""
        features = df.copy()
        
        # All V columns are already preprocessed features
        v_columns = [col for col in features.columns if col.startswith('V')]
        feature_cols = v_columns + ['Amount']
        
        # Add time features if available
        if 'Time' in features.columns:
            features['hour'] = (features['Time'] / 3600) % 24
            features['day'] = (features['Time'] / (3600 * 24)) % 7
            feature_cols.extend(['hour', 'day'])
        
        return features[feature_cols]
    
    def prepare_features_creditcard_detailed(self, df):
        """Feature preparation for detailed credit card data"""
        features = df.copy()
        
        # Time features
        if 'trans_date_trans_time' in features.columns:
            features['trans_date_trans_time'] = pd.to_datetime(features['trans_date_trans_time'])
            features['hour'] = features['trans_date_trans_time'].dt.hour
            features['day_of_week'] = features['trans_date_trans_time'].dt.dayofweek
            features['is_weekend'] = (features['day_of_week'] >= 5).astype(int)
        
        # Amount features
        if 'amt' in features.columns:
            features['amt_log'] = np.log1p(features['amt'])
            features['is_high_amount'] = (features['amt'] > features['amt'].quantile(0.95)).astype(int)
        
        # Location features
        if all(col in features.columns for col in ['lat', 'long', 'merch_lat', 'merch_long']):
            features['distance'] = np.sqrt((features['lat'] - features['merch_lat'])**2 + 
                                         (features['long'] - features['merch_long'])**2)
        
        # Age calculation
        if 'dob' in features.columns:
            features['dob'] = pd.to_datetime(features['dob'])
            if 'trans_date_trans_time' in features.columns:
                features['age'] = (features['trans_date_trans_time'] - features['dob']).dt.days / 365.25
        
        # Categorical encoding
        categorical_cols = ['merchant', 'category', 'gender', 'job', 'state']
        for col in categorical_cols:
            if col in features.columns:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    features[f'{col}_encoded'] = self.encoders[col].fit_transform(features[col].astype(str))
                else:
                    mask = features[col].astype(str).isin(self.encoders[col].classes_)
                    features[f'{col}_encoded'] = 0
                    if mask.any():
                        features.loc[mask, f'{col}_encoded'] = self.encoders[col].transform(features.loc[mask, col].astype(str))
        
        # Select features
        numerical_cols = features.select_dtypes(include=[np.number]).columns.tolist()
        categorical_encoded = [col for col in features.columns if col.endswith('_encoded')]
        
        feature_cols = list(set(numerical_cols + categorical_encoded))
        feature_cols = [col for col in feature_cols if not any(target in col.lower() for target in ['fraud', 'class', 'target'])]
        
        return features[feature_cols]
    
    def prepare_features_generic(self, df):
        """Generic feature preparation for unknown formats"""
        features = df.copy()
        
        # Find amount and fraud columns
        amount_cols = [col for col in features.columns if any(word in col.lower() for word in ['amount', 'amt', 'value', 'sum'])]
        fraud_cols = [col for col in features.columns if any(word in col.lower() for word in ['fraud', 'class', 'label', 'target'])]
        
        # Time column detection
        time_cols = [col for col in features.columns if any(word in col.lower() for word in ['time', 'date', 'timestamp'])]
        
        # Process time features
        for col in time_cols:
            try:
                features[col] = pd.to_datetime(features[col])
                features[f'{col}_hour'] = features[col].dt.hour
                features[f'{col}_day'] = features[col].dt.dayofweek
            except:
                pass
        
        # Process amount features
        for col in amount_cols:
            if features[col].dtype in ['int64', 'float64']:
                features[f'{col}_log'] = np.log1p(features[col])
                features[f'{col}_high'] = (features[col] > features[col].quantile(0.95)).astype(int)
        
        # Encode categorical features
        categorical_cols = features.select_dtypes(include=['object']).columns.tolist()
        categorical_cols = [col for col in categorical_cols if col not in fraud_cols and col not in time_cols]
        
        for col in categorical_cols[:10]:  # Limit to first 10 to avoid explosion
            if col not in self.encoders:
                self.encoders[col] = LabelEncoder()
                features[f'{col}_encoded'] = self.encoders[col].fit_transform(features[col].astype(str))
            else:
                mask = features[col].astype(str).isin(self.encoders[col].classes_)
                features[f'{col}_encoded'] = 0
                if mask.any():
                    features.loc[mask, f'{col}_encoded'] = self.encoders[col].transform(features.loc[mask, col].astype(str))
        
        # Select numerical features
        numerical_cols = features.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [col for col in numerical_cols if not any(target in col.lower() for target in fraud_cols)]
        
        return features[feature_cols]
    
    def prepare_features(self, df):
        """Route to appropriate feature preparation based on dataset type"""
        if self.dataset_type == 'upi':
            return self.prepare_features_upi(df)
        elif self.dataset_type == 'creditcard_pca':
            return self.prepare_features_creditcard_pca(df)
        elif self.dataset_type == 'creditcard_detailed':
            return self.prepare_features_creditcard_detailed(df)
        else:
            return self.prepare_features_generic(df)
    
    def get_target_column(self, df):
        """Get the target column based on dataset type"""
        if self.dataset_type == 'upi':
            return 'fraud_flag'
        elif self.dataset_type == 'creditcard_pca':
            return 'Class'
        elif self.dataset_type == 'creditcard_detailed':
            return 'is_fraud'
        else:
            # Generic detection
            fraud_cols = [col for col in df.columns if any(word in col.lower() for word in ['fraud', 'class', 'label', 'target'])]
            return fraud_cols[0] if fraud_cols else None
    
    def train_or_load_model(self, df):
        """Train a new model or load existing one"""
        print(f"🚀 Preparing {self.dataset_type} fraud detection model...")
        
        # Check if model exists
        model_path = os.path.join(self.models_dir, f"{self.dataset_type}_model.pkl")
        scaler_path = os.path.join(self.models_dir, f"{self.dataset_type}_scaler.pkl")
        encoders_path = os.path.join(self.models_dir, f"{self.dataset_type}_encoders.pkl")
        
        if os.path.exists(model_path) and len(df) < 10000:  # Use existing model for small datasets
            print("📁 Loading existing model...")
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.encoders = joblib.load(encoders_path)
            return
        
        # Train new model
        target_col = self.get_target_column(df)
        if target_col is None:
            raise ValueError("Could not identify target column for fraud detection")
        
        X = self.prepare_features(df)
        y = df[target_col]
        
        print(f"Training with {len(X)} samples, {X.shape[1]} features")
        print(f"Fraud rate: {y.mean():.4f}")
        
        # Store feature columns
        self.feature_columns = X.columns.tolist()
        
        # Split and train
        if len(X) > 1000:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        else:
            X_train, X_test, y_train, y_test = X, X, y, y
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Train model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate if we have test data
        if len(X) > 1000:
            X_test_scaled = self.scaler.transform(X_test)
            y_pred = self.model.predict(X_test_scaled)
            print("\n🎯 Model Performance:")
            print(classification_report(y_test, y_pred))
        
        # Save model
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        joblib.dump(self.encoders, encoders_path)
        print(f"💾 Model saved as {model_path}")
    
    def predict(self, df):
        """Predict fraud for new data"""
        print(f"🔍 Making predictions using {self.dataset_type} model...")
        
        X = self.prepare_features(df)
        
        # Ensure same features as training
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0
        X = X[self.feature_columns]
        
        # Scale and predict
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        
        return predictions, probabilities
    
    def analyze_dataset(self, file_path_or_df, save_results=True):
        """Universal analysis function for any dataset"""
        print(f"🌟 Universal Fraud Detection Analysis")
        print("=" * 50)
        
        # Load data
        if isinstance(file_path_or_df, str):
            print(f"📁 Loading file: {file_path_or_df}")
            df = pd.read_csv(file_path_or_df)
        else:
            df = file_path_or_df.copy()
            
        print(f"📊 Dataset size: {len(df)} rows, {len(df.columns)} columns")
        
        # Detect dataset type
        self.dataset_type = self.detect_dataset_type(df)
        print(f"🎯 Detected format: {self.dataset_type}")
        
        # Train or load model
        self.train_or_load_model(df)
        
        # Make predictions
        predictions, probabilities = self.predict(df)
        
        # Add results
        df['fraud_prediction'] = predictions
        df['fraud_probability'] = probabilities
        
        # Analysis
        fraud_count = predictions.sum()
        fraud_rate = fraud_count / len(df) * 100
        
        # Find amount column
        amount_cols = [col for col in df.columns if any(word in col.lower() for word in ['amount', 'amt', 'value'])]
        amount_col = amount_cols[0] if amount_cols else None
        
        total_fraud_amount = 0
        if amount_col:
            total_fraud_amount = df[predictions == 1][amount_col].sum()
        
        high_risk_count = (probabilities > 0.7).sum()
        
        print(f"\n🚨 FRAUD DETECTION RESULTS:")
        print(f"📈 Total transactions: {len(df):,}")
        print(f"⚠️  Fraud cases detected: {fraud_count:,}")
        print(f"📊 Fraud rate: {fraud_rate:.2f}%")
        if amount_col:
            print(f"💰 Total fraud amount: ${total_fraud_amount:,.2f}")
        print(f"🔴 High-risk transactions (>70%): {high_risk_count:,}")
        
        # Show top fraud cases
        if fraud_count > 0:
            print(f"\n🔍 Top {min(10, fraud_count)} Fraud Cases:")
            fraud_cases = df[predictions == 1].nlargest(10, 'fraud_probability')
            for idx, row in fraud_cases.iterrows():
                amount_str = f"${row[amount_col]:.2f}" if amount_col else "N/A"
                print(f"  • Row {idx}: {amount_str} (Probability: {row['fraud_probability']:.3f})")
        
        # Save results
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"fraud_analysis_{self.dataset_type}_{timestamp}.csv"
            df.to_csv(output_file, index=False)
            print(f"\n💾 Results saved to: {output_file}")
        
        return df

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Universal Fraud Detection System')
    parser.add_argument('--file', help='CSV file to analyze', required=True)
    parser.add_argument('--no-save', action='store_true', help='Do not save results')
    
    args = parser.parse_args()
    
    detector = UniversalFraudDetector()
    results = detector.analyze_dataset(args.file, save_results=not args.no_save)
    
    print(f"\n✅ Analysis complete! Dataset type: {detector.dataset_type}")

if __name__ == "__main__":
    main()
