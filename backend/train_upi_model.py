#!/usr/bin/env python3
"""
UPI Fraud Detection Model Training
Uses real Indian UPI transaction data for better fraud detection
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import os

def load_upi_data():
    """Load the UPI transaction dataset"""
    print("🇮🇳 Loading UPI Transaction Dataset...")
    
    data_path = os.path.join('..', 'ProvidedData', 'UPI', 'upi_transactions_2024.csv')
    
    if not os.path.exists(data_path):
        print(f"❌ UPI dataset not found at {data_path}")
        return None
    
    df = pd.read_csv(data_path)
    
    print(f"📊 Dataset shape: {df.shape}")
    print(f"📈 Fraud percentage: {df['fraud_flag'].mean() * 100:.2f}%")
    print(f"📋 Columns: {df.columns.tolist()}")
    
    return df

def preprocess_upi_data(df):
    """Preprocess UPI data for machine learning"""
    print("\n🔧 Preprocessing UPI Data...")
    
    # Create a copy
    df_processed = df.copy()
    
    # Convert timestamp to useful features
    df_processed['timestamp'] = pd.to_datetime(df_processed['timestamp'])
    df_processed['hour'] = df_processed['timestamp'].dt.hour
    df_processed['day_of_month'] = df_processed['timestamp'].dt.day
    df_processed['month'] = df_processed['timestamp'].dt.month
    
    # Encode categorical variables
    label_encoders = {}
    categorical_columns = [
        'transaction type', 'merchant_category', 'transaction_status',
        'sender_age_group', 'receiver_age_group', 'sender_state',
        'sender_bank', 'receiver_bank', 'device_type', 'network_type',
        'day_of_week'
    ]
    
    for col in categorical_columns:
        if col in df_processed.columns:
            le = LabelEncoder()
            df_processed[f'{col}_encoded'] = le.fit_transform(df_processed[col].astype(str))
            label_encoders[col] = le
    
    # Feature engineering
    df_processed['amount_log'] = np.log1p(df_processed['amount (INR)'])
    df_processed['is_high_amount'] = (df_processed['amount (INR)'] > df_processed['amount (INR)'].quantile(0.95)).astype(int)
    df_processed['is_night_transaction'] = ((df_processed['hour'] >= 23) | (df_processed['hour'] <= 5)).astype(int)
    
    # Bank risk features
    bank_fraud_rates = df_processed.groupby('sender_bank')['fraud_flag'].mean()
    df_processed['sender_bank_risk'] = df_processed['sender_bank'].map(bank_fraud_rates)
    
    # State risk features
    state_fraud_rates = df_processed.groupby('sender_state')['fraud_flag'].mean()
    df_processed['sender_state_risk'] = df_processed['sender_state'].map(state_fraud_rates)
    
    print(f"✅ Preprocessing completed. New shape: {df_processed.shape}")
    
    return df_processed, label_encoders

def train_upi_fraud_model(df, label_encoders):
    """Train fraud detection model on UPI data"""
    print("\n🤖 Training UPI Fraud Detection Model...")
    
    # Select features for training
    feature_columns = [
        'amount (INR)', 'amount_log', 'hour_of_day', 'is_weekend',
        'is_high_amount', 'is_night_transaction', 'hour', 'day_of_month', 'month',
        'sender_bank_risk', 'sender_state_risk'
    ] + [f'{col}_encoded' for col in [
        'transaction type', 'merchant_category', 'sender_age_group',
        'receiver_age_group', 'device_type', 'network_type', 'day_of_week'
    ] if f'{col}_encoded' in df.columns]
    
    # Remove any columns that don't exist
    feature_columns = [col for col in feature_columns if col in df.columns]
    
    print(f"📋 Using {len(feature_columns)} features:")
    for i, col in enumerate(feature_columns, 1):
        print(f"   {i:2d}. {col}")
    
    # Prepare features and target
    X = df[feature_columns].fillna(0)
    y = df['fraud_flag']
    
    print(f"\n📊 Data split:")
    print(f"   Features shape: {X.shape}")
    print(f"   Target distribution: Normal={sum(y==0)}, Fraud={sum(y==1)}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest
    print("\n🌳 Training Random Forest Classifier...")
    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight='balanced',
        n_jobs=-1
    )
    
    rf_model.fit(X_train_scaled, y_train)
    
    # Evaluate model
    print("\n📈 Model Evaluation:")
    
    # Training predictions
    train_pred = rf_model.predict(X_train_scaled)
    train_prob = rf_model.predict_proba(X_train_scaled)[:, 1]
    
    # Test predictions
    test_pred = rf_model.predict(X_test_scaled)
    test_prob = rf_model.predict_proba(X_test_scaled)[:, 1]
    
    # Calculate metrics
    train_auc = roc_auc_score(y_train, train_prob)
    test_auc = roc_auc_score(y_test, test_prob)
    
    print(f"🎯 Training AUC: {train_auc:.4f}")
    print(f"🎯 Test AUC: {test_auc:.4f}")
    
    print(f"\n📋 Test Set Classification Report:")
    print(classification_report(y_test, test_pred))
    
    print(f"\n🧮 Confusion Matrix:")
    cm = confusion_matrix(y_test, test_pred)
    print(cm)
    
    # Feature importance
    print(f"\n⭐ Top 10 Most Important Features:")
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for i, (_, row) in enumerate(feature_importance.head(10).iterrows(), 1):
        print(f"   {i:2d}. {row['feature']}: {row['importance']:.4f}")
    
    # Save the UPI model
    models_dir = os.path.join('..', 'data', 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    model_data = {
        'model': rf_model,
        'scaler': scaler,
        'feature_columns': feature_columns,
        'label_encoders': label_encoders,
        'model_type': 'upi_random_forest',
        'test_auc': test_auc,
        'feature_importance': feature_importance.to_dict('records')
    }
    
    model_path = os.path.join(models_dir, 'upi_fraud_model.pkl')
    
    try:
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        print(f"\n✅ UPI Model saved to: {model_path}")
        print(f"📊 Model Performance: {test_auc:.2%} AUC")
        
    except Exception as e:
        print(f"❌ Error saving model: {e}")
        return None, None, None, None
    
    return rf_model, scaler, feature_columns, label_encoders

def test_upi_predictions(model, scaler, feature_columns, label_encoders):
    """Test the UPI model with sample data"""
    print("\n🧪 Testing UPI Model Predictions...")
    
    # Sample UPI transactions to test
    test_cases = [
        {
            'description': 'Normal UPI payment',
            'amount': 500,
            'hour': 14,
            'is_weekend': 0,
            'merchant_category': 'Grocery',
            'transaction_type': 'P2M',
            'device_type': 'Android'
        },
        {
            'description': 'Suspicious large transfer',
            'amount': 99999,
            'hour': 2,
            'is_weekend': 1,
            'merchant_category': 'Other',
            'transaction_type': 'P2P',
            'device_type': 'Android'
        },
        {
            'description': 'Small coffee payment',
            'amount': 150,
            'hour': 10,
            'is_weekend': 0,
            'merchant_category': 'Food',
            'transaction_type': 'P2M',
            'device_type': 'iOS'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {case['description']}")
        print(f"   Amount: ₹{case['amount']}")
        print(f"   Time: {case['hour']}:00")
        print(f"   Category: {case['merchant_category']}")
        
        # Create feature vector (simplified for demo)
        # In real implementation, you'd need to encode all categorical variables properly
        sample_features = np.zeros(len(feature_columns))
        
        # Fill in known features
        if 'amount (INR)' in feature_columns:
            idx = feature_columns.index('amount (INR)')
            sample_features[idx] = case['amount']
        
        if 'hour_of_day' in feature_columns:
            idx = feature_columns.index('hour_of_day')
            sample_features[idx] = case['hour']
        
        if 'is_weekend' in feature_columns:
            idx = feature_columns.index('is_weekend')
            sample_features[idx] = case['is_weekend']
        
        # Scale and predict
        sample_scaled = scaler.transform([sample_features])
        fraud_prob = model.predict_proba(sample_scaled)[0][1]
        is_fraud = model.predict(sample_scaled)[0]
        
        risk_level = 'HIGH' if fraud_prob > 0.7 else 'MEDIUM' if fraud_prob > 0.3 else 'LOW'
        
        print(f"   🎯 Fraud Probability: {fraud_prob:.4f}")
        print(f"   📊 Risk Level: {risk_level}")
        print(f"   🚨 Prediction: {'SUSPICIOUS' if is_fraud else 'LEGITIMATE'}")

if __name__ == "__main__":
    try:
        print("🚀 UPI Fraud Detection Model Training Started")
        print("=" * 60)
        
        # Load UPI data
        df = load_upi_data()
        if df is None:
            exit(1)
        
        # Preprocess data
        df_processed, label_encoders = preprocess_upi_data(df)
        
        # Train model
        model, scaler, features, encoders = train_upi_fraud_model(df_processed, label_encoders)
        
        if model is not None:
            # Test predictions
            test_upi_predictions(model, scaler, features, encoders)
            
            print(f"\n🎉 UPI Fraud Detection Model Training Completed!")
            print(f"💡 The model is now ready for real-time UPI fraud detection")
            print(f"🏦 Banks can use this for live transaction monitoring")
        
    except Exception as e:
        print(f"❌ Error during UPI model training: {e}")
        import traceback
        traceback.print_exc()
