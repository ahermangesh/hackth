#!/usr/bin/env python3
"""
Enterprise Batch Processing API
For banks and startups to upload transaction data for fraud analysis
"""

from flask import Blueprint, request, jsonify, send_file
import pandas as pd
import numpy as np
import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import threading
import time

enterprise_bp = Blueprint('enterprise', __name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
REPORTS_FOLDER = 'reports'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'csv', 'json'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

# Job tracking
active_jobs = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_batch_analysis(job_id, file_path, customer_id):
    """Process batch fraud analysis in background"""
    try:
        active_jobs[job_id]['status'] = 'processing'
        active_jobs[job_id]['progress'] = 10
        
        # Load data
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_json(file_path)
            
        active_jobs[job_id]['progress'] = 30
        active_jobs[job_id]['total_transactions'] = len(df)
        
        # Basic fraud analysis
        fraud_results = []
        
        for index, row in df.iterrows():
            # Simple rule-based fraud detection
            fraud_score = calculate_fraud_score(row)
            is_fraud = fraud_score > 0.5
            
            fraud_results.append({
                'transaction_id': row.get('transaction_id', f'TXN_{index}'),
                'amount': row.get('amount', 0),
                'fraud_score': fraud_score,
                'is_fraud': is_fraud,
                'risk_level': get_risk_level(fraud_score)
            })
            
            # Update progress
            progress = 30 + (index / len(df)) * 60
            active_jobs[job_id]['progress'] = min(progress, 90)
        
        # Generate comprehensive report
        report = generate_enterprise_report(df, fraud_results, customer_id)
        
        # Save report
        report_filename = f"fraud_analysis_{job_id}.json"
        report_path = os.path.join(REPORTS_FOLDER, report_filename)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Complete job
        active_jobs[job_id]['status'] = 'completed'
        active_jobs[job_id]['progress'] = 100
        active_jobs[job_id]['report_file'] = report_filename
        active_jobs[job_id]['completed_at'] = datetime.now()
        
    except Exception as e:
        active_jobs[job_id]['status'] = 'failed'
        active_jobs[job_id]['error'] = str(e)

def calculate_fraud_score(transaction):
    """Calculate fraud score for a transaction"""
    score = 0.0
    
    amount = transaction.get('amount', 0)
    
    # Amount-based scoring
    if amount > 100000:  # >1 lakh
        score += 0.4
    elif amount > 50000:  # >50k
        score += 0.2
    elif amount > 10000:  # >10k
        score += 0.1
    
    # Time-based scoring
    if 'timestamp' in transaction:
        try:
            timestamp = pd.to_datetime(transaction['timestamp'])
            hour = timestamp.hour
            if hour >= 22 or hour <= 5:  # Night time
                score += 0.2
        except:
            pass
    
    # Status-based scoring
    if transaction.get('status') == 'FAILED':
        score += 0.3
    
    # Type-based scoring
    transaction_type = transaction.get('transaction_type', '').lower()
    if 'transfer' in transaction_type:
        score += 0.1
    
    return min(score, 1.0)

def get_risk_level(score):
    """Convert fraud score to risk level"""
    if score >= 0.7:
        return 'HIGH'
    elif score >= 0.4:
        return 'MEDIUM'
    else:
        return 'LOW'

def generate_enterprise_report(df, fraud_results, customer_id):
    """Generate comprehensive enterprise fraud report"""
    total_transactions = len(df)
    fraud_transactions = sum(1 for r in fraud_results if r['is_fraud'])
    total_amount = df['amount'].sum() if 'amount' in df.columns else 0
    fraud_amount = sum(r['amount'] for r in fraud_results if r['is_fraud'])
    
    # Risk distribution
    risk_distribution = {}
    for result in fraud_results:
        risk_level = result['risk_level']
        risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
    
    # Top risky transactions
    top_risky = sorted(fraud_results, key=lambda x: x['fraud_score'], reverse=True)[:10]
    
    report = {
        'analysis_summary': {
            'customer_id': customer_id,
            'analysis_date': datetime.now().isoformat(),
            'total_transactions': total_transactions,
            'fraud_transactions': fraud_transactions,
            'fraud_rate': (fraud_transactions / total_transactions * 100) if total_transactions > 0 else 0,
            'total_amount': float(total_amount),
            'amount_at_risk': float(fraud_amount),
            'risk_percentage': (fraud_amount / total_amount * 100) if total_amount > 0 else 0
        },
        'risk_distribution': risk_distribution,
        'top_risky_transactions': top_risky,
        'recommendations': generate_recommendations(fraud_results),
        'detailed_results': fraud_results
    }
    
    return report

def generate_recommendations(fraud_results):
    """Generate actionable recommendations"""
    high_risk_count = sum(1 for r in fraud_results if r['risk_level'] == 'HIGH')
    medium_risk_count = sum(1 for r in fraud_results if r['risk_level'] == 'MEDIUM')
    
    recommendations = []
    
    if high_risk_count > 0:
        recommendations.append({
            'priority': 'HIGH',
            'action': f'Review {high_risk_count} high-risk transactions immediately',
            'impact': 'Prevent potential fraud losses'
        })
    
    if medium_risk_count > 0:
        recommendations.append({
            'priority': 'MEDIUM', 
            'action': f'Enhanced monitoring for {medium_risk_count} medium-risk transactions',
            'impact': 'Early fraud detection'
        })
    
    recommendations.append({
        'priority': 'LOW',
        'action': 'Implement real-time fraud monitoring for future transactions',
        'impact': 'Continuous fraud prevention'
    })
    
    return recommendations

@enterprise_bp.route('/upload-batch', methods=['POST'])
def upload_batch():
    """Upload batch of transactions for fraud analysis"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        customer_id = request.form.get('customer_id', 'demo_customer')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format. Use CSV or JSON'}), 400
        
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
            'created_at': datetime.now(),
            'file_path': file_path
        }
        
        # Start background processing
        thread = threading.Thread(
            target=process_batch_analysis, 
            args=(job_id, file_path, customer_id)
        )
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'message': 'File uploaded successfully. Processing started.',
            'estimated_time': '2-5 minutes'
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@enterprise_bp.route('/analysis/<job_id>', methods=['GET'])
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
        'created_at': job['created_at'].isoformat()
    }
    
    if job['status'] == 'completed':
        response['download_url'] = f'/api/enterprise/download/{job_id}'
        response['completed_at'] = job['completed_at'].isoformat()
        response['total_transactions'] = job.get('total_transactions', 0)
    elif job['status'] == 'failed':
        response['error'] = job.get('error', 'Unknown error')
    
    return jsonify(response)

@enterprise_bp.route('/download/<job_id>', methods=['GET'])
def download_report(job_id):
    """Download fraud analysis report"""
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
        download_name=f'fraud_analysis_{job_id}.json',
        mimetype='application/json'
    )

@enterprise_bp.route('/demo-upload', methods=['GET'])
def demo_upload_page():
    """Demo upload page for testing"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enterprise Fraud Detection - Batch Upload</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
            .upload-area:hover { border-color: #007bff; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .progress { width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; margin: 10px 0; }
            .progress-bar { height: 100%; background: #28a745; border-radius: 10px; width: 0%; transition: width 0.3s; }
        </style>
    </head>
    <body>
        <h1>🏦 Enterprise Fraud Detection</h1>
        <h2>Batch Transaction Analysis</h2>
        
        <div class="upload-area">
            <h3>Upload Transaction Data</h3>
            <p>Upload CSV or JSON file (max 100MB)</p>
            <input type="file" id="fileInput" accept=".csv,.json">
            <br><br>
            <input type="text" id="customerId" placeholder="Customer ID" value="demo_bank">
            <br><br>
            <button onclick="uploadFile()">Analyze Transactions</button>
        </div>
        
        <div id="status" style="display:none;">
            <h3>Analysis Status</h3>
            <div class="progress">
                <div class="progress-bar" id="progressBar"></div>
            </div>
            <p id="statusText">Uploading...</p>
            <div id="downloadLink" style="display:none;">
                <button onclick="downloadReport()">Download Report</button>
            </div>
        </div>
        
        <script>
            let currentJobId = null;
            
            function uploadFile() {
                const fileInput = document.getElementById('fileInput');
                const customerId = document.getElementById('customerId').value;
                
                if (!fileInput.files[0]) {
                    alert('Please select a file');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('customer_id', customerId);
                
                document.getElementById('status').style.display = 'block';
                document.getElementById('statusText').textContent = 'Uploading...';
                
                fetch('/api/enterprise/upload-batch', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.job_id) {
                        currentJobId = data.job_id;
                        checkStatus();
                    } else {
                        alert('Upload failed: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Upload error: ' + error);
                });
            }
            
            function checkStatus() {
                if (!currentJobId) return;
                
                fetch(`/api/enterprise/analysis/${currentJobId}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('statusText').textContent = 
                        `Status: ${data.status} (${data.progress}%)`;
                    document.getElementById('progressBar').style.width = data.progress + '%';
                    
                    if (data.status === 'completed') {
                        document.getElementById('downloadLink').style.display = 'block';
                    } else if (data.status === 'failed') {
                        alert('Analysis failed: ' + data.error);
                    } else {
                        setTimeout(checkStatus, 2000);
                    }
                })
                .catch(error => {
                    console.error('Status check error:', error);
                    setTimeout(checkStatus, 5000);
                });
            }
            
            function downloadReport() {
                if (currentJobId) {
                    window.open(`/api/enterprise/download/${currentJobId}`, '_blank');
                }
            }
        </script>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(enterprise_bp, url_prefix='/api/enterprise')
    app.run(debug=True, port=5001)
