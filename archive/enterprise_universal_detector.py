#!/usr/bin/env python3
"""
Enterprise Universal Fraud Detector with Interactive Column Mapping
Handles ANY dataset format with intelligent column detection and user mapping
"""

import pandas as pd
import numpy as np
import pickle
import os
import json
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import warnings
warnings.filterwarnings('ignore')

class EnterpriseUniversalDetector:
    def __init__(self):
        self.dataset_type = None
        self.column_mappings = {}
        self.scaler = StandardScaler()
        self.model = None
        self.label_encoders = {}
        self.feature_columns = []
        self.mappings_file = 'data/column_mappings.json'
        
        # Load saved column mappings
        self.load_saved_mappings()
        
        # Enhanced column patterns for auto-detection
        self.column_patterns = {
            'amount': ['amount', 'amt', 'value', 'price', 'cost', 'total', 'sum', 'money', 'payment', 'transaction_amount', 'txn_amt'],
            'user_id': ['user', 'customer', 'client', 'account', 'id', 'userid', 'customerid', 'account_id', 'user_id', 'customer_id'],
            'merchant': ['merchant', 'vendor', 'shop', 'store', 'business', 'company', 'seller', 'retailer'],
            'category': ['category', 'type', 'class', 'genre', 'group', 'section', 'department'],
            'timestamp': ['time', 'date', 'timestamp', 'created', 'occurred', 'transaction_time', 'datetime', 'created_at'],
            'location': ['location', 'city', 'state', 'country', 'region', 'place', 'address'],
            'description': ['description', 'desc', 'details', 'memo', 'note', 'reference', 'ref'],
            'status': ['status', 'state', 'result', 'outcome', 'response']
        }
    
    def load_saved_mappings(self):
        """Load previously saved column mappings"""
        try:
            if os.path.exists(self.mappings_file):
                with open(self.mappings_file, 'r') as f:
                    self.saved_mappings = json.load(f)
            else:
                self.saved_mappings = {}
        except:
            self.saved_mappings = {}
    
    def save_column_mapping(self, dataset_signature, mapping):
        """Save column mapping for future use"""
        try:
            os.makedirs(os.path.dirname(self.mappings_file), exist_ok=True)
            self.saved_mappings[dataset_signature] = mapping
            with open(self.mappings_file, 'w') as f:
                json.dump(self.saved_mappings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save mapping: {e}")
    
    def get_dataset_signature(self, df):
        """Create unique signature for dataset based on columns"""
        columns = sorted(df.columns.tolist())
        return "_".join(columns[:10])  # Use first 10 columns for signature
    
    def analyze_dataset_structure(self, df):
        """Analyze dataset and return structure information"""
        analysis = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': df.columns.tolist(),
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'text_columns': df.select_dtypes(include=['object']).columns.tolist(),
            'missing_data': df.isnull().sum().to_dict(),
            'data_types': df.dtypes.astype(str).to_dict(),
            'sample_data': df.head(3).to_dict('records')
        }
        
        # Auto-detect potential column mappings
        auto_mappings = self.auto_detect_columns(df)
        analysis['suggested_mappings'] = auto_mappings
        
        return analysis
    
    def auto_detect_columns(self, df):
        """Automatically detect column purposes based on patterns"""
        mappings = {}
        columns_lower = [col.lower() for col in df.columns]
        
        for purpose, patterns in self.column_patterns.items():
            best_match = None
            best_score = 0
            
            for i, col_lower in enumerate(columns_lower):
                score = 0
                for pattern in patterns:
                    if pattern in col_lower:
                        score += len(pattern) / len(col_lower)  # Longer matches get higher scores
                
                if score > best_score:
                    best_score = score
                    best_match = df.columns[i]
            
            if best_match and best_score > 0.3:  # Confidence threshold
                mappings[purpose] = best_match
        
        return mappings
    
    def needs_column_mapping(self, df):
        """Check if dataset needs interactive column mapping"""
        signature = self.get_dataset_signature(df)
        print(f"Dataset signature: {signature}")
        
        # Check if we have saved mapping
        if signature in self.saved_mappings:
            print(f"Found saved mapping for signature: {signature}")
            self.column_mappings = self.saved_mappings[signature]
            return False
        
        # Check if it's a known format
        is_known = self.detect_known_format(df)
        print(f"Known format detected: {is_known}, type: {self.dataset_type if is_known else 'None'}")
        if is_known:
            return False
        
        # For any unknown format, always show mapping interface
        print("Unknown format - triggering mapping interface")
        return True
    
    def detect_known_format(self, df):
        """Detect if dataset matches known formats"""
        columns = set(df.columns)
        
        # UPI format detection - require exact column names
        upi_indicators = {'amount (INR)', 'transaction_type', 'payer_vpa'}
        if len(upi_indicators.intersection(columns)) >= 2:
            self.dataset_type = 'upi_transactions'
            return True
        
        # Credit card detailed format - require exact column names
        cc_detailed_indicators = {'amt', 'merchant', 'category', 'city'}
        if len(cc_detailed_indicators.intersection(columns)) >= 3:
            self.dataset_type = 'credit_card_detailed'
            return True
        
        # Credit card PCA format - require many V columns and Amount
        v_columns = [col for col in df.columns if col.startswith('V') and col[1:].isdigit()]
        if len(v_columns) > 15 and 'Amount' in columns and 'Time' in columns:
            self.dataset_type = 'credit_card_pca'
            return True
        
        # FraudTest format - require exact columns
        fraudtest_indicators = {'amt', 'zip', 'lat', 'long', 'city_pop', 'unix_time', 'merch_lat', 'merch_long'}
        if len(fraudtest_indicators.intersection(columns)) >= 6:
            self.dataset_type = 'fraudtest'
            return True
        
        return False
    
    def apply_column_mapping(self, df, mappings):
        """Apply user-provided column mappings to dataset"""
        self.column_mappings = mappings
        
        # Save mapping for future use
        signature = self.get_dataset_signature(df)
        self.save_column_mapping(signature, mappings)
        
        # Set dataset type as custom
        self.dataset_type = 'custom_mapped'
        
        return True
    
    def engineer_features_custom(self, df):
        """Engineer features for custom mapped dataset"""
        features = pd.DataFrame()
        
        # Amount-based features
        if 'amount' in self.column_mappings:
            amount_col = self.column_mappings['amount']
            if amount_col in df.columns:
                features['amount'] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
                features['amount_log'] = np.log1p(features['amount'])
                features['amount_zscore'] = np.abs((features['amount'] - features['amount'].mean()) / features['amount'].std())
                features['is_round_amount'] = (features['amount'] % 100 == 0).astype(int)
                features['amount_category'] = pd.cut(features['amount'], bins=5, labels=False)
        
        # User ID features
        if 'user_id' in self.column_mappings:
            user_col = self.column_mappings['user_id']
            if user_col in df.columns:
                user_counts = df[user_col].value_counts()
                features['user_frequency'] = df[user_col].map(user_counts)
                features['is_frequent_user'] = (features['user_frequency'] > features['user_frequency'].quantile(0.8)).astype(int)
        
        # Merchant features
        if 'merchant' in self.column_mappings:
            merchant_col = self.column_mappings['merchant']
            if merchant_col in df.columns:
                merchant_counts = df[merchant_col].value_counts()
                features['merchant_frequency'] = df[merchant_col].map(merchant_counts)
                features['is_rare_merchant'] = (features['merchant_frequency'] < features['merchant_frequency'].quantile(0.2)).astype(int)
        
        # Category features
        if 'category' in self.column_mappings:
            category_col = self.column_mappings['category']
            if category_col in df.columns:
                if category_col not in self.label_encoders:
                    self.label_encoders[category_col] = LabelEncoder()
                    features['category_encoded'] = self.label_encoders[category_col].fit_transform(df[category_col].astype(str))
                else:
                    try:
                        features['category_encoded'] = self.label_encoders[category_col].transform(df[category_col].astype(str))
                    except:
                        features['category_encoded'] = 0
        
        # Time-based features
        if 'timestamp' in self.column_mappings:
            time_col = self.column_mappings['timestamp']
            if time_col in df.columns:
                try:
                    timestamps = pd.to_datetime(df[time_col], errors='coerce')
                    features['hour'] = timestamps.dt.hour
                    features['day_of_week'] = timestamps.dt.dayofweek
                    features['is_weekend'] = (timestamps.dt.dayofweek >= 5).astype(int)
                    features['is_night'] = ((timestamps.dt.hour < 6) | (timestamps.dt.hour > 22)).astype(int)
                except:
                    pass
        
        # Add statistical features for any remaining numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
            if col not in [self.column_mappings.get('amount', '')]:
                col_data = pd.to_numeric(df[col], errors='coerce').fillna(0)
                features[f'{col}_normalized'] = (col_data - col_data.mean()) / (col_data.std() + 1e-8)
                features[f'{col}_outlier'] = (np.abs(features[f'{col}_normalized']) > 2).astype(int)
        
        # Fill any remaining NaN values
        features = features.fillna(0)
        
        return features
    
    def train_custom_model(self, features, has_labels=False, label_column=None):
        """Train fraud detection model for custom dataset"""
        if has_labels and label_column is not None:
            # Supervised learning with labels
            y = label_column
            X_train, X_test, y_train, y_test = train_test_split(features, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train Random Forest
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            print("Model Performance:")
            print(classification_report(y_test, y_pred))
            
        else:
            # Unsupervised learning - anomaly detection
            features_scaled = self.scaler.fit_transform(features)
            
            # Train Isolation Forest for anomaly detection
            self.model = IsolationForest(contamination=0.1, random_state=42)
            self.model.fit(features_scaled)
            
            print("Trained unsupervised anomaly detection model")
        
        self.feature_columns = features.columns.tolist()
    
    def predict_fraud(self, df):
        """Predict fraud for new dataset"""
        if self.dataset_type == 'custom_mapped':
            features = self.engineer_features_custom(df)
        elif self.dataset_type == 'generic_statistical':
            features = self.engineer_features_generic(df)
        else:
            # Use existing feature engineering for known formats
            if self.dataset_type == 'upi_transactions':
                features = self.engineer_features_upi(df)
            elif self.dataset_type == 'credit_card_detailed':
                features = self.engineer_features_credit_detailed(df)
            elif self.dataset_type == 'credit_card_pca':
                features = self.engineer_features_credit_pca(df)
            else:
                features = self.engineer_features_generic(df)
        
        # Ensure feature consistency
        for col in self.feature_columns:
            if col not in features.columns:
                features[col] = 0
        
        features = features[self.feature_columns].fillna(0)
        features_scaled = self.scaler.transform(features)
        
        # Make predictions
        if hasattr(self.model, 'predict_proba'):
            fraud_probs = self.model.predict_proba(features_scaled)[:, 1]
        elif hasattr(self.model, 'decision_function'):
            # For Isolation Forest, convert decision function to probability-like scores
            decision_scores = self.model.decision_function(features_scaled)
            fraud_probs = 1 / (1 + np.exp(decision_scores))  # Sigmoid transformation
        else:
            fraud_probs = self.model.predict(features_scaled)
        
        predictions = (fraud_probs > 0.5).astype(int)
        
        # Create results dataframe
        results_df = df.copy()
        results_df['fraud_probability'] = fraud_probs
        results_df['fraud_prediction'] = predictions
        
        return results_df
    
    def analyze_dataset(self, file_path, column_mappings=None, has_fraud_labels=False, fraud_label_column=None):
        """Main analysis function"""
        try:
            # Load dataset
            df = pd.read_csv(file_path)
            print(f"Loaded dataset: {len(df)} rows, {len(df.columns)} columns")
            
            # Check if custom mapping is provided
            if column_mappings is not None:
                if len(column_mappings) > 0:
                    # Use provided mappings
                    self.apply_column_mapping(df, column_mappings)
                else:
                    # Empty mappings mean use generic approach
                    self.dataset_type = 'generic_statistical'
            elif self.needs_column_mapping(df):
                # Return dataset structure for interactive mapping
                return {
                    'status': 'needs_mapping',
                    'structure': self.analyze_dataset_structure(df),
                    'message': 'Custom dataset detected. Please provide column mappings.'
                }
            
            # Engineer features based on dataset type
            if self.dataset_type == 'custom_mapped':
                features = self.engineer_features_custom(df)
            elif self.dataset_type == 'generic_statistical':
                features = self.engineer_features_generic(df)
            else:
                # Use existing methods for known formats
                features = self.engineer_features_generic(df)
            
            # Train model if we don't have one
            if self.model is None:
                fraud_labels = None
                if has_fraud_labels and fraud_label_column:
                    fraud_labels = df[fraud_label_column]
                
                self.train_custom_model(features, has_fraud_labels, fraud_labels)
            
            # Make predictions
            results_df = self.predict_fraud(df)
            
            return {
                'status': 'success',
                'results': results_df,
                'dataset_type': self.dataset_type,
                'total_transactions': len(results_df),
                'fraud_detected': int(results_df['fraud_prediction'].sum()),
                'fraud_rate': float(results_df['fraud_prediction'].mean() * 100)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Analysis failed: {str(e)}"
            }
    
    def engineer_features_generic(self, df):
        """Generic feature engineering for unknown formats"""
        features = pd.DataFrame()
        
        # Statistical features for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            col_data = pd.to_numeric(df[col], errors='coerce').fillna(0)
            features[f'{col}_value'] = col_data
            features[f'{col}_zscore'] = np.abs((col_data - col_data.mean()) / (col_data.std() + 1e-8))
            features[f'{col}_outlier'] = (features[f'{col}_zscore'] > 2).astype(int)
        
        # Categorical features encoding
        text_cols = df.select_dtypes(include=['object']).columns
        for col in text_cols[:3]:  # Limit to first 3 text columns
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                features[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col].astype(str))
            else:
                try:
                    features[f'{col}_encoded'] = self.label_encoders[col].transform(df[col].astype(str))
                except:
                    features[f'{col}_encoded'] = 0
        
        return features.fillna(0)
