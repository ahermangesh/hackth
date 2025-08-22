from flask import Blueprint, request, jsonify
from models import Transaction, FraudAlert, db
from ml.fraud_model import fraud_model
from datetime import datetime
import uuid

transaction_bp = Blueprint('transactions', __name__)

@transaction_bp.route('/', methods=['GET'])
def get_transactions():
    """Get all transactions with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Filter by fraud status if requested
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

@transaction_bp.route('/', methods=['POST'])
def create_transaction():
    """Create a new transaction and check for fraud"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'error'
            }), 400
        
        # Validate required fields
        required_fields = ['amount', 'user_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'status': 'error'
                }), 400
        
        # Create transaction
        transaction = Transaction(
            amount=float(data['amount']),
            user_id=data['user_id'],
            merchant_id=data.get('merchant_id', f"merchant_{uuid.uuid4().hex[:8]}"),
            transaction_type=data.get('transaction_type', 'credit_card'),
            location=data.get('location'),
            device_id=data.get('device_id'),
            ip_address=data.get('ip_address'),
            timestamp=datetime.utcnow()
        )
        
        # Fraud detection if model is trained
        if fraud_model.is_trained:
            try:
                # Prepare features for ML model
                ml_features = {
                    'Amount': transaction.amount,
                    'Time': 0,  # Will be calculated based on timestamp
                }
                
                # Add additional features if provided
                for i in range(28):  # V1-V28 features common in fraud datasets
                    feature_name = f'V{i+1}'
                    ml_features[feature_name] = data.get(feature_name, 0.0)
                
                # Make prediction
                fraud_prediction = fraud_model.predict(ml_features)[0]
                fraud_probability = fraud_model.predict_proba(ml_features)[0]
                
                transaction.is_fraud = bool(fraud_prediction)
                transaction.fraud_score = float(fraud_probability)
                
                # Create fraud alert if high risk
                if fraud_probability > 0.7:
                    alert = FraudAlert(
                        transaction_id=None,  # Will be set after transaction is saved
                        alert_type='high_risk',
                        confidence_score=fraud_probability,
                        description=f'High fraud probability: {fraud_probability:.3f}',
                        status='pending'
                    )
                    
                    # We'll add the alert after saving the transaction
                    transaction.fraud_reason = f"ML Model flagged with {fraud_probability:.1%} confidence"
                
            except Exception as ml_error:
                print(f"ML prediction error: {ml_error}")
                transaction.fraud_score = 0.0
                transaction.is_fraud = False
        
        # Save transaction
        db.session.add(transaction)
        db.session.commit()
        
        # Create fraud alert if needed
        if transaction.fraud_score > 0.7:
            alert = FraudAlert(
                transaction_id=transaction.id,
                alert_type='high_risk',
                confidence_score=transaction.fraud_score,
                description=f'High fraud probability: {transaction.fraud_score:.3f}',
                status='pending'
            )
            db.session.add(alert)
            db.session.commit()
        
        response_data = transaction.to_dict()
        response_data['ml_prediction'] = {
            'model_available': fraud_model.is_trained,
            'prediction_made': fraud_model.is_trained
        }
        
        return jsonify({
            'transaction': response_data,
            'status': 'created'
        }), 201
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@transaction_bp.route('/<int:transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """Get specific transaction details"""
    try:
        transaction = Transaction.query.get_or_404(transaction_id)
        return jsonify({
            'transaction': transaction.to_dict(),
            'alerts': [alert.to_dict() for alert in transaction.alerts],
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@transaction_bp.route('/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """Update transaction (e.g., mark as legitimate/fraud)"""
    try:
        transaction = Transaction.query.get_or_404(transaction_id)
        data = request.get_json()
        
        # Update allowed fields
        if 'is_fraud' in data:
            transaction.is_fraud = bool(data['is_fraud'])
        
        if 'fraud_reason' in data:
            transaction.fraud_reason = data['fraud_reason']
        
        transaction.updated_at = datetime.utcnow()
        
        # Update related alerts
        if 'alert_status' in data:
            for alert in transaction.alerts:
                alert.status = data['alert_status']
        
        db.session.commit()
        
        return jsonify({
            'transaction': transaction.to_dict(),
            'status': 'updated'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@transaction_bp.route('/bulk', methods=['POST'])
def create_bulk_transactions():
    """Create multiple transactions for testing"""
    try:
        data = request.get_json()
        
        if not data or 'transactions' not in data:
            return jsonify({
                'error': 'No transactions provided',
                'status': 'error'
            }), 400
        
        transactions_data = data['transactions']
        created_transactions = []
        
        for trans_data in transactions_data:
            # Create transaction
            transaction = Transaction(
                amount=float(trans_data['amount']),
                user_id=trans_data['user_id'],
                merchant_id=trans_data.get('merchant_id', f"merchant_{uuid.uuid4().hex[:8]}"),
                transaction_type=trans_data.get('transaction_type', 'credit_card'),
                timestamp=datetime.utcnow()
            )
            
            # Fraud detection
            if fraud_model.is_trained:
                try:
                    ml_features = {
                        'Amount': transaction.amount,
                        'Time': 0,
                    }
                    
                    for i in range(28):
                        feature_name = f'V{i+1}'
                        ml_features[feature_name] = trans_data.get(feature_name, 0.0)
                    
                    fraud_prediction = fraud_model.predict(ml_features)[0]
                    fraud_probability = fraud_model.predict_proba(ml_features)[0]
                    
                    transaction.is_fraud = bool(fraud_prediction)
                    transaction.fraud_score = float(fraud_probability)
                    
                except Exception:
                    transaction.fraud_score = 0.0
                    transaction.is_fraud = False
            
            db.session.add(transaction)
            created_transactions.append(transaction)
        
        db.session.commit()
        
        return jsonify({
            'transactions': [t.to_dict() for t in created_transactions],
            'total_created': len(created_transactions),
            'status': 'success'
        }), 201
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@transaction_bp.route('/sample', methods=['POST'])
def generate_sample_transactions():
    """Generate sample transactions for testing"""
    import random
    
    try:
        count = request.json.get('count', 10) if request.json else 10
        count = min(count, 100)  # Limit to 100 for safety
        
        sample_transactions = []
        
        for i in range(count):
            # Random transaction data
            amount = round(random.uniform(10, 1000), 2)
            is_suspicious = random.random() < 0.1  # 10% suspicious
            
            transaction = Transaction(
                amount=amount * (5 if is_suspicious else 1),  # Suspicious ones have higher amounts
                user_id=f"user_{random.randint(1000, 9999)}",
                merchant_id=f"merchant_{random.randint(100, 999)}",
                transaction_type=random.choice(['credit_card', 'upi', 'bank_transfer']),
                location=random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata']),
                device_id=f"device_{random.randint(1000000, 9999999)}",
                timestamp=datetime.utcnow()
            )
            
            # Simple rule-based fraud detection for samples
            if amount > 5000 or is_suspicious:
                transaction.is_fraud = True
                transaction.fraud_score = random.uniform(0.7, 0.9)
                transaction.fraud_reason = "High amount or suspicious pattern"
            else:
                transaction.is_fraud = False
                transaction.fraud_score = random.uniform(0.1, 0.3)
            
            db.session.add(transaction)
            sample_transactions.append(transaction)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Generated {count} sample transactions',
            'transactions': [t.to_dict() for t in sample_transactions[-5:]],  # Return last 5
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500
