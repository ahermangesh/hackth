#!/usr/bin/env python3
"""
Real Fraud Test Detector
Specifically designed to work with the fraudTest.csv format
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class RealFraudDetector:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.encoders = {}
        self.feature_columns = []
        
    def prepare_features(self, df):
        """Prepare features specifically for fraudTest.csv format"""
        df = df.copy()
        
        # Convert trans_date_trans_time to datetime features
        df['trans_date_trans_time'] = pd.to_datetime(df['trans_date_trans_time'])
        df['hour'] = df['trans_date_trans_time'].dt.hour
        df['day_of_week'] = df['trans_date_trans_time'].dt.dayofweek
        df['month'] = df['trans_date_trans_time'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Time-based features
        df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
        df['is_business_hours'] = ((df['hour'] >= 9) & (df['hour'] <= 17)).astype(int)
        
        # Amount-based features
        df['amt_log'] = np.log1p(df['amt'])
        df['is_high_amount'] = (df['amt'] > df['amt'].quantile(0.95)).astype(int)
        
        # Location features
        df['lat_long_dist'] = np.sqrt((df['lat'] - df['merch_lat'])**2 + 
                                    (df['long'] - df['merch_long'])**2)
        
        # Age calculation
        df['dob'] = pd.to_datetime(df['dob'])
        df['age'] = (df['trans_date_trans_time'] - df['dob']).dt.days / 365.25
        
        # Categorical encoding
        categorical_features = ['merchant', 'category', 'gender', 'job', 'state']
        
        for col in categorical_features:
            if col not in self.encoders:
                self.encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.encoders[col].fit_transform(df[col].astype(str))
            else:
                # Handle unseen categories
                df[f'{col}_temp'] = df[col].astype(str)
                mask = df[f'{col}_temp'].isin(self.encoders[col].classes_)
                df[f'{col}_encoded'] = 0  # Default for unseen categories
                df.loc[mask, f'{col}_encoded'] = self.encoders[col].transform(df.loc[mask, f'{col}_temp'])
                df.drop(f'{col}_temp', axis=1, inplace=True)
        
        # Select numerical features
        feature_cols = [
            'amt', 'amt_log', 'lat', 'long', 'city_pop', 'merch_lat', 'merch_long',
            'hour', 'day_of_week', 'month', 'is_weekend', 'is_night', 'is_business_hours',
            'is_high_amount', 'lat_long_dist', 'age'
        ] + [f'{col}_encoded' for col in categorical_features]
        
        return df[feature_cols]
    
    def train(self, df):
        """Train the model on the fraudTest.csv format"""
        print("🚀 Training Real Fraud Detector...")
        
        # Prepare features
        X = self.prepare_features(df)
        y = df['is_fraud']
        
        # Store feature columns for consistency
        self.feature_columns = X.columns.tolist()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        
        print("\n📊 Training Results:")
        print(f"Training samples: {len(X_train)}")
        print(f"Test samples: {len(X_test)}")
        print(f"Fraud rate in training: {y_train.mean():.4f}")
        print(f"Fraud rate in test: {y_test.mean():.4f}")
        
        print("\n🎯 Model Performance:")
        print(classification_report(y_test, y_pred))
        
        return self
    
    def predict(self, df):
        """Predict fraud for new data"""
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
    
    def analyze_file(self, file_path):
        """Analyze a CSV file for fraud"""
        print(f"🔍 Analyzing file: {file_path}")
        
        # Load data
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} transactions")
        
        # Get predictions
        predictions, probabilities = self.predict(df)
        
        # Add results to dataframe
        df['fraud_prediction'] = predictions
        df['fraud_probability'] = probabilities
        
        # Analysis
        fraud_count = predictions.sum()
        total_fraud_amount = df[predictions == 1]['amt'].sum()
        high_risk_transactions = (probabilities > 0.7).sum()
        
        print(f"\n🚨 Fraud Detection Results:")
        print(f"Total transactions: {len(df)}")
        print(f"Predicted fraud cases: {fraud_count}")
        print(f"Fraud rate: {fraud_count/len(df)*100:.2f}%")
        print(f"Total fraud amount: ${total_fraud_amount:,.2f}")
        print(f"High-risk transactions (>70% probability): {high_risk_transactions}")
        
        # Show fraud cases
        if fraud_count > 0:
            print(f"\n🔍 Top {min(10, fraud_count)} Fraud Cases:")
            fraud_cases = df[predictions == 1].nlargest(10, 'fraud_probability')
            for idx, row in fraud_cases.iterrows():
                print(f"  • Transaction {idx}: ${row['amt']:.2f} at {row['merchant']} "
                      f"(Probability: {row['fraud_probability']:.3f})")
        
        return df

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Real Fraud Detection for fraudTest.csv format')
    parser.add_argument('--train', help='Training data file (fraudTest.csv)')
    parser.add_argument('--test', help='Test data file to analyze')
    parser.add_argument('--full-analysis', help='Use same file for training and testing')
    
    args = parser.parse_args()
    
    detector = RealFraudDetector()
    
    if args.full_analysis:
        # Train and test on the same file (split internally)
        print("🎯 Full Analysis Mode: Training and Testing on same dataset")
        df_full = pd.read_csv(args.full_analysis)
        
        # Train on portion of data
        train_size = int(0.8 * len(df_full))
        df_train = df_full.iloc[:train_size]
        df_test = df_full.iloc[train_size:]
        
        detector.train(df_train)
        detector.analyze_file(args.full_analysis)
        
    elif args.train and args.test:
        # Train on one file, test on another
        df_train = pd.read_csv(args.train)
        detector.train(df_train)
        detector.analyze_file(args.test)
        
    else:
        # Default: analyze the provided fraudTest.csv
        test_file = "ProvidedData/6/fraudTest.csv"
        print(f"🎯 Default Mode: Analyzing {test_file}")
        
        # Load and split for training
        df_full = pd.read_csv(test_file)
        train_size = int(0.8 * len(df_full))
        df_train = df_full.iloc[:train_size]
        
        # Train the model
        detector.train(df_train)
        
        # Analyze the full file
        results = detector.analyze_file(test_file)
        
        # Save results
        output_file = "fraud_detection_results.csv"
        results.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")

if __name__ == "__main__":
    main()
