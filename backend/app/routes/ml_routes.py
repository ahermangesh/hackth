from flask import Blueprint, request, jsonify
from ml.fraud_model import fraud_model, train_model_from_data
import numpy as np
import pandas as pd
import os

ml_bp = Blueprint('ml', __name__)

@ml_bp.route('/status', methods=['GET'])
def model_status():
    """Get current model status"""
    return jsonify({
        'model_loaded': fraud_model.is_trained,
        'model_type': fraud_model.model_type,
        'feature_count': len(fraud_model.feature_columns) if fraud_model.feature_columns else 0,
        'features': fraud_model.feature_columns[:10] if fraud_model.feature_columns else [],  # First 10 features
        'status': 'ready' if fraud_model.is_trained else 'not_trained'
    })

@ml_bp.route('/predict', methods=['POST'])
def predict_fraud():
    """Predict fraud for a single transaction"""
    try:
        if not fraud_model.is_trained:
            return jsonify({
                'error': 'Model not trained yet. Please train model first.',
                'status': 'error'
            }), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'error'
            }), 400
        
        # Handle both single transaction and batch predictions
        if 'features' in data:
            # Single transaction with features array
            features_dict = {}
            for i, value in enumerate(data['features']):
                features_dict[f'V{i+1}'] = value
            prediction_data = features_dict
        else:
            # Direct feature dictionary
            prediction_data = data
        
        # Make prediction
        prediction = fraud_model.predict(prediction_data)[0]
        probability = fraud_model.predict_proba(prediction_data)[0]
        
        # Determine risk level
        if probability > 0.8:
            risk_level = 'high'
        elif probability > 0.6:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return jsonify({
            'is_fraud': bool(prediction),
            'fraud_probability': float(probability),
            'risk_level': risk_level,
            'confidence': float(abs(probability - 0.5) * 2),  # 0-1 confidence score
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@ml_bp.route('/predict/batch', methods=['POST'])
def predict_batch():
    """Predict fraud for multiple transactions"""
    try:
        if not fraud_model.is_trained:
            return jsonify({
                'error': 'Model not trained yet. Please train model first.',
                'status': 'error'
            }), 400
        
        data = request.get_json()
        
        if not data or 'transactions' not in data:
            return jsonify({
                'error': 'No transactions provided',
                'status': 'error'
            }), 400
        
        transactions = data['transactions']
        results = []
        
        for i, transaction in enumerate(transactions):
            try:
                prediction = fraud_model.predict(transaction)[0]
                probability = fraud_model.predict_proba(transaction)[0]
                
                results.append({
                    'transaction_id': i,
                    'is_fraud': bool(prediction),
                    'fraud_probability': float(probability),
                    'risk_level': 'high' if probability > 0.8 else 'medium' if probability > 0.6 else 'low'
                })
            except Exception as e:
                results.append({
                    'transaction_id': i,
                    'error': str(e),
                    'is_fraud': False,
                    'fraud_probability': 0.0
                })
        
        return jsonify({
            'predictions': results,
            'total_processed': len(results),
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@ml_bp.route('/train', methods=['POST'])
def train_model():
    """Train model with uploaded data"""
    try:
        # Check if file is uploaded
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file uploaded',
                'status': 'error'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'status': 'error'
            }), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({
                'error': 'Only CSV files are supported',
                'status': 'error'
            }), 400
        
        # Save uploaded file
        os.makedirs('data/raw', exist_ok=True)
        file_path = os.path.join('data/raw', file.filename)
        file.save(file_path)
        
        # Train model
        success = train_model_from_data(file_path)
        
        if success:
            return jsonify({
                'message': 'Model trained successfully',
                'model_type': fraud_model.model_type,
                'feature_count': len(fraud_model.feature_columns),
                'status': 'success'
            })
        else:
            return jsonify({
                'error': 'Model training failed',
                'status': 'error'
            }), 500
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@ml_bp.route('/retrain', methods=['POST'])
def retrain_model():
    """Retrain model with existing data"""
    try:
        # Look for existing data files
        data_files = []
        if os.path.exists('data/raw'):
            data_files = [f for f in os.listdir('data/raw') if f.endswith('.csv')]
        
        if not data_files:
            return jsonify({
                'error': 'No training data found. Please upload data first.',
                'status': 'error'
            }), 400
        
        # Use the first available CSV file
        file_path = os.path.join('data/raw', data_files[0])
        success = train_model_from_data(file_path)
        
        if success:
            return jsonify({
                'message': 'Model retrained successfully',
                'data_file': data_files[0],
                'model_type': fraud_model.model_type,
                'status': 'success'
            })
        else:
            return jsonify({
                'error': 'Model retraining failed',
                'status': 'error'
            }), 500
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@ml_bp.route('/sample-prediction', methods=['GET'])
def sample_prediction():
    """Generate a sample prediction for testing"""
    try:
        if not fraud_model.is_trained:
            return jsonify({
                'error': 'Model not trained yet.',
                'status': 'error'
            }), 400
        
        # Create sample transaction data
        sample_data = {}
        for i, feature in enumerate(fraud_model.feature_columns[:10]):  # Use first 10 features
            sample_data[feature] = np.random.normal(0, 1)  # Random normal values
        
        # Add amount if not present
        if 'Amount' not in sample_data:
            sample_data['Amount'] = np.random.uniform(1, 1000)
        
        prediction = fraud_model.predict(sample_data)[0]
        probability = fraud_model.predict_proba(sample_data)[0]
        
        return jsonify({
            'sample_data': sample_data,
            'is_fraud': bool(prediction),
            'fraud_probability': float(probability),
            'risk_level': 'high' if probability > 0.8 else 'medium' if probability > 0.6 else 'low',
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500
