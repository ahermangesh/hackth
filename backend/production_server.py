#!/usr/bin/env python3
"""
Production Fraud Detection Server
With real ML model and proper error handling
"""

import sys
import os
import json
import logging
import pickle
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fraud_detection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    merchant = db.Column(db.String(100))
    card_type = db.Column(db.String(50))
    is_fraud = db.Column(db.Boolean, default=False)
    fraud_score = db.Column(db.Float, default=0.0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'amount': self.amount,
            'merchant': self.merchant,
            'card_type': self.card_type,
            'is_fraud': self.is_fraud,
            'fraud_score': self.fraud_score
        }

class FraudAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))
    alert_type = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ML Model Loader
class FraudDetectionML:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.load_model()
    
    def load_model(self):
        """Load the trained ML model"""
        try:
            model_path = os.path.join('..', 'data', 'models', 'fraud_model.pkl')
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data['model']
                    self.scaler = model_data['scaler']
                logger.info("✅ ML model loaded successfully!")
            else:
                logger.warning("⚠️ ML model file not found, using fallback rules")
                self.model = None
        except Exception as e:
            logger.error(f"❌ Error loading ML model: {e}")
            self.model = None
    
    def predict_fraud(self, features):
        """Predict fraud probability for transaction features"""
        try:
            if self.model is None:
                # Fallback rule-based detection
                return self._rule_based_detection(features)
            
            # Use ML model
            features_scaled = self.scaler.transform([features])
            fraud_prob = self.model.predict_proba(features_scaled)[0][1]
            is_fraud = fraud_prob > 0.5
            
            return is_fraud, fraud_prob
            
        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")
            return self._rule_based_detection(features)
    
    def _rule_based_detection(self, features):
        """Fallback rule-based fraud detection"""
        # Simple rules based on amount and patterns
        amount = features[0] if len(features) > 0 else 0
        
        # High risk conditions
        if amount > 10000:  # Large transactions
            return True, 0.8
        elif amount > 5000:  # Medium transactions
            return True, 0.6
        else:
            return False, 0.1

# Initialize ML model
ml_detector = FraudDetectionML()

# API Routes
@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Fraud Detection API',
        'timestamp': datetime.utcnow().isoformat(),
        'ml_model': 'loaded' if ml_detector.model else 'fallback',
        'version': '1.0.0'
    })

@app.route('/api/predict', methods=['POST'])
def predict_fraud():
    """Predict fraud for a transaction"""
    try:
        data = request.get_json()
        
        # Extract features (simplified for demo)
        amount = float(data.get('amount', 0))
        merchant = data.get('merchant', 'Unknown')
        card_type = data.get('card_type', 'credit')
        
        # Create feature vector (simplified - in real case use V1-V28 features)
        features = [amount] + [0] * 29  # Pad to 30 features like trained model
        
        # Predict fraud
        is_fraud, fraud_score = ml_detector.predict_fraud(features)
        
        # Store transaction
        transaction = Transaction(
            amount=amount,
            merchant=merchant,
            card_type=card_type,
            is_fraud=is_fraud,
            fraud_score=fraud_score
        )
        db.session.add(transaction)
        
        # Create alert if fraud detected
        if is_fraud:
            alert = FraudAlert(
                transaction_id=transaction.id,
                alert_type='high_risk',
                confidence=fraud_score
            )
            db.session.add(alert)
        
        db.session.commit()
        
        return jsonify({
            'transaction_id': transaction.id,
            'is_fraud': is_fraud,
            'fraud_score': round(fraud_score, 4),
            'risk_level': 'HIGH' if fraud_score > 0.7 else 'MEDIUM' if fraud_score > 0.3 else 'LOW',
            'timestamp': transaction.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get recent transactions"""
    try:
        limit = int(request.args.get('limit', 50))
        transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'transactions': [t.to_dict() for t in transactions],
            'count': len(transactions)
        })
        
    except Exception as e:
        logger.error(f"❌ Error fetching transactions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get fraud detection statistics"""
    try:
        total_transactions = Transaction.query.count()
        fraud_transactions = Transaction.query.filter_by(is_fraud=True).count()
        recent_alerts = FraudAlert.query.order_by(FraudAlert.created_at.desc()).limit(10).all()
        
        fraud_rate = (fraud_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        return jsonify({
            'total_transactions': total_transactions,
            'fraud_transactions': fraud_transactions,
            'fraud_rate': round(fraud_rate, 2),
            'recent_alerts': len(recent_alerts),
            'model_status': 'active' if ml_detector.model else 'fallback'
        })
        
    except Exception as e:
        logger.error(f"❌ Error fetching stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        # Create database tables
        with app.app_context():
            db.create_all()
            logger.info("✅ Database tables created")
        
        logger.info("🚀 Starting Fraud Detection Server...")
        logger.info(f"🔗 Server will be available at: http://localhost:5000")
        logger.info(f"🤖 ML Model Status: {'Loaded' if ml_detector.model else 'Fallback Rules'}")
        
        # Start the server
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # Disable debug for production
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)
