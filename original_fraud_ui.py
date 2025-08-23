#!/usr/bin/env python3
"""
FraudGuard Enterprise API - Original Beautiful UI/UX
"""

from flask import Flask, request, jsonify
import pandas as pd
import uuid
import os
import threading
import time
import traceback

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Global storage for analysis results
analysis_results = {}
analysis_status = {}

def background_analysis(task_id, file_path):
    """Run fraud analysis in background"""
    try:
        analysis_status[task_id] = "Processing"
        print(f"Starting analysis for task {task_id}")
        
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
            'top_fraud_cases': results_df[results_df['fraud_prediction'] == 1].nlargest(5, 'fraud_probability').to_dict('records'),
        }
        
        # Calculate total fraud amount if amount column exists
        amount_cols = [col for col in results_df.columns if any(word in col.lower() for word in ['amount', 'amt', 'value'])]
        if amount_cols:
            amount_col = amount_cols[0]
            fraud_amount = float(results_df[results_df['fraud_prediction'] == 1][amount_col].sum())
            analysis_results[task_id]['total_fraud_amount'] = fraud_amount
        
        analysis_status[task_id] = "Completed"
        print(f"Analysis completed for task {task_id}")
        
        # Clean up file
        if os.path.exists(file_path):
            os.remove(file_path)
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        analysis_status[task_id] = error_msg
        print(f"Analysis failed for task {task_id}: {error_msg}")
        print(traceback.format_exc())

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>FraudGuard Enterprise - AI Fraud Detection</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
        .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 100px 0; text-align: center; }
        .hero h1 { font-size: 3.5em; margin-bottom: 20px; }
        .hero p { font-size: 1.3em; margin-bottom: 40px; opacity: 0.9; }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        .features { padding: 80px 0; background: #f8f9fa; }
        .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 40px; margin-top: 50px; }
        .feature-card { background: white; padding: 40px 30px; border-radius: 15px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.1); transition: transform 0.3s; }
        .feature-card:hover { transform: translateY(-10px); }
        .feature-icon { font-size: 3em; margin-bottom: 20px; }
        .btn { background: #667eea; color: white; padding: 15px 30px; border: none; border-radius: 25px; font-size: 1.1em; cursor: pointer; margin: 10px; text-decoration: none; display: inline-block; transition: background 0.3s; }
        .btn:hover { background: #5a67d8; }
        .btn-secondary { background: white; color: #667eea; border: 2px solid #667eea; }
        .btn-secondary:hover { background: #667eea; color: white; }
        .stats { padding: 60px 0; text-align: center; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; margin-top: 40px; }
        .stat-item h3 { font-size: 3em; color: #667eea; margin-bottom: 10px; }
        .cta { background: #667eea; color: white; padding: 80px 0; text-align: center; }
        .footer { background: #2d3748; color: white; padding: 40px 0; text-align: center; }
        
        /* Upload section styles */
        .upload-section { background: white; margin: 50px auto; max-width: 800px; border-radius: 15px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .upload-area { border: 3px dashed #667eea; border-radius: 15px; padding: 40px; text-align: center; background: #f8f9ff; transition: all 0.3s; }
        .upload-area:hover { background: #f0f3ff; transform: scale(1.02); }
        .upload-area.dragover { background: #e8f2ff; border-color: #5a67d8; }
        .file-input { margin: 20px 0; padding: 15px; border: 2px solid #ddd; border-radius: 10px; font-size: 16px; width: 300px; }
        .btn-upload { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .btn-test { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); }
        
        /* Status and results */
        .status { margin: 30px 0; padding: 25px; border-radius: 15px; display: none; }
        .status.processing { background: #fff3cd; border: 3px solid #ffc107; color: #856404; }
        .status.completed { background: #d1f2eb; border: 3px solid #28a745; color: #155724; }
        .status.error { background: #f8d7da; border: 3px solid #dc3545; color: #721c24; }
        .progress { width: 100%; height: 25px; background: #e9ecef; border-radius: 15px; overflow: hidden; margin: 15px 0; }
        .progress-bar { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); width: 0%; transition: width 0.5s ease; }
        .results { background: white; border-radius: 15px; padding: 30px; margin: 30px auto; max-width: 1000px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); display: none; }
        .result-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
        .result-card { background: #f8f9fa; padding: 25px; border-radius: 15px; text-align: center; border-left: 5px solid #667eea; }
        .result-card h4 { margin-bottom: 10px; color: #333; }
        .result-card .number { font-size: 2.5em; font-weight: bold; color: #667eea; }
        .fraud-item { background: #fff5f5; border-left: 4px solid #e74c3c; margin: 15px 0; padding: 20px; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="hero">
        <div class="container">
            <h1>🛡️ FraudGuard Enterprise</h1>
            <p>AI-Powered Fraud Detection for Banks, Fintech Startups & Payment Processors</p>
            <button class="btn" onclick="scrollToUpload()">Try Demo Upload</button>
            <button class="btn btn-secondary" onclick="scrollToPricing()">View Pricing</button>
        </div>
    </div>
    
    <!-- Upload Section -->
    <div class="upload-section" id="uploadSection">
        <h2 style="text-align: center; margin-bottom: 30px; color: #667eea;">🔍 Upload & Analyze Fraud Data</h2>
        <p style="text-align: center; margin-bottom: 30px; color: #666;">Upload any CSV transaction file - our AI automatically detects format and finds fraud</p>
        
        <div class="upload-area" id="uploadArea">
            <h3>📁 Drop your CSV file here or click to browse</h3>
            <p style="margin: 20px 0; color: #666;">Supports: UPI, Credit Card, Generic Transaction Data (up to 500MB)</p>
            <input type="file" id="csvFile" accept=".csv" class="file-input">
            <br>
            <button class="btn btn-upload" id="uploadBtn" onclick="uploadFile()">📤 Upload File</button>
            <button class="btn btn-test" id="testBtn" onclick="testUploadedFile()" style="display:none;">⚡ Analyze for Fraud</button>
        </div>
        
        <div id="statusSection" class="status">
            <div id="statusText"></div>
            <div class="progress">
                <div id="progressBar" class="progress-bar"></div>
            </div>
        </div>
    </div>
    
    <div id="resultsSection" class="results">
        <h2 style="text-align: center; margin-bottom: 30px;">🚨 Fraud Detection Results</h2>
        <div id="resultsContent"></div>
    </div>
    
    <div class="features">
        <div class="container">
            <h2 style="text-align: center; font-size: 2.5em; margin-bottom: 20px;">Why Choose FraudGuard?</h2>
            <p style="text-align: center; font-size: 1.2em; color: #666; max-width: 800px; margin: 0 auto;">
                Advanced machine learning models trained on multiple datasets to catch fraud patterns that traditional systems miss.
            </p>
            
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🎯</div>
                    <h3>Multi-Dataset Support</h3>
                    <p>Supports UPI transactions, credit card payments, and online transfers. Auto-detects transaction type and applies the best model.</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <h3>Real-Time Detection</h3>
                    <p>Sub-second fraud scoring for real-time transaction processing. Prevent fraud before it happens.</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">🧠</div>
                    <h3>Explainable AI</h3>
                    <p>Understand why transactions are flagged. Get detailed insights and actionable recommendations.</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">💰</div>
                    <h3>Cost-Effective</h3>
                    <p>Starting at ₹99/month. 90% cheaper than enterprise solutions with better accuracy.</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">🔒</div>
                    <h3>Enterprise Security</h3>
                    <p>Bank-grade security, compliance ready. Data encryption, audit logs, and access controls.</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">🚀</div>
                    <h3>Quick Setup</h3>
                    <p>5-minute integration. Upload your data, get fraud reports instantly. No complex setup required.</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="stats">
        <div class="container">
            <h2 style="font-size: 2.5em; margin-bottom: 20px;">Proven Results</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <h3>95%+</h3>
                    <p>Fraud Detection Accuracy</p>
                </div>
                <div class="stat-item">
                    <h3>&lt;2%</h3>
                    <p>False Positive Rate</p>
                </div>
                <div class="stat-item">
                    <h3>&lt;100ms</h3>
                    <p>Average Response Time</p>
                </div>
                <div class="stat-item">
                    <h3>₹10L+</h3>
                    <p>Fraud Prevented Monthly</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="cta" id="pricingSection">
        <div class="container">
            <h2 style="margin-bottom: 20px;">Enterprise Pricing</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; margin: 40px 0;">
                <div style="background: white; color: #333; padding: 30px; border-radius: 15px;">
                    <h3 style="color: #667eea; margin-bottom: 15px;">Starter</h3>
                    <div style="font-size: 2.5em; font-weight: bold; color: #667eea;">₹99<span style="font-size: 0.4em;">/month</span></div>
                    <p style="margin: 20px 0;">Up to 10,000 transactions/month</p>
                </div>
                <div style="background: white; color: #333; padding: 30px; border-radius: 15px; transform: scale(1.05); border: 3px solid #667eea;">
                    <h3 style="color: #667eea; margin-bottom: 15px;">Professional</h3>
                    <div style="font-size: 2.5em; font-weight: bold; color: #667eea;">₹499<span style="font-size: 0.4em;">/month</span></div>
                    <p style="margin: 20px 0;">Up to 100,000 transactions/month</p>
                </div>
                <div style="background: white; color: #333; padding: 30px; border-radius: 15px;">
                    <h3 style="color: #667eea; margin-bottom: 15px;">Enterprise</h3>
                    <div style="font-size: 2.5em; font-weight: bold; color: #667eea;">₹1,999<span style="font-size: 0.4em;">/month</span></div>
                    <p style="margin: 20px 0;">Unlimited transactions</p>
                </div>
            </div>
            <p style="margin-bottom: 30px; font-size: 1.2em;">Join leading fintech companies using FraudGuard to protect their customers</p>
            <button class="btn btn-secondary" onclick="alert('Contact sales@fraudguard.ai for free trial!')">Start Free Trial</button>
            <button class="btn" onclick="alert('Email: contact@fraudguard.ai')">Contact Sales</button>
        </div>
    </div>
    
    <div class="footer">
        <div class="container">
            <p>&copy; 2025 FraudGuard Enterprise. AI-Powered Fraud Detection for the Digital Age.</p>
            <p style="margin-top: 10px; opacity: 0.8;">Upload your fraud dataset above to see our AI in action!</p>
        </div>
    </div>

    <script>
        let taskId = null;
        let lastUploadedFile = null;

        // Smooth scrolling
        function scrollToUpload() {
            document.getElementById('uploadSection').scrollIntoView({ behavior: 'smooth' });
        }
        
        function scrollToPricing() {
            document.getElementById('pricingSection').scrollIntoView({ behavior: 'smooth' });
        }

        // Drag and drop functionality
        const uploadArea = document.getElementById('uploadArea');
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('csvFile').files = files;
                uploadFile();
            }
        });

        function uploadFile() {
            const fileInput = document.getElementById('csvFile');
            const file = fileInput.files[0];
            const uploadBtn = document.getElementById('uploadBtn');
            const testBtn = document.getElementById('testBtn');
            
            console.log('Starting upload process');
            
            if (!file) {
                alert('Please select a CSV file first!');
                return;
            }

            if (!file.name.toLowerCase().endsWith('.csv')) {
                alert('Please select a CSV file!');
                return;
            }

            // Store file info for testing later
            lastUploadedFile = file.name;
            
            // Disable upload button, show test button
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '⏳ Uploading...';
            testBtn.style.display = 'inline-block';
            
            // Show status
            const statusSection = document.getElementById('statusSection');
            statusSection.style.display = 'block';
            statusSection.className = 'status processing';
            document.getElementById('statusText').innerHTML = '📤 Uploading: ' + file.name + ' (' + (file.size / (1024*1024)).toFixed(1) + ' MB)';
            document.getElementById('progressBar').style.width = '25%';

            const formData = new FormData();
            formData.append('file', file);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                console.log('Upload response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Upload response:', data);
                if (data.status === 'success') {
                    taskId = data.task_id;
                    document.getElementById('statusText').innerHTML = '✅ Upload successful! Click "Analyze for Fraud" to start detection.';
                    document.getElementById('progressBar').style.width = '100%';
                    statusSection.className = 'status completed';
                    
                    // Re-enable upload button for new files
                    uploadBtn.disabled = false;
                    uploadBtn.innerHTML = '📁 Upload Another File';
                } else {
                    showError(data.message || 'Upload failed');
                }
            })
            .catch(error => {
                console.error('Upload error:', error);
                showError('Upload failed: ' + error.message);
            });
        }

        function testUploadedFile() {
            if (!taskId) {
                alert('Please upload a file first!');
                return;
            }

            const testBtn = document.getElementById('testBtn');
            testBtn.disabled = true;
            testBtn.innerHTML = '⚡ Analyzing...';

            // Show analysis status
            const statusSection = document.getElementById('statusSection');
            statusSection.style.display = 'block';
            statusSection.className = 'status processing';
            document.getElementById('statusText').innerHTML = '🧠 Auto-detecting format and analyzing fraud patterns...';
            document.getElementById('progressBar').style.width = '50%';

            // Start background analysis by checking status
            setTimeout(checkStatus, 1000);
        }

        function checkStatus() {
            if (!taskId) return;

            console.log('Checking status for task:', taskId);

            fetch('/status/' + taskId)
            .then(response => response.json())
            .then(data => {
                console.log('Status response:', data);
                
                if (data.status === 'Processing') {
                    document.getElementById('statusText').innerHTML = '⚡ Running advanced fraud detection algorithms...';
                    document.getElementById('progressBar').style.width = '75%';
                    setTimeout(checkStatus, 2000);
                } else if (data.status === 'Completed') {
                    document.getElementById('statusText').innerHTML = '✅ Fraud analysis complete!';
                    document.getElementById('progressBar').style.width = '100%';
                    document.getElementById('statusSection').className = 'status completed';
                    setTimeout(showResults, 500);
                } else if (data.status.startsWith('Error')) {
                    showError(data.status);
                } else {
                    document.getElementById('statusText').innerHTML = 'Status: ' + data.status;
                    setTimeout(checkStatus, 1000);
                }
            })
            .catch(error => {
                console.error('Status error:', error);
                showError('Status check failed');
            });
        }

        function showResults() {
            console.log('Fetching results for task:', taskId);
            
            fetch('/results/' + taskId)
            .then(response => response.json())
            .then(data => {
                console.log('Results data:', data);
                
                let amountCard = '';
                if (data.total_fraud_amount) {
                    amountCard = `
                        <div class="result-card">
                            <h4>💰 Total Fraud Amount</h4>
                            <div class="number" style="color: #e74c3c;">$${data.total_fraud_amount.toLocaleString()}</div>
                        </div>
                    `;
                }
                
                const resultsHtml = `
                    <div class="result-grid">
                        <div class="result-card">
                            <h4>📊 Detected Format</h4>
                            <div class="number" style="font-size: 1.2em; text-transform: capitalize;">${data.dataset_type.replace('_', ' ')}</div>
                        </div>
                        <div class="result-card">
                            <h4>🚨 Fraud Cases Found</h4>
                            <div class="number" style="color: #e74c3c;">${data.fraud_detected.toLocaleString()}</div>
                        </div>
                        <div class="result-card">
                            <h4>📈 Fraud Rate</h4>
                            <div class="number" style="color: #f39c12;">${data.fraud_rate.toFixed(2)}%</div>
                        </div>
                        <div class="result-card">
                            <h4>📋 Total Transactions</h4>
                            <div class="number" style="color: #28a745;">${data.total_transactions.toLocaleString()}</div>
                        </div>
                        ${amountCard}
                    </div>
                    
                    <div style="margin-top: 30px;">
                        <h3>🔍 Top Fraud Cases Detected</h3>
                        <p style="color: #666; margin-bottom: 20px;">Showing highest-risk transactions identified by our AI:</p>
                        ${data.top_fraud_cases.map((fraudCase, index) => `
                            <div class="fraud-item">
                                <strong>🚨 High-Risk Case ${index + 1}:</strong> 
                                <span style="color: #e74c3c; font-weight: bold;">Risk Score: ${(fraudCase.fraud_probability * 100).toFixed(1)}%</span>
                                ${fraudCase.amt ? ` | Amount: $${fraudCase.amt}` : ''}
                                ${fraudCase['amount (INR)'] ? ` | Amount: ₹${fraudCase['amount (INR)']}` : ''}
                                ${fraudCase.Amount ? ` | Amount: $${fraudCase.Amount}` : ''}
                                <br><small style="color: #6c757d;">AI Confidence: ${fraudCase.fraud_probability > 0.9 ? 'Very High' : fraudCase.fraud_probability > 0.7 ? 'High' : 'Medium'}</small>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div style="text-align: center; margin-top: 40px; padding: 30px; background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%); border-radius: 15px;">
                        <h3 style="color: #28a745; margin-bottom: 15px;">✅ Analysis Complete!</h3>
                        <p style="margin-bottom: 20px; color: #155724;">Your fraud detection analysis is ready. Ready to integrate this technology?</p>
                        <button class="btn" onclick="scrollToPricing()">💰 View Pricing Plans</button>
                        <button class="btn btn-secondary" onclick="alert('Contact our sales team at sales@fraudguard.ai')">🏢 Enterprise Solutions</button>
                    </div>
                `;
                
                document.getElementById('resultsContent').innerHTML = resultsHtml;
                document.getElementById('resultsSection').style.display = 'block';
                
                // Scroll to results
                document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
                
                // Reset test button
                const testBtn = document.getElementById('testBtn');
                testBtn.disabled = false;
                testBtn.innerHTML = '⚡ Analyze Again';
                
            })
            .catch(error => {
                console.error('Results error:', error);
                showError('Failed to load results');
            });
        }

        function showError(message) {
            console.error('Error:', message);
            const statusSection = document.getElementById('statusSection');
            statusSection.style.display = 'block';
            statusSection.className = 'status error';
            document.getElementById('statusText').innerHTML = '❌ ' + message;
            
            // Reset buttons
            const uploadBtn = document.getElementById('uploadBtn');
            const testBtn = document.getElementById('testBtn');
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '📤 Upload File';
            testBtn.disabled = false;
            testBtn.innerHTML = '⚡ Analyze for Fraud';
        }
    </script>
</body>
</html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        print("Upload endpoint called")
        
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'})
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'Only CSV files supported'})
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        print(f"Generated task ID: {task_id}")
        
        # Save file temporarily
        upload_dir = 'temp_uploads'
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{task_id}.csv")
        file.save(file_path)
        print(f"File saved to: {file_path}")
        
        # Start background analysis
        thread = threading.Thread(target=background_analysis, args=(task_id, file_path))
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'success', 'task_id': task_id})
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/status/<task_id>')
def get_status(task_id):
    try:
        status = analysis_status.get(task_id, 'Not found')
        print(f"Status check for {task_id}: {status}")
        return jsonify({'status': status})
    except Exception as e:
        print(f"Status error: {str(e)}")
        return jsonify({'status': f'Error: {str(e)}'})

@app.route('/results/<task_id>')
def get_results(task_id):
    try:
        if task_id in analysis_results:
            print(f"Returning results for {task_id}")
            return jsonify(analysis_results[task_id])
        else:
            print(f"Results not found for {task_id}")
            return jsonify({'error': 'Results not found'}), 404
    except Exception as e:
        print(f"Results error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🛡️ Starting FraudGuard Enterprise...")
    print("🔗 Open: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
