#!/usr/bin/env python3
"""
Minimal Universal Fraud Detection API - Working Version
"""

from flask import Flask, request, jsonify
import pandas as pd
import uuid
import os
import threading
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

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
            'avg_fraud_probability': float(results_df['fraud_probability'].mean()),
            'max_fraud_probability': float(results_df['fraud_probability'].max())
        }
        
        # Calculate total fraud amount if amount column exists
        amount_cols = [col for col in results_df.columns if any(word in col.lower() for word in ['amount', 'amt', 'value'])]
        if amount_cols:
            amount_col = amount_cols[0]
            fraud_amount = float(results_df[results_df['fraud_prediction'] == 1][amount_col].sum())
            analysis_results[task_id]['total_fraud_amount'] = fraud_amount
        
        analysis_status[task_id] = "Completed"
        
        # Clean up file
        if os.path.exists(file_path):
            os.remove(file_path)
        
    except Exception as e:
        analysis_status[task_id] = f"Error: {str(e)}"
        print(f"Analysis error: {e}")

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Universal Fraud Detection</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: #667eea; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }
        .upload-area { border: 2px dashed #667eea; padding: 30px; text-align: center; margin: 20px 0; border-radius: 8px; }
        .btn { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        .results { margin-top: 20px; padding: 20px; background: #f0f0f0; border-radius: 8px; display: none; }
        .status { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .processing { background: #fff3cd; }
        .completed { background: #d1f2eb; }
        .error { background: #f8d7da; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌟 Universal Fraud Detection System</h1>
        <p>Upload any CSV file for automatic fraud detection</p>
    </div>

    <div class="upload-area">
        <h3>📁 Upload CSV File</h3>
        <input type="file" id="csvFile" accept=".csv">
        <br><br>
        <button class="btn" onclick="uploadFile()">🔍 Analyze for Fraud</button>
    </div>

    <div id="statusDiv" class="status" style="display: none;"></div>
    <div id="resultsDiv" class="results"></div>

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

            document.getElementById('statusDiv').style.display = 'block';
            document.getElementById('statusDiv').className = 'status processing';
            document.getElementById('statusDiv').innerHTML = '📤 Uploading file...';

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    taskId = data.task_id;
                    document.getElementById('statusDiv').innerHTML = '🧠 Analyzing fraud patterns...';
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
                    document.getElementById('statusDiv').innerHTML = '⚡ Processing fraud detection...';
                    setTimeout(checkStatus, 2000);
                } else if (data.status === 'Completed') {
                    document.getElementById('statusDiv').className = 'status completed';
                    document.getElementById('statusDiv').innerHTML = '✅ Analysis completed!';
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
                let html = '<h2>🚨 Fraud Detection Results</h2>';
                html += '<p><strong>Dataset Type:</strong> ' + data.dataset_type + '</p>';
                html += '<p><strong>Total Transactions:</strong> ' + data.total_transactions.toLocaleString() + '</p>';
                html += '<p><strong>Fraud Cases Detected:</strong> ' + data.fraud_detected + '</p>';
                html += '<p><strong>Fraud Rate:</strong> ' + data.fraud_rate.toFixed(2) + '%</p>';
                
                if (data.total_fraud_amount) {
                    html += '<p><strong>Total Fraud Amount:</strong> $' + data.total_fraud_amount.toLocaleString() + '</p>';
                }
                
                html += '<p><strong>High Risk Transactions:</strong> ' + data.high_risk_count + '</p>';
                
                document.getElementById('resultsDiv').innerHTML = html;
                document.getElementById('resultsDiv').style.display = 'block';
            });
        }

        function showError(message) {
            document.getElementById('statusDiv').className = 'status error';
            document.getElementById('statusDiv').innerHTML = '❌ ' + message;
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

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Universal Fraud Detection API is running'})

if __name__ == '__main__':
    print("🌟 Starting Minimal Universal Fraud Detection API...")
    print("🔗 Upload interface: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
