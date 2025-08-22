import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import os

def load_and_prepare_data():
    """Load the credit card fraud dataset"""
    print("Loading credit card fraud dataset...")
    
    # Load dataset
    data_path = os.path.join('..', 'data', 'raw', 'creditcard.csv')
    df = pd.read_csv(data_path)
    
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"Fraud percentage: {df['Class'].mean() * 100:.2f}%")
    
    return df

def train_fraud_model(df):
    """Train a fraud detection model"""
    print("\nTraining fraud detection models...")
    
    # Prepare features and target
    X = df.drop(['Class'], axis=1)
    y = df['Class']
    
    print(f"Features shape: {X.shape}")
    print(f"Target distribution: {y.value_counts()}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Isolation Forest (Unsupervised)
    print("\nTraining Isolation Forest...")
    isolation_forest = IsolationForest(
        contamination=0.001,  # Adjust based on fraud rate
        random_state=42,
        n_estimators=100
    )
    
    # Train on normal transactions only
    normal_transactions = X_train_scaled[y_train == 0]
    isolation_forest.fit(normal_transactions)
    
    # Train Random Forest (Supervised)
    print("Training Random Forest...")
    random_forest = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )
    random_forest.fit(X_train_scaled, y_train)
    
    # Evaluate models
    print("\nEvaluating models...")
    
    # Isolation Forest evaluation
    iso_pred = isolation_forest.predict(X_test_scaled)
    iso_pred_binary = (iso_pred == -1).astype(int)  # Convert to 0/1
    
    print("Isolation Forest Results:")
    print(classification_report(y_test, iso_pred_binary))
    
    # Random Forest evaluation
    rf_pred = random_forest.predict(X_test_scaled)
    rf_prob = random_forest.predict_proba(X_test_scaled)[:, 1]
    
    print("Random Forest Results:")
    print(classification_report(y_test, rf_pred))
    print(f"AUC Score: {roc_auc_score(y_test, rf_prob):.4f}")
    
    # Save models
    models_dir = os.path.join('..', 'data', 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Save the best performing model (Random Forest) and scaler
    model_data = {
        'model': random_forest,
        'scaler': scaler,
        'feature_columns': X.columns.tolist(),
        'model_type': 'random_forest'
    }
    
    model_path = os.path.join(models_dir, 'fraud_model.pkl')
    
    # Use pickle instead of joblib for better compatibility
    try:
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        # Verify the saved model
        with open(model_path, 'rb') as f:
            loaded_data = pickle.load(f)
            print("✅ Model verification: Successfully saved and loaded")
        
        print(f"\nModel saved to: {model_path}")
        
    except Exception as e:
        print(f"❌ Error saving model: {e}")
        return None, None, None
    
    return random_forest, scaler, X.columns.tolist()

def test_prediction(model, scaler, feature_columns):
    """Test the trained model with sample data"""
    print("\nTesting prediction...")
    
    # Create sample transaction
    sample_data = np.zeros(len(feature_columns))
    sample_data[0] = 100.0  # Amount
    
    # Reshape and scale
    sample_scaled = scaler.transform([sample_data])
    
    # Predict
    prediction = model.predict(sample_scaled)[0]
    probability = model.predict_proba(sample_scaled)[0][1]
    
    print(f"Sample prediction: {'Fraud' if prediction else 'Normal'}")
    print(f"Fraud probability: {probability:.4f}")

if __name__ == "__main__":
    try:
        # Load data
        df = load_and_prepare_data()
        
        # Train model
        model, scaler, features = train_fraud_model(df)
        
        # Test prediction
        test_prediction(model, scaler, features)
        
        print("\n✅ ML model training completed successfully!")
        print("The trained model is ready for use in the fraud detection API.")
        
    except Exception as e:
        print(f"❌ Error during training: {e}")
        import traceback
        traceback.print_exc()
