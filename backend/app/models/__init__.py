from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Import db from parent module
try:
    from app import db
except ImportError:
    # Fallback for when running from different context
    db = None

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    merchant_id = db.Column(db.String(100))
    user_id = db.Column(db.String(100))
    transaction_type = db.Column(db.String(50))  # 'credit_card', 'upi', 'bank_transfer'
    
    # Fraud detection results
    is_fraud = db.Column(db.Boolean, default=False)
    fraud_score = db.Column(db.Float, default=0.0)
    fraud_reason = db.Column(db.Text)
    
    # Additional features for ML
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
    alert_type = db.Column(db.String(50))  # 'high_risk', 'suspicious_pattern', 'anomaly'
    confidence_score = db.Column(db.Float)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'reviewed', 'false_positive'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    transaction = db.relationship('Transaction', backref=db.backref('alerts', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'alert_type': self.alert_type,
            'confidence_score': self.confidence_score,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'transaction': self.transaction.to_dict() if self.transaction else None
        }
