import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import joblib
import os
from datetime import datetime, timedelta

class FraudDetectionModel:
    def __init__(self, model_type='isolation_forest'):
        self.model_type = model_type
        self.model = None
        self.scaler = RobustScaler()
        self.feature_columns = []
        self.is_trained = False
        
        # Initialize model based on type
        if model_type == 'isolation_forest':
            self.model = IsolationForest(
                contamination=0.1, 
                random_state=42,
                n_estimators=100
            )
        elif model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
    
    def prepare_features(self, df):
        """Prepare features for model training/prediction"""
        features = df.copy()
        
        # Basic amount features
        if 'Amount' in features.columns:
            features['amount_log'] = np.log1p(features['Amount'])
            features['amount_sqrt'] = np.sqrt(features['Amount'])
        
        # Time-based features
        if 'Time' in features.columns:
            features['hour'] = (features['Time'] / 3600) % 24
            features['day_of_week'] = ((features['Time'] / 86400) % 7).astype(int)
        
        # Handle V1-V28 features (common in credit card datasets)
        v_columns = [col for col in features.columns if col.startswith('V')]
        if v_columns:
            # Create interaction features for top V columns
            if len(v_columns) >= 4:
                features['V1_V4_interaction'] = features['V1'] * features['V4']
                features['V2_V5_interaction'] = features['V2'] * features['V5']
        
        # Select relevant columns for training
        exclude_cols = ['Class'] if 'Class' in features.columns else []
        feature_cols = [col for col in features.columns if col not in exclude_cols]
        
        return features[feature_cols]
    
    def train(self, df, target_column='Class'):
        """Train the fraud detection model"""
        try:
            print(f"Training {self.model_type} model...")
            
            # Prepare features
            X = self.prepare_features(df)
            self.feature_columns = X.columns.tolist()
            
            # Handle missing values
            X = X.fillna(X.median())
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            if self.model_type == 'isolation_forest':
                # For unsupervised learning, use only normal transactions
                normal_data = X_scaled[df[target_column] == 0] if target_column in df.columns else X_scaled
                self.model.fit(normal_data)
            else:
                # For supervised learning
                y = df[target_column]
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.2, random_state=42, stratify=y
                )
                
                self.model.fit(X_train, y_train)
                
                # Evaluate model
                y_pred = self.model.predict(X_test)
                print("Model Performance:")
                print(classification_report(y_test, y_pred))
                
                if hasattr(self.model, 'predict_proba'):
                    y_prob = self.model.predict_proba(X_test)[:, 1]
                    auc_score = roc_auc_score(y_test, y_prob)
                    print(f"AUC Score: {auc_score:.4f}")
            
            self.is_trained = True
            print(f"Model training completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error during training: {str(e)}")
            return False
    
    def predict(self, X):
        """Make fraud predictions"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare features
        if isinstance(X, dict):
            X = pd.DataFrame([X])
        elif isinstance(X, list):
            X = pd.DataFrame(X)
        
        # Ensure all feature columns are present
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0
        
        X = X[self.feature_columns]
        X = X.fillna(X.median())
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        if self.model_type == 'isolation_forest':
            # Convert -1/1 to 1/0 for fraud/normal
            predictions = self.model.predict(X_scaled)
            return (predictions == -1).astype(int)
        else:
            return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """Get fraud probability scores"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare features (same as predict)
        if isinstance(X, dict):
            X = pd.DataFrame([X])
        elif isinstance(X, list):
            X = pd.DataFrame(X)
        
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0
        
        X = X[self.feature_columns]
        X = X.fillna(X.median())
        X_scaled = self.scaler.transform(X)
        
        if self.model_type == 'isolation_forest':
            # Use decision function and normalize to 0-1
            scores = self.model.decision_function(X_scaled)
            # Convert to probability-like scores (higher = more likely fraud)
            proba = 1 / (1 + np.exp(scores))  # Sigmoid transformation
            return proba
        else:
            if hasattr(self.model, 'predict_proba'):
                return self.model.predict_proba(X_scaled)[:, 1]
            else:
                return self.model.decision_function(X_scaled)
    
    def save_model(self, filepath):
        """Save the trained model"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, filepath)
        print(f"Model saved to: {filepath}")
    
    def load_model(self, filepath):
        """Load a pre-trained model"""
        try:
            model_data = joblib.load(filepath)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.model_type = model_data['model_type']
            self.is_trained = model_data['is_trained']
            
            print(f"Model loaded from: {filepath}")
            return True
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            return False

# Global model instance
fraud_model = FraudDetectionModel('isolation_forest')

def train_model_from_data(data_path):
    """Train model from uploaded data"""
    try:
        # Load data
        if data_path.endswith('.csv'):
            df = pd.read_csv(data_path)
        else:
            raise ValueError("Only CSV files are supported")
        
        print(f"Loaded dataset with shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Train model
        success = fraud_model.train(df)
        
        if success:
            # Save trained model
            model_path = os.path.join('data', 'models', 'fraud_model.pkl')
            fraud_model.save_model(model_path)
            
        return success
        
    except Exception as e:
        print(f"Error training model: {str(e)}")
        return False

def load_pretrained_model():
    """Load pre-trained model if available"""
    model_path = os.path.join('data', 'models', 'fraud_model.pkl')
    if os.path.exists(model_path):
        return fraud_model.load_model(model_path)
    return False

# Load model on import if available
load_pretrained_model()
