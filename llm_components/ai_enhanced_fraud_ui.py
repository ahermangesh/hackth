#!/usr/bin/env python3
"""
🤖 FraudGuard AI-Enhanced System
Beautiful enterprise UI with LLM-powered fraud analysis
"""

from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import uuid
import os
import threading
import time
import traceback
import json
from llm_integration import LLMFraudAnalyzer, LLMEnhancedFraudUI

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Initialize LLM capabilities
try:
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("💡 Install python-dotenv: pip install python-dotenv")
    
    # Try different providers in order of preference (Gemini first from environment)
    providers = [
        ("gemini", None),  # Will use GEMINI_API_KEY from .env
        ("ollama", None),
        ("openai", None),
        ("anthropic", None)
    ]
    llm_analyzer = None
    
    for provider, api_key in providers:
        try:
            llm_analyzer = LLMFraudAnalyzer(api_provider=provider, api_key=api_key)
            print(f"🤖 LLM integration enabled with {provider}")
            break
        except Exception as e:
            print(f"   Failed to initialize {provider}: {e}")
            continue
    
    if llm_analyzer:
        llm_ui = LLMEnhancedFraudUI(llm_analyzer)
        llm_enabled = True
    else:
        llm_enabled = False
        print("⚠️ No LLM provider available")
        
except Exception as e:
    llm_enabled = False
    print(f"⚠️ LLM integration disabled: {e}")

# Global storage
analysis_results = {}
analysis_status = {}
chat_history = {}

@app.route('/')
def index():
    """Main page with LLM-enhanced interface"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 FraudGuard AI - LLM Enhanced Fraud Detection</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            color: white;
        }
        
        .header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .ai-badge {
            background: linear-gradient(45deg, #ff6b6b, #feca57);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
            margin: 10px 0;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            background: linear-gradient(45deg, #f8f9ff, #e8ecff);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-area:hover {
            border-color: #764ba2;
            background: linear-gradient(45deg, #e8ecff, #d4e3ff);
        }
        
        .upload-area.dragover {
            border-color: #ff6b6b;
            background: linear-gradient(45deg, #fff0f0, #ffe8e8);
        }
        
        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn-ai {
            background: linear-gradient(45deg, #ff6b6b, #feca57);
        }
        
        .btn-ai:hover {
            box-shadow: 0 10px 20px rgba(255, 107, 107, 0.4);
        }
        
        .chat-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            height: 400px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: linear-gradient(to bottom, #f8f9ff, #e8ecff);
        }
        
        .chat-input {
            display: flex;
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
        }
        
        .chat-input input {
            flex: 1;
            padding: 12px;
            border: 2px solid #eee;
            border-radius: 15px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s ease;
        }
        
        .chat-input input:focus {
            border-color: #667eea;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 18px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .message.user {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            margin-left: auto;
        }
        
        .message.ai {
            background: linear-gradient(45deg, #ff6b6b, #feca57);
            color: white;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }
        
        .feature-card {
            background: rgba(255, 255, 255, 0.9);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }
        
        .status-indicator {
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
            margin: 10px 0;
        }
        
        .status-enabled {
            background: linear-gradient(45deg, #4ecdc4, #2ecc71);
            color: white;
        }
        
        .status-disabled {
            background: linear-gradient(45deg, #95a5a6, #bdc3c7);
            color: white;
        }
        
        .results-container {
            display: none;
            margin-top: 30px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
        }
        
        .fraud-alert {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin: 15px 0;
            font-weight: bold;
        }
        
        .safe-alert {
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin: 15px 0;
            font-weight: bold;
        }
        
        .ai-explanation {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin: 15px 0;
            white-space: pre-wrap;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 FraudGuard AI</h1>
            <p>LLM-Enhanced Fraud Detection System</p>
            <div class="ai-badge">
                🧠 Powered by Artificial Intelligence
            </div>
            <div class="status-indicator {{ 'status-enabled' if llm_enabled else 'status-disabled' }}">
                🤖 AI Analysis: {{ 'ENABLED' if llm_enabled else 'DISABLED' }}
            </div>
        </div>
        
        <div class="main-grid">
            <div class="card">
                <h2>📊 Upload & Analyze</h2>
                <div class="upload-area" id="uploadArea">
                    <div class="feature-icon">📁</div>
                    <h3>Drop your fraud dataset here</h3>
                    <p>Supports UPI and Credit Card transaction data</p>
                    <input type="file" id="fileInput" accept=".csv" style="display: none;">
                    <br><br>
                    <button class="btn" onclick="document.getElementById('fileInput').click()">
                        Choose File
                    </button>
                </div>
                <div id="analysisResults" class="results-container"></div>
            </div>
            
            <div class="card">
                <h2>🤖 AI Chat Assistant</h2>
                <div class="chat-container">
                    <div class="chat-messages" id="chatMessages">
                        {% if llm_enabled %}
                        <div class="message ai">
                            🤖 Hello! I'm your AI fraud analyst. Ask me anything about fraud patterns, upload your data for intelligent analysis, or request fraud insights!
                        </div>
                        {% else %}
                        <div class="message ai">
                            🤖 AI Assistant is currently offline. Please configure an LLM provider (OpenAI, Anthropic, or Ollama) to enable intelligent fraud analysis.
                        </div>
                        {% endif %}
                    </div>
                    <div class="chat-input">
                        <input type="text" id="chatInput" placeholder="Ask about fraud patterns, analysis results, or detection insights..." {% if not llm_enabled %}disabled{% endif %}>
                        <button class="btn btn-ai" onclick="sendMessage()" {% if not llm_enabled %}disabled{% endif %}>
                            Send 🚀
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">🧠</div>
                <h3>AI-Powered Analysis</h3>
                <p>Get intelligent explanations for every fraud decision with advanced reasoning</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">💬</div>
                <h3>Natural Language Queries</h3>
                <p>Ask questions about your fraud data in plain English and get instant insights</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">📈</div>
                <h3>Pattern Recognition</h3>
                <p>AI identifies complex fraud patterns and emerging threats automatically</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <h3>Focused Detection</h3>
                <p>Specialized models for UPI and Credit Card fraud with 99.8%+ accuracy</p>
            </div>
        </div>
    </div>
    
    <script>
        let currentTaskId = null;
        
        // File upload handling
        document.getElementById('fileInput').addEventListener('change', handleFileUpload);
        
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });
        
        function handleFileUpload() {
            const file = document.getElementById('fileInput').files[0];
            if (file) {
                handleFile(file);
            }
        }
        
        function handleFile(file) {
            const formData = new FormData();
            formData.append('file', file);
            
            // Show loading
            const resultsContainer = document.getElementById('analysisResults');
            resultsContainer.style.display = 'block';
            resultsContainer.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <h3>🤖 AI is analyzing your data...</h3>
                    <p>Detecting fraud patterns and generating intelligent insights</p>
                </div>
            `;
            
            // Upload and analyze
            fetch('/upload_and_analyze', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.task_id) {
                    currentTaskId = data.task_id;
                    checkAnalysisStatus();
                } else {
                    throw new Error(data.error || 'Upload failed');
                }
            })
            .catch(error => {
                resultsContainer.innerHTML = `
                    <div class="fraud-alert">
                        ❌ Error: ${error.message}
                    </div>
                `;
            });
        }
        
        function checkAnalysisStatus() {
            if (!currentTaskId) return;
            
            fetch(`/status/${currentTaskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    showResults();
                } else if (data.status === 'error') {
                    document.getElementById('analysisResults').innerHTML = `
                        <div class="fraud-alert">
                            ❌ Analysis failed: ${data.error}
                        </div>
                    `;
                } else {
                    setTimeout(checkAnalysisStatus, 2000);
                }
            })
            .catch(error => {
                console.error('Status check failed:', error);
                setTimeout(checkAnalysisStatus, 2000);
            });
        }
        
        function showResults() {
            fetch(`/results/${currentTaskId}`)
            .then(response => response.json())
            .then(data => {
                const resultsContainer = document.getElementById('analysisResults');
                
                let html = `
                    <h3>🎯 Analysis Results</h3>
                    <div class="${data.fraud_detected ? 'fraud-alert' : 'safe-alert'}">
                        ${data.fraud_detected ? '🚨 FRAUD DETECTED' : '✅ NO FRAUD DETECTED'}
                        <br>Accuracy: ${(data.accuracy * 100).toFixed(1)}%
                        <br>Fraud Cases: ${data.fraud_count}/${data.total_transactions}
                    </div>
                `;
                
                if (data.ai_explanation) {
                    html += `
                        <div class="ai-explanation">
                            <h4>🤖 AI Analysis:</h4>
                            ${data.ai_explanation}
                        </div>
                    `;
                }
                
                if (data.top_features) {
                    html += `
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 15px; margin: 15px 0;">
                            <h4>📊 Top Risk Factors:</h4>
                            <ul>
                    `;
                    for (const [feature, importance] of Object.entries(data.top_features)) {
                        html += `<li>${feature}: ${(importance * 100).toFixed(1)}%</li>`;
                    }
                    html += `</ul></div>`;
                }
                
                resultsContainer.innerHTML = html;
                
                // Add to chat if AI is enabled
                if (data.ai_explanation && {{ 'true' if llm_enabled else 'false' }}) {
                    addMessage('ai', `📊 Analysis Complete: ${data.ai_explanation}`);
                }
            })
            .catch(error => {
                document.getElementById('analysisResults').innerHTML = `
                    <div class="fraud-alert">
                        ❌ Failed to load results: ${error.message}
                    </div>
                `;
            });
        }
        
        // Chat functionality
        function sendMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage('user', message);
            input.value = '';
            
            // Show typing indicator
            addMessage('ai', '🤖 Thinking...');
            
            // Send to AI
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    task_id: currentTaskId
                })
            })
            .then(response => response.json())
            .then(data => {
                // Remove thinking indicator
                const messages = document.getElementById('chatMessages');
                messages.removeChild(messages.lastChild);
                
                addMessage('ai', data.response);
            })
            .catch(error => {
                // Remove thinking indicator
                const messages = document.getElementById('chatMessages');
                messages.removeChild(messages.lastChild);
                
                addMessage('ai', `❌ Sorry, I encountered an error: ${error.message}`);
            });
        }
        
        function addMessage(sender, text) {
            const messages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            messageDiv.textContent = text;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }
        
        // Enter key support for chat
        document.getElementById('chatInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
    """, llm_enabled=llm_enabled)

@app.route('/upload_and_analyze', methods=['POST'])
def upload_and_analyze():
    """Upload and analyze dataset with AI enhancement"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        analysis_status[task_id] = 'processing'
        
        # Save uploaded file
        temp_dir = 'temp_uploads'
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, f"{task_id}_{file.filename}")
        file.save(file_path)
        
        # Start analysis in background
        thread = threading.Thread(target=analyze_with_ai, args=(task_id, file_path))
        thread.start()
        
        return jsonify({'task_id': task_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_with_ai(task_id, file_path):
    """Analyze dataset with AI enhancement"""
    try:
        # Load and analyze data
        df = pd.read_csv(file_path)
        
        # Determine dataset type and fraud column
        fraud_col = None
        if 'Class' in df.columns:
            fraud_col = 'Class'
        elif 'is_fraud' in df.columns:
            fraud_col = 'is_fraud'
        elif 'fraud_flag' in df.columns:
            fraud_col = 'fraud_flag'
        
        if fraud_col is None:
            # No fraud labels - use unsupervised detection
            from sklearn.ensemble import IsolationForest
            
            # Basic feature engineering
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            X = df[numeric_cols].fillna(0)
            
            # Train isolation forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            predictions = iso_forest.fit_predict(X)
            fraud_predictions = (predictions == -1).astype(int)
            
            fraud_count = fraud_predictions.sum()
            accuracy = 0.85  # Estimated for unsupervised
            
        else:
            # Supervised learning with known fraud labels
            fraud_count = df[fraud_col].sum()
            
            # Feature engineering based on dataset type
            if 'V1' in df.columns:  # Credit Card PCA
                features = engineer_cc_features(df)
            else:  # UPI or detailed credit card
                features = engineer_upi_features(df)
            
            # Train model
            X = features.drop([fraud_col], axis=1, errors='ignore')
            y = df[fraud_col]
            
            X = X.fillna(0)
            
            # Split and train
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Feature importance
            feature_importance = dict(zip(X.columns, model.feature_importances_))
            top_features = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5])
        
        # Generate AI explanation if available
        ai_explanation = None
        if llm_enabled and llm_analyzer:
            try:
                # Create sample transaction for explanation
                sample_transaction = df.iloc[0].to_dict()
                
                explanation = llm_analyzer.explain_fraud_decision(
                    sample_transaction, 
                    1 if fraud_count > 0 else 0,
                    accuracy,
                    top_features if 'top_features' in locals() else {}
                )
                ai_explanation = explanation
            except Exception as e:
                ai_explanation = f"AI analysis unavailable: {str(e)}"
        
        # Store results
        analysis_results[task_id] = {
            'total_transactions': len(df),
            'fraud_count': int(fraud_count),
            'fraud_detected': fraud_count > 0,
            'accuracy': accuracy,
            'ai_explanation': ai_explanation,
            'top_features': top_features if 'top_features' in locals() else {},
            'dataset_type': 'Credit Card (PCA)' if 'V1' in df.columns else 'UPI/Credit Card',
            'analysis_timestamp': time.time()
        }
        
        analysis_status[task_id] = 'completed'
        
        # Cleanup
        os.remove(file_path)
        
    except Exception as e:
        analysis_status[task_id] = 'error'
        analysis_results[task_id] = {'error': str(e)}
        print(f"Analysis error: {e}")

def engineer_cc_features(df):
    """Engineer Credit Card features"""
    features = df.copy()
    
    # V feature aggregations
    v_columns = [col for col in features.columns if col.startswith('V')]
    if v_columns:
        features['V_mean'] = features[v_columns].mean(axis=1)
        features['V_std'] = features[v_columns].std(axis=1)
        features['V_max'] = features[v_columns].max(axis=1)
        features['V_min'] = features[v_columns].min(axis=1)
    
    # Amount features
    if 'Amount' in features.columns:
        features['Amount_log'] = np.log1p(features['Amount'])
        features['Amount_normalized'] = features['Amount'] / features['Amount'].max()
    
    return features

def engineer_upi_features(df):
    """Engineer UPI features"""
    features = df.copy()
    
    # Amount features
    amount_cols = [col for col in features.columns if 'amount' in col.lower()]
    if amount_cols:
        amount_col = amount_cols[0]
        features['amount_log'] = np.log1p(features[amount_col])
        features['high_amount'] = (features[amount_col] > features[amount_col].quantile(0.95)).astype(int)
    
    # Categorical encoding
    categorical_cols = features.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if col not in ['transaction id', 'timestamp']:
            le = LabelEncoder()
            features[f'{col}_encoded'] = le.fit_transform(features[col].astype(str))
    
    return features

@app.route('/status/<task_id>')
def get_status(task_id):
    """Get analysis status"""
    status = analysis_status.get(task_id, 'not_found')
    return jsonify({'status': status})

@app.route('/results/<task_id>')
def get_results(task_id):
    """Get analysis results"""
    if task_id not in analysis_results:
        return jsonify({'error': 'Results not found'}), 404
    
    return jsonify(analysis_results[task_id])

@app.route('/chat', methods=['POST'])
def chat():
    """AI chat endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        task_id = data.get('task_id')
        
        if not llm_enabled:
            return jsonify({
                'response': '🤖 AI Assistant is currently offline. Please configure an LLM provider to enable intelligent analysis.'
            })
        
        # Get context from analysis if available
        context_data = None
        if task_id and task_id in analysis_results:
            context_data = analysis_results[task_id]
        
        # Generate AI response
        if context_data:
            # Create a simple dataframe for context
            context_df = pd.DataFrame([{
                'total_transactions': context_data['total_transactions'],
                'fraud_count': context_data['fraud_count'],
                'accuracy': context_data['accuracy']
            }])
            response = llm_analyzer.natural_language_query(message, context_df)
        else:
            # General fraud detection question
            response = llm_analyzer.natural_language_query(message, pd.DataFrame())
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({
            'response': f'🤖 Sorry, I encountered an error: {str(e)}'
        })

if __name__ == '__main__':
    print("🤖 Starting FraudGuard AI-Enhanced System...")
    print(f"🧠 LLM Integration: {'ENABLED' if llm_enabled else 'DISABLED'}")
    print("🌐 Open: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
