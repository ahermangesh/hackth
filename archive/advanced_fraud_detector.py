#!/usr/bin/env python3
"""
Advanced Multi-Dataset Fraud Detection System
Integrates UPI, Credit Card, and Online Payment datasets for enterprise customers
"""

import pandas as pd
import numpy as np
import os
import pickle
import json
from datetime import datetime
from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler
from sklearn.ensemble import RandomForestClassifier, IsolationForest, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from imblearn.over_sampling import SMOTE
from imblearn.ensemble import BalancedRandomForestClassifier
import warnings
warnings.filterwarnings('ignore')

class AdvancedFraudDetector:
    def __init__(self):
        """Initialize the advanced fraud detection system"""
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_columns = {}
        self.model_performance = {}
        
        # Dataset paths
        self.dataset_paths = {
            'upi': 'ProvidedData/UPI/upi_transactions_2024.csv',
            'creditcard': 'ProvidedData/archive/creditcard.csv', 
            'onlinefraud': 'ProvidedData/archive (4)/onlinefraud.csv'
        }
        
        print("🚀 Advanced Multi-Dataset Fraud Detection System")
        print("=" * 60)
    
    def load_all_datasets(self):
        """Load and analyze all available datasets"""
        datasets = {}
        
        print("📊 Loading datasets...")
        
        # Load UPI Dataset
        if os.path.exists(self.dataset_paths['upi']):
            print("Loading UPI transactions...")
            upi_df = pd.read_csv(self.dataset_paths['upi'])
            datasets['upi'] = upi_df
            fraud_rate = upi_df['fraud_flag'].mean() * 100
            print(f"   ✅ UPI: {len(upi_df):,} transactions, {fraud_rate:.2f}% fraud rate")
        
        # Load Credit Card Dataset
        if os.path.exists(self.dataset_paths['creditcard']):
            print("Loading Credit Card transactions...")
            cc_df = pd.read_csv(self.dataset_paths['creditcard'])
            datasets['creditcard'] = cc_df
            fraud_rate = cc_df['Class'].mean() * 100
            print(f"   ✅ Credit Card: {len(cc_df):,} transactions, {fraud_rate:.2f}% fraud rate")
        
        # Load Online Fraud Dataset (PaySim-like)
        if os.path.exists(self.dataset_paths['onlinefraud']):
            print("Loading Online Payment transactions...")
            online_df = pd.read_csv(self.dataset_paths['onlinefraud'])
            datasets['onlinefraud'] = online_df
            fraud_rate = online_df['isFraud'].mean() * 100
            print(f"   ✅ Online Payments: {len(online_df):,} transactions, {fraud_rate:.2f}% fraud rate")
        
        return datasets
    
    def prepare_upi_features(self, df):
        """Feature engineering for UPI transactions"""
        features = df.copy()
        
        # Encode categorical variables
        categorical_columns = ['transaction type', 'merchant_category', 'transaction_status', 
                             'sender_age_group', 'receiver_age_group', 'sender_state', 
                             'sender_bank', 'receiver_bank', 'device_type', 'network_type']
        
        for col in categorical_columns:
            if col in features.columns:
                le = LabelEncoder()
                features[f'{col}_encoded'] = le.fit_transform(features[col].astype(str))
                if col not in self.encoders:
                    self.encoders[col] = le
        
        # Amount-based features
        if 'amount (INR)' in features.columns:
            features['amount_log'] = np.log1p(features['amount (INR)'])
            features['amount_sqrt'] = np.sqrt(features['amount (INR)'])
            features['amount_bin'] = pd.qcut(features['amount (INR)'], q=10, labels=False, duplicates='drop')
        
        # Time-based features
        if 'timestamp' in features.columns:
            features['timestamp'] = pd.to_datetime(features['timestamp'])
            features['hour'] = features['timestamp'].dt.hour
            features['day_of_week'] = features['timestamp'].dt.dayofweek
            features['month'] = features['timestamp'].dt.month
            
            # Advanced time features
            features['is_night'] = ((features['hour'] >= 22) | (features['hour'] <= 5)).astype(int)
            features['is_business_hours'] = ((features['hour'] >= 9) & (features['hour'] <= 17)).astype(int)
        
        # Cross-state transaction
        if 'sender_state' in features.columns and 'receiver_state' in features.columns:
            features['is_cross_state'] = (features['sender_state'] != features['receiver_state']).astype(int)
        
        # Cross-bank transaction
        if 'sender_bank' in features.columns and 'receiver_bank' in features.columns:
            features['is_cross_bank'] = (features['sender_bank'] != features['receiver_bank']).astype(int)
        
        # Device/Network risk features
        if 'device_type' in features.columns:
            features['is_android'] = (features['device_type'] == 'Android').astype(int)
            features['is_ios'] = (features['device_type'] == 'iOS').astype(int)
        
        if 'network_type' in features.columns:
            features['is_wifi'] = (features['network_type'] == 'WiFi').astype(int)
            features['is_5g'] = (features['network_type'] == '5G').astype(int)
        
        return features
    
    def prepare_creditcard_features(self, df):
        """Feature engineering for credit card transactions"""
        features = df.copy()
        
        # Time-based features
        if 'Time' in features.columns:
            features['hour'] = (features['Time'] / 3600) % 24
            features['day'] = (features['Time'] / 86400) % 7
            features['is_weekend'] = ((features['day'] == 5) | (features['day'] == 6)).astype(int)
        
        # Amount-based features
        if 'Amount' in features.columns:
            features['amount_log'] = np.log1p(features['Amount'])
            features['amount_sqrt'] = np.sqrt(features['Amount'])
            features['amount_normalized'] = (features['Amount'] - features['Amount'].mean()) / features['Amount'].std()
        
        # V-features statistical aggregations
        v_columns = [col for col in features.columns if col.startswith('V')]
        if v_columns:
            features['v_sum'] = features[v_columns].sum(axis=1)
            features['v_mean'] = features[v_columns].mean(axis=1)
            features['v_std'] = features[v_columns].std(axis=1)
            features['v_skew'] = features[v_columns].skew(axis=1)
        
        return features
    
    def prepare_online_features(self, df):
        """Feature engineering for online payment transactions (PaySim-like)"""
        features = df.copy()
        
        # Encode transaction type
        if 'type' in features.columns:
            le = LabelEncoder()
            features['type_encoded'] = le.fit_transform(features['type'])
            self.encoders['payment_type'] = le
        
        # Balance-based features
        if all(col in features.columns for col in ['oldbalanceOrg', 'newbalanceOrig']):
            features['balance_change_orig'] = features['newbalanceOrig'] - features['oldbalanceOrg']
            features['balance_ratio_orig'] = np.where(features['oldbalanceOrg'] > 0, 
                                                    features['newbalanceOrig'] / features['oldbalanceOrg'], 0)
        
        if all(col in features.columns for col in ['oldbalanceDest', 'newbalanceDest']):
            features['balance_change_dest'] = features['newbalanceDest'] - features['oldbalanceDest']
            features['balance_ratio_dest'] = np.where(features['oldbalanceDest'] > 0,
                                                    features['newbalanceDest'] / features['oldbalanceDest'], 0)
        
        # Amount vs balance ratios
        if 'amount' in features.columns and 'oldbalanceOrg' in features.columns:
            features['amount_to_balance_ratio'] = np.where(features['oldbalanceOrg'] > 0,
                                                         features['amount'] / features['oldbalanceOrg'], 0)
        
        # Transaction flow features
        features['is_cash_transaction'] = features['type'].isin(['CASH_OUT', 'CASH_IN']).astype(int) if 'type' in features.columns else 0
        features['is_payment'] = (features['type'] == 'PAYMENT').astype(int) if 'type' in features.columns else 0
        features['is_transfer'] = (features['type'] == 'TRANSFER').astype(int) if 'type' in features.columns else 0
        
        return features
    
    def train_model_for_dataset(self, dataset_name, df, target_column):
        """Train optimized model for specific dataset"""
        print(f"\n🎯 Training model for {dataset_name.upper()} dataset...")
        
        # Prepare features based on dataset type
        if dataset_name == 'upi':
            features_df = self.prepare_upi_features(df)
        elif dataset_name == 'creditcard':
            features_df = self.prepare_creditcard_features(df)
        elif dataset_name == 'onlinefraud':
            features_df = self.prepare_online_features(df)
        
        # Select numeric features for modeling
        numeric_columns = features_df.select_dtypes(include=[np.number]).columns.tolist()
        if target_column in numeric_columns:
            numeric_columns.remove(target_column)
        
        # Remove any ID columns
        id_columns = [col for col in numeric_columns if 'id' in col.lower() or 'step' in col.lower()]
        numeric_columns = [col for col in numeric_columns if col not in id_columns]
        
        X = features_df[numeric_columns]
        y = features_df[target_column]
        
        # Handle missing values
        X = X.fillna(0)
        
        print(f"   Features: {X.shape[1]}, Samples: {X.shape[0]}")
        print(f"   Fraud rate: {y.mean():.4f}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = RobustScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Handle class imbalance with SMOTE
        smote = SMOTE(random_state=42, k_neighbors=min(5, sum(y_train) - 1))
        X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
        
        print(f"   After SMOTE: {X_train_balanced.shape[0]} samples")
        
        # Train ensemble of models
        models = {
            'random_forest': BalancedRandomForestClassifier(
                n_estimators=100, 
                random_state=42,
                max_depth=10,
                min_samples_split=5
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=6,
                learning_rate=0.1
            ),
            'isolation_forest': IsolationForest(
                contamination=float(y.mean()),
                random_state=42,
                n_estimators=100
            )
        }
        
        best_model = None
        best_score = 0
        model_scores = {}
        
        for model_name, model in models.items():
            if model_name == 'isolation_forest':
                # Unsupervised model - train on normal transactions only
                normal_data = X_train_scaled[y_train == 0]
                model.fit(normal_data)
                
                # Evaluate
                y_pred = model.predict(X_test_scaled)
                y_pred_binary = (y_pred == -1).astype(int)
                score = roc_auc_score(y_test, y_pred_binary)
            else:
                # Supervised models
                model.fit(X_train_balanced, y_train_balanced)
                
                # Evaluate
                y_pred = model.predict(X_test_scaled)
                y_prob = model.predict_proba(X_test_scaled)[:, 1]
                score = roc_auc_score(y_test, y_prob)
            
            model_scores[model_name] = score
            print(f"   {model_name}: ROC-AUC = {score:.4f}")
            
            if score > best_score:
                best_score = score
                best_model = model
        
        # Save the best model
        self.models[dataset_name] = best_model
        self.scalers[dataset_name] = scaler
        self.feature_columns[dataset_name] = numeric_columns
        self.model_performance[dataset_name] = model_scores
        
        print(f"   ✅ Best model saved with ROC-AUC: {best_score:.4f}")
        
        return best_model, best_score
    
    def train_all_models(self):
        """Train models for all available datasets"""
        datasets = self.load_all_datasets()
        
        target_mapping = {
            'upi': 'fraud_flag',
            'creditcard': 'Class', 
            'onlinefraud': 'isFraud'
        }
        
        trained_models = {}
        
        for dataset_name, df in datasets.items():
            target_col = target_mapping[dataset_name]
            
            if target_col in df.columns:
                model, score = self.train_model_for_dataset(dataset_name, df, target_col)
                trained_models[dataset_name] = {
                    'model': model,
                    'score': score,
                    'samples': len(df)
                }
        
        return trained_models
    
    def predict_fraud(self, transaction_data, model_type='auto'):
        """Predict fraud for a transaction using appropriate model"""
        
        if model_type == 'auto':
            # Auto-detect transaction type
            if 'transaction type' in transaction_data or 'sender_bank' in transaction_data:
                model_type = 'upi'
            elif any(f'V{i}' in transaction_data for i in range(1, 29)):
                model_type = 'creditcard'
            elif 'type' in transaction_data and 'oldbalanceOrg' in transaction_data:
                model_type = 'onlinefraud'
            else:
                model_type = 'upi'  # Default to UPI
        
        if model_type not in self.models:
            return {
                'error': f'Model for {model_type} not trained',
                'available_models': list(self.models.keys())
            }
        
        try:
            # Prepare features
            df_temp = pd.DataFrame([transaction_data])
            
            if model_type == 'upi':
                features_df = self.prepare_upi_features(df_temp)
            elif model_type == 'creditcard':
                features_df = self.prepare_creditcard_features(df_temp)
            elif model_type == 'onlinefraud':
                features_df = self.prepare_online_features(df_temp)
            
            # Extract numeric features
            feature_cols = self.feature_columns[model_type]
            
            # Ensure all required columns exist
            for col in feature_cols:
                if col not in features_df.columns:
                    features_df[col] = 0
            
            X = features_df[feature_cols].fillna(0)
            
            # Scale features
            X_scaled = self.scalers[model_type].transform(X)
            
            # Make prediction
            model = self.models[model_type]
            
            if hasattr(model, 'predict_proba'):
                fraud_prob = model.predict_proba(X_scaled)[0][1]
                is_fraud = fraud_prob > 0.5
            else:
                # Isolation Forest
                anomaly_score = model.predict(X_scaled)[0]
                is_fraud = anomaly_score == -1
                fraud_prob = 0.8 if is_fraud else 0.2
            
            # Risk level
            if fraud_prob >= 0.7:
                risk_level = 'HIGH'
            elif fraud_prob >= 0.4:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            return {
                'is_fraud': bool(is_fraud),
                'fraud_probability': float(fraud_prob),
                'risk_level': risk_level,
                'model_used': model_type,
                'confidence': float(abs(fraud_prob - 0.5) * 2)  # How confident the model is
            }
            
        except Exception as e:
            return {
                'error': f'Prediction failed: {str(e)}',
                'model_type': model_type
            }
    
    def save_models(self, directory='data/models'):
        """Save all trained models"""
        os.makedirs(directory, exist_ok=True)
        
        model_data = {
            'models': self.models,
            'scalers': self.scalers,
            'encoders': self.encoders,
            'feature_columns': self.feature_columns,
            'model_performance': self.model_performance,
            'trained_at': datetime.now().isoformat()
        }
        
        model_path = os.path.join(directory, 'advanced_fraud_models.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"\n💾 Models saved to: {model_path}")
        return model_path
    
    def load_models(self, model_path='data/models/advanced_fraud_models.pkl'):
        """Load pre-trained models"""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.models = model_data['models']
            self.scalers = model_data['scalers']
            self.encoders = model_data['encoders']
            self.feature_columns = model_data['feature_columns']
            self.model_performance = model_data['model_performance']
            
            print(f"✅ Models loaded from: {model_path}")
            print(f"Available models: {list(self.models.keys())}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load models: {e}")
            return False
    
    def generate_model_report(self):
        """Generate comprehensive model performance report"""
        report = {
            'training_summary': {
                'total_models': len(self.models),
                'available_datasets': list(self.models.keys()),
                'training_date': datetime.now().isoformat()
            },
            'model_performance': self.model_performance,
            'dataset_info': {}
        }
        
        # Add dataset information
        datasets = self.load_all_datasets()
        for name, df in datasets.items():
            if name in self.models:
                target_col = {'upi': 'fraud_flag', 'creditcard': 'Class', 'onlinefraud': 'isFraud'}[name]
                report['dataset_info'][name] = {
                    'total_transactions': len(df),
                    'fraud_rate': float(df[target_col].mean()),
                    'features_used': len(self.feature_columns[name])
                }
        
        return report

def main():
    """Main function to train and test the advanced fraud detector"""
    print("🚀 Initializing Advanced Multi-Dataset Fraud Detector...")
    
    detector = AdvancedFraudDetector()
    
    # Train models on all datasets
    print("\n📈 Training models on all datasets...")
    trained_models = detector.train_all_models()
    
    # Save models
    model_path = detector.save_models()
    
    # Generate performance report
    report = detector.generate_model_report()
    
    print("\n📊 TRAINING SUMMARY")
    print("=" * 50)
    for dataset, info in report['dataset_info'].items():
        print(f"{dataset.upper()}:")
        print(f"   Transactions: {info['total_transactions']:,}")
        print(f"   Fraud Rate: {info['fraud_rate']:.4f}")
        print(f"   Features: {info['features_used']}")
        if dataset in report['model_performance']:
            best_score = max(report['model_performance'][dataset].values())
            print(f"   Best ROC-AUC: {best_score:.4f}")
        print()
    
    # Test predictions
    print("🧪 TESTING PREDICTIONS")
    print("=" * 50)
    
    # Test UPI transaction
    upi_test = {
        'amount (INR)': 50000,
        'transaction type': 'P2P',
        'merchant_category': 'Other',
        'transaction_status': 'SUCCESS',
        'hour_of_day': 23,  # Late night
        'is_weekend': 1,
        'sender_state': 'Delhi',
        'receiver_state': 'Mumbai'  # Cross-state
    }
    
    result = detector.predict_fraud(upi_test, 'upi')
    print("UPI Test Transaction:")
    print(f"   Amount: ₹{upi_test['amount (INR)']} at {upi_test['hour_of_day']}:00")
    print(f"   Prediction: {'🚨 FRAUD' if result.get('is_fraud') else '✅ LEGITIMATE'}")
    print(f"   Risk Level: {result.get('risk_level', 'Unknown')}")
    print(f"   Confidence: {result.get('fraud_probability', 0):.3f}")
    
    print("\n🎉 Advanced fraud detection system ready!")
    print(f"📁 Models saved to: {model_path}")
    
    return detector

if __name__ == "__main__":
    detector = main()
