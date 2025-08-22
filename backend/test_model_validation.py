#!/usr/bin/env python3
"""
Test the trained model with actual test data to validate performance
"""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

def load_model():
    """Load the trained model"""
    try:
        model_path = os.path.join('..', 'data', 'models', 'fraud_model.pkl')
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        return model_data['model'], model_data['scaler'], model_data['feature_columns']
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, None, None

def test_model_on_real_data():
    """Test model performance on actual test set"""
    print("🧪 Testing Model Performance on Real Data...")
    
    # Load model
    model, scaler, feature_columns = load_model()
    if model is None:
        print("❌ Could not load model")
        return
    
    # Load original dataset
    data_path = os.path.join('..', 'data', 'raw', 'creditcard.csv')
    if not os.path.exists(data_path):
        print(f"❌ Dataset not found at {data_path}")
        return
    
    df = pd.read_csv(data_path)
    print(f"📊 Dataset loaded: {df.shape}")
    
    # Prepare data same way as training
    X = df.drop(['Class'], axis=1)
    y = df['Class']
    
    # Use same split as training (test_size=0.2, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale test data
    X_test_scaled = scaler.transform(X_test)
    
    print(f"🔢 Test set size: {X_test.shape}")
    print(f"🚨 Actual fraud in test set: {y_test.sum()} / {len(y_test)} ({y_test.mean()*100:.2f}%)")
    
    # Make predictions
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    
    # Calculate metrics
    auc_score = roc_auc_score(y_test, y_prob)
    
    print(f"\n📈 Model Performance:")
    print(f"AUC Score: {auc_score:.4f}")
    print(f"Fraud predictions: {y_pred.sum()} / {len(y_pred)}")
    
    print(f"\n📋 Classification Report:")
    print(classification_report(y_test, y_pred))
    
    print(f"\n🧮 Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    
    # Test some high fraud probability samples
    print(f"\n🚨 Top 10 Highest Fraud Probabilities:")
    high_fraud_indices = np.argsort(y_prob)[-10:]
    for i, idx in enumerate(high_fraud_indices):
        original_idx = X_test.index[idx]
        actual_label = y_test.iloc[idx]
        fraud_prob = y_prob[idx]
        amount = X_test.iloc[idx]['Amount']
        print(f"{i+1}. Index {original_idx}: Amount={amount:.2f}, Fraud_Prob={fraud_prob:.4f}, Actual={'FRAUD' if actual_label else 'NORMAL'}")
    
    # Test some specific amounts that should trigger fraud
    print(f"\n🧪 Testing Specific Transaction Amounts:")
    test_amounts = [50, 1000, 10000, 100000]
    
    for amount in test_amounts:
        # Create feature vector (amount + zeros for other features)
        features = np.zeros(len(feature_columns))
        
        # Find amount column index
        if 'Amount' in feature_columns:
            amount_idx = feature_columns.index('Amount')
            features[amount_idx] = amount
        else:
            features[0] = amount  # Assume first feature if Amount not found
        
        # Scale and predict
        features_scaled = scaler.transform([features])
        fraud_prob = model.predict_proba(features_scaled)[0][1]
        is_fraud = model.predict(features_scaled)[0]
        
        print(f"Amount ${amount}: Fraud_Prob={fraud_prob:.4f}, Prediction={'FRAUD' if is_fraud else 'NORMAL'}")

if __name__ == "__main__":
    test_model_on_real_data()
