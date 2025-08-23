#!/usr/bin/env python3
"""
Working Universal Fraud Detection API
Simple, functional frontend with proper JavaScript
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
    <title>FraudGuard Enterprise - Universal Fraud Detection</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 0; 
            background: #f8f9fa;
        }
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem 2rem;
            color: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .navbar h1 { margin: 0; font-size: 1.8rem; }
        .navbar p { margin: 5px 0 0 0; opacity: 0.9; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .hero {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4rem 2rem;
            text-align: center;
            margin-bottom: 3rem;
            border-radius: 15px;
        }
        .hero h1 { font-size: 3rem; margin-bottom: 1rem; }
        .hero p { font-size: 1.3rem; opacity: 0.9; max-width: 600px; margin: 0 auto; }
        .tabs {
            display: flex;
            background: white;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .tab {
            flex: 1;
            padding: 1rem 2rem;
            background: #f8f9fa;
            border: none;
            cursor: pointer;
            font-size: 1.1rem;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .tab:hover:not(.active) { background: #e9ecef; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .upload-section { 
            background: white; 
            border-radius: 15px; 
            padding: 3rem; 
            text-align: center; 
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 2rem;
            margin: 1rem 0;
            background: #f8f9ff;
            transition: all 0.3s ease;
        }
        .upload-area:hover { background: #f0f3ff; }
        .upload-area.dragover { 
            background: #e8f2ff; 
            border-color: #5a6fd8; 
            transform: scale(1.02); 
        }
        .file-input { 
            margin: 1rem 0; 
            padding: 1rem; 
            border: 2px solid #ddd; 
            border-radius: 8px; 
            font-size: 1rem; 
            width: 300px;
        }
        .btn { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 1rem 2rem; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 1.1rem; 
            font-weight: bold;
            transition: all 0.3s ease;
            margin: 0.5rem;
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        .btn:disabled { 
            background: #6c757d; 
            cursor: not-allowed; 
            transform: none;
        }
        .btn-success {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }
        .pricing-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 2rem; 
            margin: 2rem 0;
        }
        .pricing-card { 
            background: white; 
            border-radius: 15px; 
            padding: 2rem; 
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .pricing-card:hover { transform: translateY(-5px); }
        .pricing-card.featured {
            border: 3px solid #667eea;
            transform: scale(1.05);
        }
        .pricing-card h3 { color: #667eea; margin-bottom: 1rem; }
        .price { font-size: 2.5rem; font-weight: bold; color: #333; }
        .price .currency { font-size: 1.2rem; }
        .price .period { font-size: 1rem; color: #6c757d; }
        .features { list-style: none; padding: 0; margin: 1.5rem 0; }
        .features li { padding: 0.5rem 0; border-bottom: 1px solid #eee; }
        .features li:last-child { border-bottom: none; }
        .status { 
            margin: 2rem 0; 
            padding: 1.5rem; 
            border-radius: 10px; 
            display: none;
            text-align: center;
        }
        .status.processing { 
            background: #fff3cd; 
            border: 2px solid #ffc107; 
            color: #856404;
        }
        .status.completed { 
            background: #d1f2eb; 
            border: 2px solid #28a745; 
            color: #155724;
        }
        .status.error { 
            background: #f8d7da; 
            border: 2px solid #dc3545; 
            color: #721c24;
        }
        .progress { 
            width: 100%; 
            height: 25px; 
            background: #e9ecef; 
            border-radius: 15px; 
            overflow: hidden; 
            margin: 1rem 0;
        }
        .progress-bar { 
            height: 100%; 
            background: linear-gradient(90deg, #667eea, #764ba2); 
            width: 0%; 
            transition: width 0.5s ease; 
            border-radius: 15px;
        }
        .results { 
            background: white; 
            border-radius: 15px; 
            padding: 2rem; 
            margin-top: 2rem; 
            display: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .result-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 1.5rem; 
            margin-bottom: 2rem;
        }
        .result-card { 
            background: #f8f9fa; 
            padding: 1.5rem; 
            border-radius: 10px; 
            text-align: center;
            border-left: 5px solid #667eea;
        }
        .result-card h4 { margin: 0 0 0.5rem 0; color: #333; }
        .result-card .number { font-size: 2rem; font-weight: bold; color: #667eea; }
        .fraud-list { margin-top: 2rem; }
        .fraud-item { 
            background: #fff5f5; 
            border-left: 4px solid #e74c3c; 
            margin: 1rem 0; 
            padding: 1rem; 
            border-radius: 8px; 
        }
        .demo-section {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .feature-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 2rem; 
            margin: 2rem 0;
        }
        .feature-card { 
            background: white; 
            border-radius: 10px; 
            padding: 1.5rem; 
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .feature-card h3 { color: #667eea; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>🛡️ FraudGuard Enterprise</h1>
        <p>Universal Fraud Detection for Banks & Fintech</p>
    </div>

    <div class="hero">
        <h1>Stop Fraud Before It Happens</h1>
        <p>Upload ANY transaction dataset - our AI automatically detects format and finds fraud with 95% accuracy</p>
    </div>

    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="showTab('upload')">📁 Upload & Analyze</button>
            <button class="tab" onclick="showTab('demo')">🚀 Live Demo</button>
            <button class="tab" onclick="showTab('pricing')">💰 Pricing</button>
            <button class="tab" onclick="showTab('enterprise')">🏢 Enterprise</button>
        </div>

        <!-- Upload Tab -->
        <div id="upload" class="tab-content active">
            <div class="upload-section">
                <h2>� Universal Fraud Detection</h2>
                <p>Upload any CSV file - we automatically detect the format and apply appropriate fraud detection</p>
                
                <div class="upload-area" id="uploadArea">
                    <h3>📁 Drop your CSV file here or click to browse</h3>
                    <p>Supports: UPI, Credit Card, Generic Transaction Data (up to 500MB)</p>
                    <input type="file" id="csvFile" accept=".csv" class="file-input">
                    <br>
                    <button class="btn" id="uploadBtn" onclick="uploadFile()">🔍 Analyze for Fraud</button>
                    <button class="btn btn-success" id="testBtn" onclick="testUploadedFile()" style="display:none;">⚡ Test Uploaded File</button>
                </div>
            </div>

            <div id="statusSection" class="status">
                <div id="statusText"></div>
                <div class="progress">
                    <div id="progressBar" class="progress-bar"></div>
                </div>
            </div>

            <div id="resultsSection" class="results">
                <h2>🚨 Fraud Detection Results</h2>
                <div id="resultsContent"></div>
            </div>
        </div>

        <!-- Demo Tab -->
        <div id="demo" class="tab-content">
            <div class="demo-section">
                <h2>🚀 Live Demo - See It In Action</h2>
                <p>Experience our fraud detection capabilities with real datasets</p>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <h3>🇮🇳 UPI Transactions</h3>
                        <p>Analyze Indian UPI payment fraud</p>
                        <button class="btn" onclick="runDemo('upi')">Demo UPI Detection</button>
                    </div>
                    <div class="feature-card">
                        <h3>💳 Credit Card Fraud</h3>
                        <p>Detect credit card transaction fraud</p>
                        <button class="btn" onclick="runDemo('creditcard')">Demo Credit Detection</button>
                    </div>
                    <div class="feature-card">
                        <h3>🌍 Generic Transactions</h3>
                        <p>Universal fraud detection</p>
                        <button class="btn" onclick="runDemo('generic')">Demo Universal Detection</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Pricing Tab -->
        <div id="pricing" class="tab-content">
            <h2 style="text-align: center; margin-bottom: 2rem;">💰 Enterprise Pricing</h2>
            <div class="pricing-grid">
                <div class="pricing-card">
                    <h3>Starter</h3>
                    <div class="price">
                        <span class="currency">₹</span>99
                        <span class="period">/month</span>
                    </div>
                    <ul class="features">
                        <li>Up to 10,000 transactions/month</li>
                        <li>Basic fraud detection</li>
                        <li>Email support</li>
                        <li>Standard reporting</li>
                    </ul>
                    <button class="btn">Get Started</button>
                </div>
                
                <div class="pricing-card featured">
                    <h3>Professional</h3>
                    <div class="price">
                        <span class="currency">₹</span>499
                        <span class="period">/month</span>
                    </div>
                    <ul class="features">
                        <li>Up to 100,000 transactions/month</li>
                        <li>Advanced ML fraud detection</li>
                        <li>Priority support</li>
                        <li>Custom reporting</li>
                        <li>API access</li>
                    </ul>
                    <button class="btn">Most Popular</button>
                </div>
                
                <div class="pricing-card">
                    <h3>Enterprise</h3>
                    <div class="price">
                        <span class="currency">₹</span>1,999
                        <span class="period">/month</span>
                    </div>
                    <ul class="features">
                        <li>Unlimited transactions</li>
                        <li>Real-time fraud detection</li>
                        <li>Dedicated support</li>
                        <li>Custom integrations</li>
                        <li>On-premise deployment</li>
                    </ul>
                    <button class="btn">Contact Sales</button>
                </div>
            </div>
        </div>

        <!-- Enterprise Tab -->
        <div id="enterprise" class="tab-content">
            <div class="demo-section">
                <h2>🏢 Enterprise Solutions</h2>
                <p>Scalable fraud detection for banks, fintech companies, and payment processors</p>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <h3>🏦 For Banks</h3>
                        <p>Integrate with existing core banking systems</p>
                        <ul style="text-align: left;">
                            <li>Real-time transaction monitoring</li>
                            <li>Regulatory compliance reporting</li>
                            <li>Custom risk scoring models</li>
                        </ul>
                    </div>
                    <div class="feature-card">
                        <h3>🚀 For Fintech</h3>
                        <p>API-first fraud detection for digital payments</p>
                        <ul style="text-align: left;">
                            <li>RESTful API integration</li>
                            <li>Webhook notifications</li>
                            <li>Custom fraud rules engine</li>
                        </ul>
                    </div>
                    <div class="feature-card">
                        <h3>💼 For Enterprises</h3>
                        <p>Protect your business from financial fraud</p>
                        <ul style="text-align: left;">
                            <li>Multi-dataset support</li>
                            <li>Advanced analytics dashboard</li>
                            <li>On-premise deployment</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let taskId = null;
        let lastUploadedFile = null;

        // Tab switching functionality
        function showTab(tabName) {
            // Hide all tab contents
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Remove active class from all tabs
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
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
                    document.getElementById('statusText').innerHTML = '✅ Upload successful! File ready for analysis.';
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
                    
                    <div class="fraud-list">
                        <h3>🔍 Top Fraud Cases Detected</h3>
                        <p>Showing highest-risk transactions identified by our AI:</p>
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
                    
                    <div style="text-align: center; margin-top: 2rem; padding: 1.5rem; background: #e8f5e8; border-radius: 10px;">
                        <h4 style="color: #28a745;">✅ Analysis Complete!</h4>
                        <p>Your fraud detection analysis is ready. Contact our sales team to integrate this technology into your systems.</p>
                        <button class="btn" onclick="showTab('pricing')">💰 View Pricing Plans</button>
                        <button class="btn" onclick="showTab('enterprise')">🏢 Enterprise Solutions</button>
                    </div>
                `;
                
                document.getElementById('resultsContent').innerHTML = resultsHtml;
                document.getElementById('resultsSection').style.display = 'block';
                
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

        function runDemo(demoType) {
            // Demo functionality for different dataset types
            alert(`🚀 Demo: ${demoType} fraud detection would analyze sample data and show real-time results. Contact sales for full demo access!`);
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
            uploadBtn.innerHTML = '🔍 Analyze for Fraud';
            testBtn.disabled = false;
            testBtn.innerHTML = '⚡ Test Uploaded File';
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
    print("🌟 Starting Universal Fraud Detection API...")
    print("🔗 Open: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
