from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import sys
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'hackathon-fraud-detection-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fraud_detection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Database Models
class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    merchant_id = db.Column(db.String(100))
    user_id = db.Column(db.String(100))
    transaction_type = db.Column(db.String(50))
    
    # Fraud detection results
    is_fraud = db.Column(db.Boolean, default=False)
    fraud_score = db.Column(db.Float, default=0.0)
    fraud_reason = db.Column(db.Text)
    
    # Additional features
    location = db.Column(db.String(100))
    device_id = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'merchant_id': self.merchant_id,
            'user_id': self.user_id,
            'transaction_type': self.transaction_type,
            'is_fraud': self.is_fraud,
            'fraud_score': self.fraud_score,
            'fraud_reason': self.fraud_reason,
            'location': self.location,
            'device_id': self.device_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class FraudAlert(db.Model):
    __tablename__ = 'fraud_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    alert_type = db.Column(db.String(50))
    confidence_score = db.Column(db.Float)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transaction = db.relationship('Transaction', backref=db.backref('alerts', lazy=True))

# Simple ML Model (placeholder for hackathon)
class SimpleFraudModel:
    def __init__(self):
        self.is_trained = True  # Always ready for demo
    
    def predict_fraud(self, amount, user_id=None):
        """Simple rule-based fraud detection for demo"""
        fraud_score = 0.1  # Base score
        
        # Rule 1: High amounts are suspicious
        if amount > 1000:
            fraud_score += 0.3
        if amount > 5000:
            fraud_score += 0.4
        
        # Rule 2: Round numbers might be suspicious
        if amount % 100 == 0:
            fraud_score += 0.1
        
        # Rule 3: Very small amounts might be testing
        if amount < 1:
            fraud_score += 0.2
        
        # Add some randomness for demo
        import random
        fraud_score += random.uniform(-0.1, 0.2)
        
        # Ensure score is between 0 and 1
        fraud_score = max(0, min(1, fraud_score))
        
        is_fraud = fraud_score > 0.5
        return is_fraud, fraud_score

# Initialize simple model
fraud_model = SimpleFraudModel()

# Routes
@app.route('/')
def index():
    return jsonify({
        'message': '🛡️ Fraud Detection API - Hackathon 2025',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'transactions': '/api/transactions',
            'ml_predict': '/api/ml/predict',
            'dashboard': '/api/dashboard/stats'
        }
    })

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/dashboard/stats')
def dashboard_stats():
    try:
        total_transactions = Transaction.query.count()
        fraud_transactions = Transaction.query.filter_by(is_fraud=True).count()
        pending_alerts = FraudAlert.query.filter_by(status='pending').count()
        
        fraud_rate = (fraud_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        return jsonify({
            'total_transactions': total_transactions,
            'fraud_transactions': fraud_transactions,
            'pending_alerts': pending_alerts,
            'fraud_rate': round(fraud_rate, 2),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/transactions/', methods=['GET'])
def get_transactions():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        fraud_filter = request.args.get('fraud_only', 'false').lower() == 'true'
        
        query = Transaction.query
        if fraud_filter:
            query = query.filter_by(is_fraud=True)
        
        transactions = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'transactions': [t.to_dict() for t in transactions.items],
            'total': transactions.total,
            'pages': transactions.pages,
            'current_page': page,
            'per_page': per_page,
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/transactions/', methods=['POST'])
def create_transaction():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'error'
            }), 400
        
        # Validate required fields
        if 'amount' not in data or 'user_id' not in data:
            return jsonify({
                'error': 'Missing required fields: amount, user_id',
                'status': 'error'
            }), 400
        
        # Create transaction
        transaction = Transaction(
            amount=float(data['amount']),
            user_id=data['user_id'],
            merchant_id=data.get('merchant_id', f"merchant_{datetime.now().strftime('%H%M%S')}"),
            transaction_type=data.get('transaction_type', 'credit_card'),
            location=data.get('location', 'Unknown'),
            device_id=data.get('device_id'),
            ip_address=data.get('ip_address'),
            timestamp=datetime.utcnow()
        )
        
        # Fraud detection
        is_fraud, fraud_score = fraud_model.predict_fraud(transaction.amount, transaction.user_id)
        transaction.is_fraud = is_fraud
        transaction.fraud_score = fraud_score
        
        if is_fraud:
            transaction.fraud_reason = f"High risk transaction detected (Score: {fraud_score:.2f})"
        
        # Save transaction
        db.session.add(transaction)
        db.session.commit()
        
        # Create fraud alert if needed
        if fraud_score > 0.7:
            alert = FraudAlert(
                transaction_id=transaction.id,
                alert_type='high_risk',
                confidence_score=fraud_score,
                description=f'High fraud probability: {fraud_score:.3f}',
                status='pending'
            )
            db.session.add(alert)
            db.session.commit()
        
        return jsonify({
            'transaction': transaction.to_dict(),
            'status': 'created'
        }), 201
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/transactions/sample', methods=['POST'])
def generate_sample_transactions():
    import random
    import uuid
    
    try:
        count = request.json.get('count', 10) if request.json else 10
        count = min(count, 100)
        
        sample_transactions = []
        
        for i in range(count):
            amount = round(random.uniform(10, 2000), 2)
            is_suspicious = random.random() < 0.15  # 15% suspicious
            
            transaction = Transaction(
                amount=amount * (3 if is_suspicious else 1),
                user_id=f"user_{random.randint(1000, 9999)}",
                merchant_id=f"merchant_{random.randint(100, 999)}",
                transaction_type=random.choice(['credit_card', 'upi', 'bank_transfer']),
                location=random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Pune']),
                device_id=f"device_{uuid.uuid4().hex[:8]}",
                timestamp=datetime.utcnow()
            )
            
            # Apply fraud detection
            is_fraud, fraud_score = fraud_model.predict_fraud(transaction.amount, transaction.user_id)
            transaction.is_fraud = is_fraud
            transaction.fraud_score = fraud_score
            
            if is_fraud:
                transaction.fraud_reason = "Suspicious pattern detected by ML model"
            
            db.session.add(transaction)
            sample_transactions.append(transaction)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Generated {count} sample transactions',
            'transactions': [t.to_dict() for t in sample_transactions[-5:]],
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/ml/status')
def ml_status():
    return jsonify({
        'model_loaded': fraud_model.is_trained,
        'model_type': 'rule_based_demo',
        'status': 'ready',
        'message': 'Demo fraud detection model is ready'
    })

@app.route('/api/ml/predict', methods=['POST'])
def ml_predict():
    try:
        data = request.get_json()
        
        if not data or 'amount' not in data:
            return jsonify({
                'error': 'Amount is required',
                'status': 'error'
            }), 400
        
        amount = float(data['amount'])
        user_id = data.get('user_id', 'unknown')
        
        is_fraud, fraud_score = fraud_model.predict_fraud(amount, user_id)
        
        # Determine risk level
        if fraud_score > 0.8:
            risk_level = 'high'
        elif fraud_score > 0.5:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return jsonify({
            'is_fraud': is_fraud,
            'fraud_probability': fraud_score,
            'risk_level': risk_level,
            'confidence': abs(fraud_score - 0.5) * 2,
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    print("🚀 Fraud Detection API Server Starting...")
    print("📊 Frontend: http://localhost:3000")
    print("🔌 API: http://localhost:5000")
    print("📚 Test API: http://localhost:5000")
    print("\n🎯 Ready for Hackathon Demo!")
    app.run(debug=True, host='0.0.0.0', port=5000)
