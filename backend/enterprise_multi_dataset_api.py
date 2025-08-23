#!/usr/bin/env python3
"""
Enterprise Multi-Dataset Fraud Detection API
Supports UPI, Credit Card, and Online Payment fraud detection
"""

from flask import Flask, Blueprint, request, jsonify, send_file
import pandas as pd
import numpy as np
import os
import uuid
import json
import threading
import time
from datetime import datetime
from werkzeug.utils import secure_filename
import sys

# Import our advanced fraud detector
sys.path.append('.')
from advanced_fraud_detector import AdvancedFraudDetector

enterprise_multi_bp = Blueprint('enterprise_multi', __name__)

# Configuration
UPLOAD_FOLDER = 'uploads/enterprise'
REPORTS_FOLDER = 'reports/enterprise'
MODELS_FOLDER = 'data/models'
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB for enterprise
ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx'}

# Ensure directories exist
for folder in [UPLOAD_FOLDER, REPORTS_FOLDER, MODELS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Global fraud detector
fraud_detector = None
active_jobs = {}

def initialize_fraud_detector():
    """Initialize or load the advanced fraud detector"""
    global fraud_detector
    
    if fraud_detector is None:
        fraud_detector = AdvancedFraudDetector()
        
        # Try to load pre-trained models
        model_path = os.path.join(MODELS_FOLDER, 'advanced_fraud_models.pkl')
        if os.path.exists(model_path):
            fraud_detector.load_models(model_path)
            print("✅ Pre-trained models loaded")
        else:
            print("⚠️ No pre-trained models found. Training new models...")
            # Train models in background
            threading.Thread(target=train_models_background).start()
    
    return fraud_detector

def train_models_background():
    """Train models in background"""
    global fraud_detector
    try:
        fraud_detector.train_all_models()
        fraud_detector.save_models(MODELS_FOLDER)
        print("✅ Background model training completed")
    except Exception as e:
        print(f"❌ Background training failed: {e}")

def detect_dataset_type(df):
    """Auto-detect dataset type based on columns"""
    columns = set(df.columns.str.lower())
    
    # UPI dataset indicators
    upi_indicators = {'transaction type', 'sender_bank', 'receiver_bank', 'device_type', 'fraud_flag'}
    if len(upi_indicators.intersection(columns)) >= 3:
        return 'upi'
    
    # Credit card dataset indicators  
    cc_indicators = {'time', 'amount', 'class'}
    v_columns = [col for col in df.columns if col.startswith('V') and col[1:].isdigit()]
    if len(cc_indicators.intersection(columns)) >= 2 and len(v_columns) > 10:
        return 'creditcard'
    
    # Online fraud dataset indicators
    online_indicators = {'type', 'oldbalanceorg', 'newbalanceorig', 'isfraud'}
    if len(online_indicators.intersection(columns)) >= 3:
        return 'onlinefraud'
    
    # Default to UPI if uncertain
    return 'upi'

def analyze_transactions_batch(job_id, file_path, customer_id, dataset_type=None):
    """Analyze transactions in batch mode"""
    try:
        active_jobs[job_id]['status'] = 'processing'
        active_jobs[job_id]['progress'] = 10
        
        # Initialize detector
        detector = initialize_fraud_detector()
        
        # Load data
        print(f"Loading data from {file_path}")
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_json(file_path)
        
        active_jobs[job_id]['progress'] = 20
        active_jobs[job_id]['total_transactions'] = len(df)
        
        # Auto-detect dataset type if not provided
        if dataset_type is None:
            dataset_type = detect_dataset_type(df)
        
        active_jobs[job_id]['dataset_type'] = dataset_type
        active_jobs[job_id]['progress'] = 30
        
        print(f"Detected dataset type: {dataset_type}")
        
        # Analyze each transaction
        results = []
        fraud_count = 0
        total_amount = 0
        fraud_amount = 0
        
        batch_size = 1000
        total_batches = len(df) // batch_size + 1
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]
            
            for idx, row in batch_df.iterrows():
                transaction_data = row.to_dict()
                
                # Get amount for different dataset types
                amount = 0
                if dataset_type == 'upi' and 'amount (INR)' in transaction_data:
                    amount = transaction_data['amount (INR)']
                elif dataset_type == 'creditcard' and 'Amount' in transaction_data:
                    amount = transaction_data['Amount']
                elif dataset_type == 'onlinefraud' and 'amount' in transaction_data:
                    amount = transaction_data['amount']
                
                total_amount += amount
                
                # Predict fraud
                prediction = detector.predict_fraud(transaction_data, dataset_type)
                
                if prediction.get('is_fraud', False):
                    fraud_count += 1
                    fraud_amount += amount
                
                # Store result
                result = {
                    'transaction_id': transaction_data.get('transaction id', 
                                    transaction_data.get('transaction_id', f'TXN_{idx}')),
                    'amount': amount,
                    'is_fraud': prediction.get('is_fraud', False),
                    'fraud_probability': prediction.get('fraud_probability', 0),
                    'risk_level': prediction.get('risk_level', 'LOW'),
                    'confidence': prediction.get('confidence', 0),
                    'model_used': prediction.get('model_used', dataset_type)
                }
                
                results.append(result)
            
            # Update progress
            progress = 30 + ((batch_idx + 1) / total_batches) * 60
            active_jobs[job_id]['progress'] = min(progress, 90)
        
        # Generate comprehensive enterprise report
        report = generate_enterprise_fraud_report(
            results, df, customer_id, dataset_type, fraud_count, 
            total_amount, fraud_amount
        )
        
        # Save report
        report_filename = f"enterprise_fraud_analysis_{job_id}.json"
        report_path = os.path.join(REPORTS_FOLDER, report_filename)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Complete job
        active_jobs[job_id]['status'] = 'completed'
        active_jobs[job_id]['progress'] = 100
        active_jobs[job_id]['report_file'] = report_filename
        active_jobs[job_id]['completed_at'] = datetime.now()
        active_jobs[job_id]['fraud_detected'] = fraud_count
        active_jobs[job_id]['fraud_rate'] = (fraud_count / len(df)) * 100 if len(df) > 0 else 0
        
        print(f"✅ Analysis completed for job {job_id}")
        
    except Exception as e:
        active_jobs[job_id]['status'] = 'failed'
        active_jobs[job_id]['error'] = str(e)
        print(f"❌ Analysis failed for job {job_id}: {e}")

def generate_enterprise_fraud_report(results, original_df, customer_id, dataset_type, 
                                   fraud_count, total_amount, fraud_amount):
    """Generate comprehensive enterprise fraud report"""
    
    total_transactions = len(results)
    fraud_rate = (fraud_count / total_transactions) * 100 if total_transactions > 0 else 0
    risk_percentage = (fraud_amount / total_amount) * 100 if total_amount > 0 else 0
    
    # Risk distribution
    risk_distribution = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for result in results:
        risk_level = result.get('risk_level', 'LOW')
        risk_distribution[risk_level] += 1
    
    # Top risky transactions
    top_risky = sorted(results, key=lambda x: x.get('fraud_probability', 0), reverse=True)[:20]
    
    # Dataset-specific insights
    dataset_insights = generate_dataset_insights(original_df, dataset_type, results)
    
    # Generate recommendations
    recommendations = generate_advanced_recommendations(results, dataset_type, fraud_rate)
    
    # Model performance metrics
    detector = initialize_fraud_detector()
    model_performance = detector.model_performance.get(dataset_type, {})
    
    report = {
        'analysis_summary': {
            'customer_id': customer_id,
            'analysis_date': datetime.now().isoformat(),
            'dataset_type': dataset_type,
            'total_transactions': total_transactions,
            'fraud_transactions': fraud_count,
            'fraud_rate_percentage': round(fraud_rate, 2),
            'total_amount': float(total_amount),
            'amount_at_risk': float(fraud_amount),
            'risk_percentage': round(risk_percentage, 2),
            'model_performance': model_performance
        },
        'risk_analysis': {
            'risk_distribution': risk_distribution,
            'risk_distribution_percentage': {
                level: round((count / total_transactions) * 100, 2) 
                for level, count in risk_distribution.items()
            },
            'average_fraud_probability': round(
                np.mean([r.get('fraud_probability', 0) for r in results]), 3
            )
        },
        'dataset_insights': dataset_insights,
        'top_risky_transactions': top_risky,
        'recommendations': recommendations,
        'detailed_results': results[:1000],  # Limit to first 1000 for file size
        'export_info': {
            'full_results_count': len(results),
            'report_generated_at': datetime.now().isoformat(),
            'model_version': '2.0_multi_dataset'
        }
    }
    
    return report

def generate_dataset_insights(df, dataset_type, results):
    """Generate dataset-specific insights"""
    insights = {
        'dataset_type': dataset_type,
        'total_features_analyzed': 0,
        'key_patterns': []
    }
    
    if dataset_type == 'upi':
        insights.update({
            'transaction_types': df['transaction type'].value_counts().to_dict() if 'transaction type' in df.columns else {},
            'top_merchant_categories': df['merchant_category'].value_counts().head(10).to_dict() if 'merchant_category' in df.columns else {},
            'cross_state_transactions': int((df['sender_state'] != df['receiver_state']).sum()) if all(col in df.columns for col in ['sender_state', 'receiver_state']) else 0,
            'device_distribution': df['device_type'].value_counts().to_dict() if 'device_type' in df.columns else {},
            'peak_fraud_hours': analyze_fraud_by_hour(df, results) if 'hour_of_day' in df.columns else {}
        })
        
    elif dataset_type == 'creditcard':
        insights.update({
            'amount_statistics': {
                'mean': float(df['Amount'].mean()) if 'Amount' in df.columns else 0,
                'median': float(df['Amount'].median()) if 'Amount' in df.columns else 0,
                'std': float(df['Amount'].std()) if 'Amount' in df.columns else 0
            },
            'time_analysis': analyze_credit_card_time_patterns(df, results),
            'v_features_importance': 'V1-V28 PCA features analyzed'
        })
        
    elif dataset_type == 'onlinefraud':
        insights.update({
            'transaction_types': df['type'].value_counts().to_dict() if 'type' in df.columns else {},
            'balance_analysis': analyze_balance_patterns(df, results),
            'merchant_patterns': analyze_merchant_patterns(df, results)
        })
    
    return insights

def analyze_fraud_by_hour(df, results):
    """Analyze fraud patterns by hour"""
    if 'hour_of_day' not in df.columns:
        return {}
    
    fraud_by_hour = {}
    for i, result in enumerate(results):
        if i < len(df):
            hour = df.iloc[i]['hour_of_day']
            if hour not in fraud_by_hour:
                fraud_by_hour[hour] = {'total': 0, 'fraud': 0}
            fraud_by_hour[hour]['total'] += 1
            if result.get('is_fraud', False):
                fraud_by_hour[hour]['fraud'] += 1
    
    # Calculate fraud rates by hour
    fraud_rates = {}
    for hour, data in fraud_by_hour.items():
        fraud_rates[int(hour)] = round((data['fraud'] / data['total']) * 100, 2) if data['total'] > 0 else 0
    
    return fraud_rates

def analyze_credit_card_time_patterns(df, results):
    """Analyze credit card time patterns"""
    if 'Time' not in df.columns:
        return {}
    
    # Convert time to hours
    hours = (df['Time'] / 3600) % 24
    
    return {
        'peak_transaction_hours': hours.value_counts().head(5).to_dict(),
        'transaction_time_spread': {
            'mean_hour': float(hours.mean()),
            'std_hour': float(hours.std())
        }
    }

def analyze_balance_patterns(df, results):
    """Analyze balance patterns for online fraud"""
    balance_cols = ['oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest']
    available_cols = [col for col in balance_cols if col in df.columns]
    
    if not available_cols:
        return {}
    
    return {
        'zero_balance_transactions': int((df[available_cols] == 0).all(axis=1).sum()),
        'balance_change_patterns': 'Analyzed balance flow patterns',
        'high_balance_transfers': int((df['amount'] > 100000).sum()) if 'amount' in df.columns else 0
    }

def analyze_merchant_patterns(df, results):
    """Analyze merchant patterns"""
    merchant_analysis = {}
    
    if 'nameDest' in df.columns:
        # Merchant transaction counts
        merchant_counts = df['nameDest'].value_counts().head(10)
        merchant_analysis['top_merchants'] = merchant_counts.to_dict()
    
    return merchant_analysis

def generate_advanced_recommendations(results, dataset_type, fraud_rate):
    """Generate advanced, actionable recommendations"""
    recommendations = []
    
    high_risk_count = sum(1 for r in results if r.get('risk_level') == 'HIGH')
    medium_risk_count = sum(1 for r in results if r.get('risk_level') == 'MEDIUM')
    
    # High priority recommendations
    if high_risk_count > 0:
        recommendations.append({
            'priority': 'CRITICAL',
            'category': 'Immediate Action',
            'action': f'Investigate {high_risk_count} high-risk transactions immediately',
            'impact': 'Prevent potential fraud losses',
            'estimated_savings': f'₹{high_risk_count * 25000:,}',  # Estimated average fraud amount
            'timeline': '24 hours'
        })
    
    if fraud_rate > 5:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'System Enhancement',
            'action': 'Implement stricter fraud detection rules',
            'impact': f'Reduce fraud rate from {fraud_rate:.1f}% to <2%',
            'estimated_savings': '60-80% reduction in fraud losses',
            'timeline': '1-2 weeks'
        })
    
    # Dataset-specific recommendations
    if dataset_type == 'upi':
        recommendations.extend([
            {
                'priority': 'MEDIUM',
                'category': 'UPI Security',
                'action': 'Enhanced monitoring for cross-state transactions',
                'impact': 'Reduce geographic fraud patterns',
                'timeline': '1 week'
            },
            {
                'priority': 'MEDIUM',
                'category': 'Time-based Controls',
                'action': 'Implement additional verification for night-time transactions',
                'impact': 'Reduce time-based fraud',
                'timeline': '2 weeks'
            }
        ])
    
    elif dataset_type == 'creditcard':
        recommendations.extend([
            {
                'priority': 'MEDIUM',
                'category': 'Credit Card Security',
                'action': 'Monitor high-value transactions more closely',
                'impact': 'Catch large fraud attempts early',
                'timeline': '1 week'
            }
        ])
    
    elif dataset_type == 'onlinefraud':
        recommendations.extend([
            {
                'priority': 'MEDIUM',
                'category': 'Online Payment Security',
                'action': 'Enhanced monitoring for cash-out transactions',
                'impact': 'Reduce money laundering risks',
                'timeline': '2 weeks'
            }
        ])
    
    # General recommendations
    recommendations.extend([
        {
            'priority': 'LOW',
            'category': 'Continuous Improvement',
            'action': 'Implement real-time fraud monitoring',
            'impact': 'Prevent fraud in real-time vs post-transaction',
            'estimated_savings': '90% faster fraud detection',
            'timeline': '1 month'
        },
        {
            'priority': 'LOW',
            'category': 'Analytics',
            'action': 'Set up automated fraud trend analysis',
            'impact': 'Proactive fraud pattern detection',
            'timeline': '2-3 weeks'
        }
    ])
    
    return recommendations

@enterprise_multi_bp.route('/upload-dataset', methods=['POST'])
def upload_dataset():
    """Upload dataset for advanced fraud analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        customer_id = request.form.get('customer_id', 'enterprise_customer')
        dataset_type = request.form.get('dataset_type', None)  # auto-detect if None
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        if not file.filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS:
            return jsonify({'error': 'Invalid file format. Use CSV, JSON, or XLSX'}), 400
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(f"{job_id}_{file.filename}")
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Initialize job tracking
        active_jobs[job_id] = {
            'status': 'queued',
            'progress': 0,
            'customer_id': customer_id,
            'filename': file.filename,
            'dataset_type': dataset_type,
            'created_at': datetime.now(),
            'file_path': file_path
        }
        
        # Start background processing
        thread = threading.Thread(
            target=analyze_transactions_batch,
            args=(job_id, file_path, customer_id, dataset_type)
        )
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'message': 'Dataset uploaded successfully. Analysis started.',
            'estimated_time': '5-15 minutes depending on dataset size',
            'dataset_type': dataset_type or 'auto-detect'
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@enterprise_multi_bp.route('/analysis-status/<job_id>', methods=['GET'])
def get_analysis_status(job_id):
    """Get analysis status and results"""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = active_jobs[job_id]
    
    response = {
        'job_id': job_id,
        'status': job['status'],
        'progress': job['progress'],
        'customer_id': job['customer_id'],
        'dataset_type': job.get('dataset_type', 'unknown'),
        'created_at': job['created_at'].isoformat()
    }
    
    if job['status'] == 'completed':
        response.update({
            'download_url': f'/api/enterprise-multi/download-report/{job_id}',
            'completed_at': job['completed_at'].isoformat(),
            'total_transactions': job.get('total_transactions', 0),
            'fraud_detected': job.get('fraud_detected', 0),
            'fraud_rate': job.get('fraud_rate', 0)
        })
    elif job['status'] == 'failed':
        response['error'] = job.get('error', 'Unknown error')
    
    return jsonify(response)

@enterprise_multi_bp.route('/download-report/<job_id>', methods=['GET'])
def download_report(job_id):
    """Download comprehensive fraud analysis report"""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = active_jobs[job_id]
    
    if job['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed yet'}), 400
    
    report_filename = job.get('report_file')
    if not report_filename:
        return jsonify({'error': 'Report file not found'}), 404
    
    report_path = os.path.join(REPORTS_FOLDER, report_filename)
    
    if not os.path.exists(report_path):
        return jsonify({'error': 'Report file missing'}), 404
    
    return send_file(
        report_path,
        as_attachment=True,
        download_name=f'enterprise_fraud_analysis_{job_id}.json',
        mimetype='application/json'
    )

@enterprise_multi_bp.route('/predict-single', methods=['POST'])
def predict_single_transaction():
    """Predict fraud for a single transaction"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No transaction data provided'}), 400
        
        transaction_data = data.get('transaction', {})
        dataset_type = data.get('dataset_type', 'auto')
        
        # Initialize detector
        detector = initialize_fraud_detector()
        
        # Make prediction
        result = detector.predict_fraud(transaction_data, dataset_type)
        
        return jsonify({
            'success': True,
            'prediction': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

@enterprise_multi_bp.route('/model-status', methods=['GET'])
def get_model_status():
    """Get current model status and performance"""
    detector = initialize_fraud_detector()
    
    available_models = list(detector.models.keys()) if detector else []
    model_performance = detector.model_performance if detector else {}
    
    return jsonify({
        'models_loaded': len(available_models),
        'available_models': available_models,
        'model_performance': model_performance,
        'supported_datasets': ['upi', 'creditcard', 'onlinefraud'],
        'status': 'ready' if available_models else 'training'
    })

@enterprise_multi_bp.route('/demo-enterprise', methods=['GET'])
def demo_enterprise_page():
    """Enterprise demo page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FraudGuard Enterprise - Multi-Dataset Analysis</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }
            .upload-section { background: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .dataset-info { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .dataset-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .dataset-card h3 { color: #667eea; margin-top: 0; }
            .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; border-radius: 8px; margin: 20px 0; transition: border-color 0.3s; }
            .upload-area:hover { border-color: #667eea; }
            .upload-area.dragover { border-color: #667eea; background: #f0f4ff; }
            .btn { background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; transition: background 0.3s; }
            .btn:hover { background: #5a67d8; }
            .btn:disabled { background: #ccc; cursor: not-allowed; }
            .progress-section { background: white; padding: 20px; border-radius: 8px; margin-top: 20px; display: none; }
            .progress-bar { width: 100%; height: 8px; background: #f0f0f0; border-radius: 4px; margin: 10px 0; }
            .progress-fill { height: 100%; background: #28a745; border-radius: 4px; width: 0%; transition: width 0.3s; }
            .status-text { margin: 10px 0; padding: 10px; border-radius: 4px; }
            .status-processing { background: #fff3cd; color: #856404; }
            .status-completed { background: #d4edda; color: #155724; }
            .status-failed { background: #f8d7da; color: #721c24; }
            .results-section { background: white; padding: 20px; border-radius: 8px; margin-top: 20px; display: none; }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
            .form-group select, .form-group input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ FraudGuard Enterprise</h1>
                <p>Advanced Multi-Dataset Fraud Detection for Banks & Fintech</p>
            </div>
            
            <div class="dataset-info">
                <div class="dataset-card">
                    <h3>🏦 UPI Transactions</h3>
                    <p><strong>Best for:</strong> Indian UPI payments, P2P transfers, merchant payments</p>
                    <p><strong>Features:</strong> Bank details, state analysis, device tracking, time patterns</p>
                    <p><strong>Sample size:</strong> 250,000+ transactions</p>
                </div>
                <div class="dataset-card">
                    <h3>💳 Credit Card Fraud</h3>
                    <p><strong>Best for:</strong> Credit card transactions, PCI-compliant analysis</p>
                    <p><strong>Features:</strong> Anonymized PCA features (V1-V28), amount analysis</p>
                    <p><strong>Sample size:</strong> 284,000+ transactions</p>
                </div>
                <div class="dataset-card">
                    <h3>🌐 Online Payments</h3>
                    <p><strong>Best for:</strong> Digital wallets, online transfers, balance analysis</p>
                    <p><strong>Features:</strong> Balance tracking, merchant analysis, transaction flows</p>
                    <p><strong>Sample size:</strong> 6.3M+ transactions</p>
                </div>
            </div>
            
            <div class="upload-section">
                <h2>Upload Your Transaction Dataset</h2>
                
                <div class="form-group">
                    <label>Customer ID:</label>
                    <input type="text" id="customerId" value="enterprise_demo" placeholder="Enter your customer ID">
                </div>
                
                <div class="form-group">
                    <label>Dataset Type:</label>
                    <select id="datasetType">
                        <option value="">Auto-detect from columns</option>
                        <option value="upi">UPI Transactions</option>
                        <option value="creditcard">Credit Card Transactions</option>
                        <option value="onlinefraud">Online Payment Transactions</option>
                    </select>
                </div>
                
                <div class="upload-area" id="uploadArea">
                    <h3>📁 Drop your CSV/Excel file here</h3>
                    <p>or click to browse (max 500MB)</p>
                    <input type="file" id="fileInput" accept=".csv,.xlsx,.json" style="display: none;">
                    <button class="btn" onclick="document.getElementById('fileInput').click()">Choose File</button>
                </div>
                
                <div style="margin-top: 20px;">
                    <button class="btn" id="uploadBtn" onclick="uploadDataset()" disabled>Start Analysis</button>
                </div>
            </div>
            
            <div class="progress-section" id="progressSection">
                <h3>Analysis Progress</h3>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="status-text" id="statusText">Initializing...</div>
            </div>
            
            <div class="results-section" id="resultsSection">
                <h3>Analysis Results</h3>
                <div id="resultsContent"></div>
                <button class="btn" id="downloadBtn" onclick="downloadReport()" style="display: none;">Download Full Report</button>
            </div>
        </div>
        
        <script>
            let currentJobId = null;
            let selectedFile = null;
            
            // File input handling
            document.getElementById('fileInput').addEventListener('change', function(e) {
                selectedFile = e.target.files[0];
                updateUploadArea();
            });
            
            // Drag and drop handling
            const uploadArea = document.getElementById('uploadArea');
            uploadArea.addEventListener('dragover', function(e) {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', function(e) {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', function(e) {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                selectedFile = e.dataTransfer.files[0];
                updateUploadArea();
            });
            
            function updateUploadArea() {
                if (selectedFile) {
                    document.getElementById('uploadArea').innerHTML = `
                        <h3>✅ File Selected</h3>
                        <p><strong>${selectedFile.name}</strong> (${(selectedFile.size/1024/1024).toFixed(2)} MB)</p>
                        <button class="btn" onclick="document.getElementById('fileInput').click()">Change File</button>
                    `;
                    document.getElementById('uploadBtn').disabled = false;
                }
            }
            
            function uploadDataset() {
                if (!selectedFile) {
                    alert('Please select a file first');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('customer_id', document.getElementById('customerId').value);
                formData.append('dataset_type', document.getElementById('datasetType').value);
                
                document.getElementById('progressSection').style.display = 'block';
                document.getElementById('uploadBtn').disabled = true;
                
                fetch('/api/enterprise-multi/upload-dataset', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.job_id) {
                        currentJobId = data.job_id;
                        updateStatus('Analysis started...', 'processing');
                        checkProgress();
                    } else {
                        updateStatus('Upload failed: ' + data.error, 'failed');
                    }
                })
                .catch(error => {
                    updateStatus('Upload error: ' + error, 'failed');
                });
            }
            
            function checkProgress() {
                if (!currentJobId) return;
                
                fetch(`/api/enterprise-multi/analysis-status/${currentJobId}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('progressFill').style.width = data.progress + '%';
                    
                    if (data.status === 'completed') {
                        updateStatus(`Analysis completed! Fraud detected: ${data.fraud_detected} transactions (${data.fraud_rate.toFixed(2)}%)`, 'completed');
                        showResults(data);
                        document.getElementById('downloadBtn').style.display = 'inline-block';
                    } else if (data.status === 'failed') {
                        updateStatus('Analysis failed: ' + data.error, 'failed');
                    } else {
                        updateStatus(`Processing... ${data.progress}%`, 'processing');
                        setTimeout(checkProgress, 2000);
                    }
                })
                .catch(error => {
                    console.error('Progress check error:', error);
                    setTimeout(checkProgress, 5000);
                });
            }
            
            function updateStatus(message, type) {
                const statusEl = document.getElementById('statusText');
                statusEl.textContent = message;
                statusEl.className = 'status-text status-' + type;
            }
            
            function showResults(data) {
                const resultsEl = document.getElementById('resultsContent');
                resultsEl.innerHTML = `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px;">
                        <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                            <h4>Total Transactions</h4>
                            <h2 style="color: #667eea; margin: 0;">${data.total_transactions.toLocaleString()}</h2>
                        </div>
                        <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                            <h4>Fraud Detected</h4>
                            <h2 style="color: #dc3545; margin: 0;">${data.fraud_detected}</h2>
                        </div>
                        <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                            <h4>Fraud Rate</h4>
                            <h2 style="color: #fd7e14; margin: 0;">${data.fraud_rate.toFixed(2)}%</h2>
                        </div>
                        <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                            <h4>Dataset Type</h4>
                            <h2 style="color: #28a745; margin: 0;">${data.dataset_type.toUpperCase()}</h2>
                        </div>
                    </div>
                    <p style="color: #666;">Complete analysis report with recommendations available for download.</p>
                `;
                document.getElementById('resultsSection').style.display = 'block';
            }
            
            function downloadReport() {
                if (currentJobId) {
                    window.open(`/api/enterprise-multi/download-report/${currentJobId}`, '_blank');
                }
            }
        </script>
    </body>
    </html>
    """
    return html

# Initialize detector on module load
initialize_fraud_detector()

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(enterprise_multi_bp, url_prefix='/api/enterprise-multi')
    app.run(debug=True, port=5003)
