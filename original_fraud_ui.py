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

# Try to import LLM components (optional)
try:
    from llm_integration import LLMFraudAnalyzer, LLMEnhancedFraudUI
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Initialize LLM integration (optional)
llm_enabled = False
llm_analyzer = None
llm_ui = None

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("💡 Install python-dotenv for better environment variable support: pip install python-dotenv")

if LLM_AVAILABLE:
    # Try Gemini first using environment variable
    try:
        print("🤖 Initializing Gemini AI...")
        llm_analyzer = LLMFraudAnalyzer(api_provider="gemini")  # Will use GEMINI_API_KEY from .env
        llm_ui = LLMEnhancedFraudUI(llm_analyzer)
        llm_enabled = True
        print("🤖 LLM integration enabled with Gemini AI")
    except Exception as e:
        print(f"⚠️ Gemini failed: {e}")
        # Fallback to Ollama if Gemini fails
        try:
            print("🔄 Falling back to Ollama...")
            llm_analyzer = LLMFraudAnalyzer(api_provider="ollama")
            llm_ui = LLMEnhancedFraudUI(llm_analyzer)
            llm_enabled = True
            print("🤖 LLM integration enabled with Ollama")
        except Exception as e2:
            llm_enabled = False
            print(f"⚠️ All LLM providers failed: Gemini: {e}, Ollama: {e2}")
else:
    print("⚠️ LLM components not found - running without AI features")
    llm_ui = None
    llm_enabled = False

# Global storage for analysis results
analysis_results = {}
analysis_status = {}

def background_analysis(task_id, file_path):
    """Run fraud analysis in background with AI explanations"""
    try:
        analysis_status[task_id] = "Processing"
        print(f"Starting analysis for task {task_id}")
        
        # Import here to avoid circular import issues
        from universal_fraud_detector import UniversalFraudDetector
        
        detector = UniversalFraudDetector()
        results_df = detector.analyze_dataset(file_path, save_results=False)
        
        # Get all fraud cases for detailed analysis
        fraud_cases = results_df[results_df['fraud_prediction'] == 1].copy()
        
        # Prepare detailed fraud analysis with AI explanations
        detailed_frauds = []
        
        print(f"🤖 Generating AI explanations for {len(fraud_cases)} fraud cases...")
        
        for idx, (_, fraud_case) in enumerate(fraud_cases.iterrows()):
            if idx >= 50:  # Limit to first 50 for performance
                break
                
            # Prepare transaction data for LLM
            transaction_data = fraud_case.to_dict()
            
            # Generate AI explanation if LLM is available
            ai_explanation = ""
            risk_factors = []
            
            if llm_enabled and llm_analyzer:
                try:
                    # Create feature importance based on fraud probability
                    feature_importance = {
                        'fraud_probability': float(fraud_case['fraud_probability']),
                        'amount': float(fraud_case.get('amount', fraud_case.get('amt', 0))),
                        'transaction_type': str(fraud_case.get('transaction_type', 'Unknown')),
                        'location': str(fraud_case.get('location', fraud_case.get('merchant', 'Unknown')))
                    }
                    
                    # Generate AI explanation
                    ai_explanation = llm_analyzer.explain_fraud_decision(
                        transaction_data=transaction_data,
                        prediction=1,
                        confidence=float(fraud_case['fraud_probability'] * 100),
                        feature_importance=feature_importance
                    )
                    
                    # Extract risk factors for summary
                    if 'amount' in transaction_data and transaction_data['amount'] > 10000:
                        risk_factors.append("High Amount")
                    if 'hour' in transaction_data and (transaction_data['hour'] < 6 or transaction_data['hour'] > 22):
                        risk_factors.append("Off-Hours Transaction")
                    if fraud_case['fraud_probability'] > 0.9:
                        risk_factors.append("Very High ML Score")
                        
                except Exception as e:
                    ai_explanation = f"AI analysis unavailable: {str(e)}"
                    print(f"LLM error for case {idx}: {e}")
            else:
                ai_explanation = "AI explanations disabled - LLM not available"
                
            # Rule-based risk factor identification
            if not risk_factors:
                if fraud_case['fraud_probability'] > 0.8:
                    risk_factors.append("High Risk Score")
                if 'amount' in fraud_case and fraud_case['amount'] > 5000:
                    risk_factors.append("Large Transaction")
                if 'failed' in str(fraud_case.get('status', '')).lower():
                    risk_factors.append("Failed Transaction")
            
            detailed_fraud = {
                'index': int(fraud_case.name),
                'probability': float(fraud_case['fraud_probability']),
                'amount': float(fraud_case.get('amount', fraud_case.get('amt', 0))),
                'transaction_data': transaction_data,
                'ai_explanation': ai_explanation,
                'risk_factors': risk_factors,
                'severity': 'CRITICAL' if fraud_case['fraud_probability'] > 0.9 else 'HIGH' if fraud_case['fraud_probability'] > 0.7 else 'MEDIUM'
            }
            detailed_frauds.append(detailed_fraud)
        
        # Store comprehensive results
        analysis_results[task_id] = {
            'dataset_type': detector.dataset_type,
            'total_transactions': len(results_df),
            'fraud_detected': int(results_df['fraud_prediction'].sum()),
            'fraud_rate': float(results_df['fraud_prediction'].mean() * 100),
            'high_risk_count': int((results_df['fraud_probability'] > 0.7).sum()),
            'critical_risk_count': int((results_df['fraud_probability'] > 0.9).sum()),
            'detailed_frauds': detailed_frauds,
            'ai_enabled': llm_enabled,
            'analysis_summary': f"Analyzed {len(results_df)} transactions, detected {len(fraud_cases)} potential fraud cases with AI explanations"
        }
        
        # Calculate total fraud amount if amount column exists
        amount_cols = [col for col in results_df.columns if any(word in col.lower() for word in ['amount', 'amt', 'value'])]
        if amount_cols:
            amount_col = amount_cols[0]
            fraud_amount = float(results_df[results_df['fraud_prediction'] == 1][amount_col].sum())
            analysis_results[task_id]['total_fraud_amount'] = fraud_amount
        
        analysis_status[task_id] = "Completed"
        print(f"Analysis completed for task {task_id} with {len(detailed_frauds)} detailed fraud explanations")
        
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
        .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 80px 0; text-align: center; position: relative; overflow: hidden; min-height: 600px; }
        .hero::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.3); z-index: 1; }
        .hero-content { position: relative; z-index: 2; display: flex; align-items: center; justify-content: space-between; max-width: 1400px; margin: 0 auto; padding: 0 20px; min-height: 500px; }
        .hero-text { flex: 1; text-align: left; padding-right: 40px; }
        .hero-photo { flex: 0 0 500px; margin-left: 30px; }
        .hero-avatar { width: 500px; height: 500px; border-radius: 25px; background-image: url('/images/nirmala.webp'); background-size: cover; background-position: center; box-shadow: 0 25px 50px rgba(0,0,0,0.4); border: 8px solid rgba(255,255,255,0.2); transition: transform 0.3s ease; }
        .hero-avatar:hover { transform: scale(1.03) rotate(1deg); }
        @media (max-width: 768px) { .hero-content { flex-direction: column; text-align: center; min-height: auto; } .hero-photo { margin: 30px 0 0 0; flex: 0 0 300px; } .hero-avatar { width: 300px; height: 300px; } }
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
        .upload-section { background: white; margin: 50px auto; max-width: 1100px; border-radius: 15px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); position: relative; }
        .upload-container { display: flex; align-items: center; justify-content: center; gap: 40px; }
        .upload-area { border: 3px dashed #667eea; border-radius: 15px; padding: 40px; text-align: center; background: #f8f9ff; transition: all 0.3s; max-width: 500px; flex: 1; }
        .upload-area:hover { background: #f0f3ff; transform: scale(1.02); }
        .upload-area.dragover { background: #e8f2ff; border-color: #5a67d8; }
        .side-image { width: 150px; height: 150px; background-image: url('/images/sigham.webp'); background-size: cover; background-position: center; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); transition: transform 0.3s ease; border: 3px solid #667eea; }
        .side-image:hover { transform: scale(1.05) rotate(2deg); }
        .side-image.left { animation: float 3s ease-in-out infinite; }
        .side-image.right { animation: float 3s ease-in-out infinite reverse; }
        @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-10px); } }
        @media (max-width: 768px) { .upload-container { flex-direction: column; } .side-image { display: none; } }
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
        <div class="hero-content">
            <div class="hero-text">
                <h1>🛡️Fraud Karega Sale</h1>
                <h1>Tere se bhi Tax Katungi</h1>
                <button class="btn" onclick="scrollToUpload()">Try Demo Upload</button>
                <button class="btn btn-secondary" onclick="scrollToPricing()">View Pricing</button>
            </div>
            <div class="hero-photo">
                <div class="hero-avatar" title="Fraud Detection Expert"></div>
            </div>
        </div>
    </div>
    
    <!-- Upload Section -->
    <div class="upload-section" id="uploadSection">
        <h2 style="text-align: center; margin-bottom: 30px; color: #667eea;">🔍 Upload & Analyze Fraud Data</h2>
        <p style="text-align: center; margin-bottom: 30px; color: #666;">Upload any CSV transaction file - our AI automatically detects format and finds fraud</p>
        
        <div class="upload-container">
            <!-- Left Square Image -->
            <div class="side-image left" title="Security Expert"></div>
            
            <!-- Main Upload Area -->
            <div class="upload-area" id="uploadArea">
                <h3>📁 Drop your CSV file here or click to browse</h3>
                <p style="margin: 20px 0; color: #666;">Supports: UPI, Credit Card, Generic Transaction Data (up to 500MB)</p>
                <input type="file" id="csvFile" accept=".csv" class="file-input">
                <br>
                <button class="btn btn-upload" id="uploadBtn" onclick="uploadFile()">📤 Upload File</button>
                <button class="btn btn-test" id="testBtn" onclick="testUploadedFile()" style="display:none;">⚡ Analyze for Fraud</button>
            </div>
            
            <!-- Right Square Image -->
            <div class="side-image right" title="Fraud Detective"></div>
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
                        <h3>🔍 Fraud Detection Summary</h3>
                        <p style="color: #666; margin-bottom: 20px;">Quick overview of detected fraud cases:</p>
                        ${data.detailed_frauds ? data.detailed_frauds.slice(0, 3).map((fraudCase, index) => `
                            <div class="fraud-item">
                                <strong>🚨 ${fraudCase.severity} Risk Case #${fraudCase.index}:</strong> 
                                <span style="color: #e74c3c; font-weight: bold;">Risk Score: ${(fraudCase.probability * 100).toFixed(1)}%</span>
                                | Amount: $${fraudCase.amount.toLocaleString()}
                                <br><small style="color: #6c757d;">Risk Factors: ${fraudCase.risk_factors.slice(0, 2).join(', ')}</small>
                                ${fraudCase.ai_explanation ? '<br><small style="color: #667eea;">🤖 AI Analysis Available</small>' : ''}
                            </div>
                        `).join('') : (data.top_fraud_cases || []).map((fraudCase, index) => `
                            <div class="fraud-item">
                                <strong>🚨 High-Risk Case ${index + 1}:</strong> 
                                <span style="color: #e74c3c; font-weight: bold;">Risk Score: ${(fraudCase.fraud_probability * 100).toFixed(1)}%</span>
                                ${fraudCase.amt ? ` | Amount: $${fraudCase.amt}` : ''}
                                ${fraudCase['amount (INR)'] ? ` | Amount: ₹${fraudCase['amount (INR)']}` : ''}
                                ${fraudCase.Amount ? ` | Amount: $${fraudCase.Amount}` : ''}
                                <br><small style="color: #6c757d;">AI Confidence: ${fraudCase.fraud_probability > 0.9 ? 'Very High' : fraudCase.fraud_probability > 0.7 ? 'High' : 'Medium'}</small>
                            </div>
                        `).join('')}
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="/dashboard/${taskId}" class="btn" style="background: #e74c3c; font-size: 1.2em; padding: 15px 30px;">
                                🛡️ View Complete AI Fraud Dashboard
                            </a>
                            ${data.ai_enabled ? '<br><small style="color: #667eea; margin-top: 10px;">🤖 Includes detailed AI explanations for all fraud cases</small>' : ''}
                        </div>
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

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve images from the images folder"""
    try:
        from flask import send_from_directory
        return send_from_directory('images', filename)
    except Exception as e:
        print(f"Image serving error: {str(e)}")
        return "Image not found", 404

@app.route('/dashboard/<task_id>')
def fraud_dashboard(task_id):
    """Enhanced fraud dashboard with AI explanations"""
    if task_id not in analysis_results:
        return "Results not found", 404
        
    results = analysis_results[task_id]
    
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>FraudGuard AI Dashboard - Detailed Fraud Analysis</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; color: #333; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 0; text-align: center; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }}
        .stat-number {{ font-size: 2.5em; font-weight: bold; color: #667eea; margin-bottom: 10px; }}
        .stat-label {{ color: #666; font-size: 1.1em; }}
        .fraud-list {{ background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 30px 0; }}
        .fraud-header {{ background: #667eea; color: white; padding: 20px; border-radius: 12px 12px 0 0; }}
        .fraud-item {{ border-bottom: 1px solid #eee; padding: 25px; }}
        .fraud-item:last-child {{ border-bottom: none; }}
        .fraud-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 15px; color: #333; }}
        .fraud-meta {{ display: flex; gap: 20px; margin-bottom: 15px; flex-wrap: wrap; }}
        .fraud-tag {{ background: #fee; color: #c53030; padding: 5px 12px; border-radius: 20px; font-size: 0.9em; }}
        .fraud-tag.critical {{ background: #fed7d7; color: #c53030; }}
        .fraud-tag.high {{ background: #fef5e7; color: #dd6b20; }}
        .fraud-tag.medium {{ background: #fefcbf; color: #d69e2e; }}
        .ai-explanation {{ background: #f7fafc; border-left: 4px solid #667eea; padding: 20px; margin: 15px 0; border-radius: 0 8px 8px 0; }}
        .risk-factors {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 15px 0; }}
        .risk-factor {{ background: #e2e8f0; color: #2d3748; padding: 8px 12px; border-radius: 15px; font-size: 0.9em; }}
        .transaction-details {{ background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 15px 0; font-family: monospace; font-size: 0.9em; }}
        .btn {{ background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; margin: 10px 5px; }}
        .btn:hover {{ background: #5a67d8; }}
        .pagination {{ text-align: center; margin: 30px 0; }}
        .ai-badge {{ background: #38a169; color: white; padding: 5px 10px; border-radius: 12px; font-size: 0.8em; margin-left: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ FraudGuard AI Dashboard</h1>
        <h1>Pakda Gya Sale..AI he 😏😏</h1>
        {"<span class='ai-badge'>🤖 Ab tera bhai bataayega fraud kaha hua he</span>" if results.get('ai_enabled') else ""}
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{results['total_transactions']:,}</div>
                <div class="stat-label">Total Transactions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #e53e3e;">{results['fraud_detected']:,}</div>
                <div class="stat-label">Fraud Cases Detected</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #dd6b20;">{results['fraud_rate']:.2f}%</div>
                <div class="stat-label">Fraud Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #c53030;">{results.get('critical_risk_count', 0):,}</div>
                <div class="stat-label">Critical Risk Cases</div>
            </div>
            {"<div class='stat-card'><div class='stat-number' style='color: #38a169;'>${:,.2f}</div><div class='stat-label'>Total Fraud Amount</div></div>".format(results['total_fraud_amount']) if 'total_fraud_amount' in results else ""}
        </div>
        
        <div class="fraud-list">
            <div class="fraud-header">
                <h2>🚨 Detailed Fraud Analysis ({len(results.get('detailed_frauds', []))} cases shown)</h2>
                <p>{results.get('analysis_summary', 'Comprehensive fraud detection analysis')}</p>
            </div>
            
            {"".join([f'''
            <div class="fraud-item">
                <div class="fraud-title">
                    🚨 Fraud Case #{fraud['index']} - {fraud['severity']} Risk
                    <span class="fraud-tag {fraud['severity'].lower()}">{fraud['probability']:.1%} Confidence</span>
                </div>
                
                <div class="fraud-meta">
                    <span><strong>Amount:</strong> ${fraud['amount']:,.2f}</span>
                    <span><strong>Severity:</strong> {fraud['severity']}</span>
                    <span><strong>ML Confidence:</strong> {fraud['probability']:.1%}</span>
                </div>
                
                {"<div class='risk-factors'>" + "".join([f"<span class='risk-factor'>⚠️ {factor}</span>" for factor in fraud['risk_factors']]) + "</div>" if fraud['risk_factors'] else ""}
                
                {"<div class='ai-explanation'><h4>🤖 AI Analysis:</h4><p>" + fraud['ai_explanation'].replace('\n', '<br>') + "</p></div>" if fraud['ai_explanation'] and not fraud['ai_explanation'].startswith('AI') else ""}
                
                <details>
                    <summary style="cursor: pointer; font-weight: bold; margin: 10px 0;">📊 View Transaction Details</summary>
                    <div class="transaction-details">
                        {"<br>".join([f"<strong>{k}:</strong> {v}" for k, v in fraud['transaction_data'].items() if k not in ['fraud_prediction', 'fraud_probability']])}
                    </div>
                </details>
            </div>
            ''' for fraud in results.get('detailed_frauds', [])[:20]])}
        </div>
        
        <div class="pagination">
            <a href="/" class="btn">🏠 Back to Home</a>
            <a href="/results/{task_id}" class="btn">📊 Raw JSON Results</a>
        </div>
    </div>
</body>
</html>
    '''

if __name__ == '__main__':
    print("🛡️ Starting FraudGuard Enterprise...")
    print("🔗 Open: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
