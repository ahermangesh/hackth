#!/usr/bin/env python3
"""
Universal Fraud Detection API
Accepts any CSV upload and automatically detects format and analyzes fraud
"""

from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import uuid
import os
import threading
import time

# Import the detector class only when needed to avoid circular imports
UniversalFraudDetector = None

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Global storage for analysis results
analysis_results = {}
analysis_status = {}

def background_analysis(task_id, file_path):
    """Run fraud analysis in background"""
    try:
        analysis_status[task_id] = "Processing"
        
        # Import here to avoid circular import issues
        from universal_fraud_detector import UniversalFraudDetector
        
        detector = UniversalFraudDetector()
        results_df = detector.analyze_dataset(file_path, save_results=False)
        
        # Store results
        analysis_results[task_id] = {
            'dataset_type': detector.dataset_type,
            'total_transactions': len(results_df),
            'fraud_detected': int(results_df['fraud_prediction'].sum()),
            'fraud_rate': float(results_df['fraud_prediction'].mean() * 100),
            'high_risk_count': int((results_df['fraud_probability'] > 0.7).sum()),
            'top_fraud_cases': results_df[results_df['fraud_prediction'] == 1].nlargest(10, 'fraud_probability').to_dict('records'),
            'summary_stats': {
                'columns': len(results_df.columns),
                'avg_fraud_probability': float(results_df['fraud_probability'].mean()),
                'max_fraud_probability': float(results_df['fraud_probability'].max())
            }
        }
        
        # Calculate total fraud amount if amount column exists
        amount_cols = [col for col in results_df.columns if any(word in col.lower() for word in ['amount', 'amt', 'value'])]
        if amount_cols:
            amount_col = amount_cols[0]
            fraud_amount = float(results_df[results_df['fraud_prediction'] == 1][amount_col].sum())
            analysis_results[task_id]['total_fraud_amount'] = fraud_amount
        
        analysis_status[task_id] = "Completed"
        
        # Clean up file
        os.remove(file_path)
        
    except Exception as e:
        analysis_status[task_id] = f"Error: {str(e)}"

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Universal Fraud Detection</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px; }
        .upload-area { border: 3px dashed #667eea; border-radius: 10px; padding: 40px; text-align: center; margin-bottom: 30px; }
        .upload-area:hover { background-color: #f0f0f0; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .feature-card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .result-section { display: none; margin-top: 30px; padding: 20px; background-color: #f9f9f9; border-radius: 8px; }
        .fraud-item { background: #fff; border-left: 4px solid #e74c3c; margin: 10px 0; padding: 10px; border-radius: 4px; }
        .btn { background-color: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .btn:hover { background-color: #5a6fd8; }
        .progress { width: 100%; height: 20px; background-color: #f0f0f0; border-radius: 10px; overflow: hidden; }
        .progress-bar { height: 100%; background-color: #667eea; width: 0%; transition: width 0.3s; }
        .status { margin: 20px 0; padding: 15px; border-radius: 5px; }
        .status.processing { background-color: #fff3cd; border: 1px solid #ffeaa7; }
        .status.completed { background-color: #d1f2eb; border: 1px solid #a3e4d7; }
        .status.error { background-color: #f8d7da; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌟 Universal Fraud Detection System</h1>
        <p>Upload ANY fraud dataset - we'll automatically detect the format and find fraud!</p>
    </div>

    <div class="feature-grid">
        <div class="feature-card">
            <h3>🧠 Auto-Detection</h3>
            <p>Automatically detects your data format:</p>
            <ul>
                <li>UPI transactions</li>
                <li>Credit card (detailed)</li>
                <li>Credit card (PCA)</li>
                <li>Generic transaction data</li>
            </ul>
        </div>
        <div class="feature-card">
            <h3>🚀 Instant Analysis</h3>
            <p>Get comprehensive fraud analysis:</p>
            <ul>
                <li>Fraud detection rate</li>
                <li>Risk scoring</li>
                <li>Financial impact</li>
                <li>Detailed reporting</li>
            </ul>
        </div>
        <div class="feature-card">
            <h3>📊 Enterprise Ready</h3>
            <p>Production-grade capabilities:</p>
            <ul>
                <li>500MB file uploads</li>
                <li>Multiple data formats</li>
                <li>Real-time processing</li>
                <li>Detailed analytics</li>
            </ul>
        </div>
    </div>

    <div class="upload-area">
        <h3>📁 Upload Your Fraud Dataset</h3>
        <p>Supports CSV files up to 500MB</p>
        <input type="file" id="csvFile" accept=".csv" style="margin: 20px 0;">
        <br>
        <button class="btn" onclick="uploadFile()">🔍 Analyze for Fraud</button>
    </div>

    <div id="statusSection" class="status" style="display: none;">
        <div id="statusText"></div>
        <div class="progress">
            <div id="progressBar" class="progress-bar"></div>
        </div>
    </div>

    <div id="resultsSection" class="result-section">
        <h2>🚨 Fraud Detection Results</h2>
        <div id="resultsContent"></div>
    </div>

    <script>
        let taskId = null;

        function uploadFile() {
            const fileInput = document.getElementById('csvFile');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a CSV file');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            // Show status
            document.getElementById('statusSection').style.display = 'block';
            document.getElementById('statusText').innerHTML = '📤 Uploading file...';
            document.getElementById('progressBar').style.width = '20%';

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    taskId = data.task_id;
                    document.getElementById('statusText').innerHTML = '🧠 Analyzing data format and detecting fraud...';
                    document.getElementById('progressBar').style.width = '50%';
                    checkStatus();
                } else {
                    showError(data.message);
                }
            })
            .catch(error => {
                showError('Upload failed: ' + error.message);
            });
        }

        function checkStatus() {
            if (!taskId) return;

            fetch('/status/' + taskId)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'Processing') {
                    document.getElementById('statusText').innerHTML = '⚡ Processing fraud detection...';
                    document.getElementById('progressBar').style.width = '80%';
                    setTimeout(checkStatus, 2000);
                } else if (data.status === 'Completed') {
                    document.getElementById('statusText').innerHTML = '✅ Analysis completed!';
                    document.getElementById('progressBar').style.width = '100%';
                    document.getElementById('statusSection').className = 'status completed';
                    showResults();
                } else {
                    showError(data.status);
                }
            });
        }

        function showResults() {
            fetch('/results/' + taskId)
            .then(response => response.json())
            .then(data => {
                const resultsHtml = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">' +
                    '<div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db;">' +
                    '<h4>📊 Dataset Type</h4>' +
                    '<p style="font-size: 18px; margin: 0;">' + data.dataset_type + '</p>' +
                    '</div>' +
                    '<div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #e74c3c;">' +
                    '<h4>🚨 Fraud Detected</h4>' +
                    '<p style="font-size: 18px; margin: 0;">' + data.fraud_detected.toLocaleString() + ' cases</p>' +
                    '</div>' +
                    '<div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #f39c12;">' +
                    '<h4>📈 Fraud Rate</h4>' +
                    '<p style="font-size: 18px; margin: 0;">' + data.fraud_rate.toFixed(2) + '%</p>' +
                    '</div>' +
                    '<div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #27ae60;">' +
                    '<h4>📋 Total Transactions</h4>' +
                    '<p style="font-size: 18px; margin: 0;">' + data.total_transactions.toLocaleString() + '</p>' +
                    '</div>' +
                    '</div>';
                
                if (data.total_fraud_amount) {
                    resultsHtml += '<div style="background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #e74c3c;">' +
                        '<h4>💰 Total Fraud Amount</h4>' +
                        '<p style="font-size: 24px; margin: 0; color: #e74c3c;">$' + data.total_fraud_amount.toLocaleString() + '</p>' +
                        '</div>';
                }
                
                resultsHtml += '<h3>🔍 Top Fraud Cases</h3><div>';
                
                for (let i = 0; i < Math.min(10, data.top_fraud_cases.length); i++) {
                    const case_ = data.top_fraud_cases[i];
                    resultsHtml += '<div class="fraud-item">' +
                        '<strong>Case ' + (i + 1) + ':</strong> ' +
                        'Probability: ' + (case_.fraud_probability * 100).toFixed(1) + '%';
                    
                    if (case_.amt) resultsHtml += ' | Amount: $' + case_.amt;
                    if (case_['amount (INR)']) resultsHtml += ' | Amount: ₹' + case_['amount (INR)'];
                    if (case_.Amount) resultsHtml += ' | Amount: $' + case_.Amount;
                    
                    resultsHtml += '</div>';
                }
                
                resultsHtml += '</div>';
                
                document.getElementById('resultsContent').innerHTML = resultsHtml;
                document.getElementById('resultsSection').style.display = 'block';
            });
        }

        function showError(message) {
            document.getElementById('statusSection').className = 'status error';
            document.getElementById('statusText').innerHTML = '❌ ' + message;
        }
    </script>
</body>
</html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'})
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'Only CSV files are supported'})
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Save file temporarily
        upload_dir = 'temp_uploads'
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{task_id}.csv")
        file.save(file_path)
        
        # Start background analysis
        thread = threading.Thread(target=background_analysis, args=(task_id, file_path))
        thread.start()
        
        return jsonify({'status': 'success', 'task_id': task_id})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/status/<task_id>')
def get_status(task_id):
    status = analysis_status.get(task_id, 'Not found')
    return jsonify({'status': status})

@app.route('/results/<task_id>')
def get_results(task_id):
    if task_id in analysis_results:
        return jsonify(analysis_results[task_id])
    else:
        return jsonify({'error': 'Results not found'}), 404

if __name__ == '__main__':
    print("🌟 Starting Universal Fraud Detection API...")
    print("🔗 Upload any CSV at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
