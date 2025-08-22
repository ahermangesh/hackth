from flask import Blueprint, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return jsonify({
        'message': 'Fraud Detection API - Hackathon 2025',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'transactions': '/api/transactions',
            'ml_predict': '/api/ml/predict',
            'ml_status': '/api/ml/status',
            'dashboard': '/api/dashboard/stats'
        }
    })

@main_bp.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': '2025-08-22T00:00:00Z'
    })

@main_bp.route('/api/dashboard/stats')
def dashboard_stats():
    from models import Transaction, FraudAlert
    from app import db
    
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
