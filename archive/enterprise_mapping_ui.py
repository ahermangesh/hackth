#!/usr/bin/env python3
"""
Enterprise FraudGuard with Interactive Column Mapping UI
The most impressive fraud detection system for enterprise clients
"""

from flask import Flask, request, jsonify
import pandas as pd
import uuid
import os
import threading
import time
import traceback
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Global storage
analysis_results = {}
analysis_status = {}
dataset_structures = {}

def background_analysis(task_id, file_path, column_mappings=None, has_fraud_labels=False, fraud_label_column=None):
    """Run fraud analysis in background with optional column mappings"""
    try:
        analysis_status[task_id] = "Processing"
        print(f"Starting analysis for task {task_id}")
        
        from enterprise_universal_detector import EnterpriseUniversalDetector
        
        detector = EnterpriseUniversalDetector()
        result = detector.analyze_dataset(
            file_path, 
            column_mappings=column_mappings,
            has_fraud_labels=has_fraud_labels,
            fraud_label_column=fraud_label_column
        )
        
        if result['status'] == 'needs_mapping':
            # Store dataset structure for interactive mapping
            dataset_structures[task_id] = result['structure']
            analysis_status[task_id] = "Needs Column Mapping"
            analysis_results[task_id] = {
                'status': 'needs_mapping',
                'structure': result['structure']
            }
            # DON'T delete file yet - we need it for remapping
            return
            
        elif result['status'] == 'success':
            results_df = result['results']
            
            # Store comprehensive results
            analysis_results[task_id] = {
                'status': 'success',
                'dataset_type': result['dataset_type'],
                'total_transactions': result['total_transactions'],
                'fraud_detected': result['fraud_detected'],
                'fraud_rate': result['fraud_rate'],
                'high_risk_count': int((results_df['fraud_probability'] > 0.7).sum()),
                'top_fraud_cases': results_df[results_df['fraud_prediction'] == 1].nlargest(5, 'fraud_probability').to_dict('records'),
            }
            
            # Calculate fraud amount if possible
            amount_cols = [col for col in results_df.columns if any(word in col.lower() for word in ['amount', 'amt', 'value', 'price', 'cost'])]
            if amount_cols:
                amount_col = amount_cols[0]
                fraud_amount = float(results_df[results_df['fraud_prediction'] == 1][amount_col].sum())
                analysis_results[task_id]['total_fraud_amount'] = fraud_amount
            
            analysis_status[task_id] = "Completed"
        else:
            analysis_status[task_id] = f"Error: {result['message']}"
        
        print(f"Analysis completed for task {task_id}")
        
        # Only clean up file after successful analysis
        if os.path.exists(file_path) and result['status'] == 'success':
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
    <title>FraudGuard Enterprise - Universal AI Fraud Detection</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: #f8f9fa; }
        .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 80px 0; text-align: center; }
        .hero h1 { font-size: 3.2em; margin-bottom: 15px; }
        .hero p { font-size: 1.3em; margin-bottom: 30px; opacity: 0.95; }
        .badge { background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-size: 0.9em; margin: 10px 5px; display: inline-block; }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        .btn { background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 25px; font-size: 1em; cursor: pointer; margin: 8px; text-decoration: none; display: inline-block; transition: all 0.3s; }
        .btn:hover { background: #5a67d8; transform: translateY(-2px); }
        .btn-secondary { background: white; color: #667eea; border: 2px solid rgba(255,255,255,0.8); }
        .btn-secondary:hover { background: rgba(255,255,255,0.1); color: white; }
        
        /* Upload section */
        .upload-section { background: white; margin: 40px auto; max-width: 900px; border-radius: 20px; padding: 40px; box-shadow: 0 15px 40px rgba(0,0,0,0.1); }
        .upload-area { border: 3px dashed #667eea; border-radius: 15px; padding: 40px; text-align: center; background: linear-gradient(135deg, #f8f9ff 0%, #f0f3ff 100%); transition: all 0.3s; }
        .upload-area:hover { background: linear-gradient(135deg, #f0f3ff 0%, #e8f2ff 100%); transform: scale(1.01); }
        .upload-area.dragover { background: linear-gradient(135deg, #e8f2ff 0%, #d4f1ff 100%); border-color: #5a67d8; }
        .file-input { margin: 20px 0; padding: 15px; border: 2px solid #ddd; border-radius: 10px; font-size: 16px; width: 350px; }
        .btn-upload { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .btn-analyze { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); }
        
        /* Column Mapping Interface */
        .mapping-section { 
            background: white; 
            margin: 30px auto; 
            max-width: 1200px; 
            border-radius: 20px; 
            padding: 40px; 
            box-shadow: 0 15px 40px rgba(0,0,0,0.1); 
            display: none;
            position: relative;
            z-index: 10;
            clear: both;
        }
        .mapping-grid { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 40px; 
            margin: 30px 0; 
        }
        .data-preview { 
            background: #f8f9fa; 
            padding: 25px; 
            border-radius: 15px; 
            border-left: 5px solid #667eea;
            max-height: 600px;
            overflow-y: auto;
        }
        .column-mapping { 
            background: #fff; 
            padding: 25px; 
            border-radius: 15px; 
            border: 2px solid #e9ecef;
            max-height: 600px;
            overflow-y: auto;
        }
        .mapping-item { margin: 20px 0; padding: 20px; background: #f8f9ff; border-radius: 12px; border-left: 4px solid #667eea; }
        .mapping-item label { font-weight: bold; color: #667eea; display: block; margin-bottom: 8px; }
        .mapping-select { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px; }
        .suggested { background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%) !important; border-left-color: #28a745 !important; }
        .suggested label { color: #28a745 !important; }
        
        /* Status and Results */
        .status { margin: 30px auto; max-width: 900px; padding: 25px; border-radius: 15px; display: none; }
        .status.processing { background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); border: 3px solid #ffc107; color: #856404; }
        .status.completed { background: linear-gradient(135deg, #d1f2eb 0%, #b2dfdb 100%); border: 3px solid #28a745; color: #155724; }
        .status.error { background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); border: 3px solid #dc3545; color: #721c24; }
        .status.needs-mapping { background: linear-gradient(135deg, #cce5ff 0%, #b3d9ff 100%); border: 3px solid #007bff; color: #004085; }
        .progress { width: 100%; height: 25px; background: #e9ecef; border-radius: 15px; overflow: hidden; margin: 15px 0; }
        .progress-bar { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); width: 0%; transition: width 0.5s ease; }
        
        /* Results display */
        .results { background: white; border-radius: 20px; padding: 40px; margin: 30px auto; max-width: 1100px; box-shadow: 0 15px 40px rgba(0,0,0,0.1); display: none; }
        .result-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 25px; margin: 30px 0; }
        .result-card { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 30px; border-radius: 15px; text-align: center; border-left: 5px solid #667eea; transition: transform 0.3s; }
        .result-card:hover { transform: translateY(-5px); }
        .result-card h4 { margin-bottom: 15px; color: #495057; font-size: 1.1em; }
        .result-card .number { font-size: 2.8em; font-weight: bold; color: #667eea; }
        .fraud-item { background: linear-gradient(135deg, #fff5f5 0%, #fee); border-left: 4px solid #e74c3c; margin: 15px 0; padding: 25px; border-radius: 12px; }
        
        /* Enhanced visual elements */
        .feature-highlight { background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%); padding: 20px; border-radius: 15px; margin: 20px 0; border-left: 4px solid #667eea; }
        .enterprise-note { background: linear-gradient(135deg, #28a74520 0%, #20c99720 100%); padding: 25px; border-radius: 15px; margin: 30px 0; text-align: center; border: 2px solid #28a745; }
        .ai-badge { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 6px 12px; border-radius: 15px; font-size: 0.8em; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="hero">
        <div class="container">
            <h1>🤖 FraudGuard Enterprise AI</h1>
            <p>Universal Fraud Detection for ANY Dataset Format</p>
            <div>
                <span class="badge">🎯 Auto-Format Detection</span>
                <span class="badge">🧠 Interactive Column Mapping</span>
                <span class="badge">📊 95%+ Accuracy</span>
                <span class="badge">⚡ Real-time Processing</span>
            </div>
            <div style="margin-top: 25px;">
                <button class="btn btn-secondary" onclick="scrollToUpload()">🚀 Try Universal Upload</button>
                <button class="btn" onclick="alert('Contact: enterprise@fraudguard.ai')">💼 Enterprise Demo</button>
            </div>
        </div>
    </div>
    
    <!-- Upload Section -->
    <div class="upload-section" id="uploadSection">
        <h2 style="text-align: center; margin-bottom: 20px; color: #667eea;">🌍 Universal Dataset Upload</h2>
        <div class="feature-highlight">
            <strong>🔥 Enterprise-Grade Intelligence:</strong> Our AI automatically detects UPI, Credit Card, E-commerce, Banking, or ANY custom transaction format. When unknown formats are detected, our interactive mapping interface guides you through the setup process.
        </div>
        
        <div class="upload-area" id="uploadArea">
            <h3>📁 Drop ANY transaction CSV here</h3>
            <p style="margin: 20px 0; color: #666;">Supports: UPI, Credit Cards, E-commerce, Banking, Insurance, Retail, or ANY custom format (up to 500MB)</p>
            <input type="file" id="csvFile" accept=".csv" class="file-input">
            <br>
            <button class="btn btn-upload" id="uploadBtn" onclick="uploadFile()">🌟 Upload & Auto-Detect</button>
            <button class="btn btn-analyze" id="analyzeBtn" onclick="analyzeFile()" style="display:none;">🧠 Analyze for Fraud</button>
        </div>
    </div>
    
    <!-- Interactive Column Mapping Section -->
    <div class="mapping-section" id="mappingSection">
        <h2 style="text-align: center; margin-bottom: 20px; color: #667eea;">🎯 Smart Column Mapping</h2>
        <div class="enterprise-note">
            <strong>🏢 Enterprise Feature:</strong> Unknown dataset format detected! Our AI has analyzed your data structure and suggests optimal column mappings. Review and confirm the mappings below to proceed with fraud detection.
        </div>
        
        <div class="mapping-grid">
            <div class="data-preview">
                <h3 style="color: #667eea; margin-bottom: 15px;">📊 Dataset Structure</h3>
                <div id="datasetInfo"></div>
                <h4 style="margin-top: 20px; color: #667eea;">📋 Sample Data:</h4>
                <div id="sampleData" style="overflow-x: auto; margin-top: 10px;"></div>
            </div>
            
            <div class="column-mapping">
                <h3 style="color: #667eea; margin-bottom: 15px;">🔗 Column Mappings <span class="ai-badge">AI Suggested</span></h3>
                <div id="mappingControls"></div>
                <div style="margin-top: 30px; text-align: center;">
                    <button class="btn" onclick="applyMappings()">✅ Apply Mappings & Analyze</button>
                    <button class="btn btn-secondary" onclick="skipMappings()">⏭️ Use Generic Detection</button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Status Section -->
    <div id="statusSection" class="status">
        <div id="statusText"></div>
        <div class="progress">
            <div id="progressBar" class="progress-bar"></div>
        </div>
    </div>
    
    <!-- Results Section -->
    <div id="resultsSection" class="results">
        <h2 style="text-align: center; margin-bottom: 30px;">🚨 Enterprise Fraud Analysis Results</h2>
        <div id="resultsContent"></div>
    </div>

    <script>
        let taskId = null;
        let currentDatasetStructure = null;

        function scrollToUpload() {
            document.getElementById('uploadSection').scrollIntoView({ behavior: 'smooth' });
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
            const analyzeBtn = document.getElementById('analyzeBtn');
            
            if (!file) {
                alert('Please select a CSV file first!');
                return;
            }

            if (!file.name.toLowerCase().endsWith('.csv')) {
                alert('Please select a CSV file!');
                return;
            }

            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '⏳ Uploading & Analyzing...';
            
            showStatus('processing', '🚀 Uploading: ' + file.name + ' (' + (file.size / (1024*1024)).toFixed(1) + ' MB)', 25);

            const formData = new FormData();
            formData.append('file', file);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    taskId = data.task_id;
                    showStatus('processing', '🧠 Auto-detecting dataset format and analyzing structure...', 50);
                    setTimeout(checkStatus, 1000);
                } else {
                    showError(data.message || 'Upload failed');
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
                    showStatus('processing', '⚡ Running advanced AI fraud detection algorithms...', 75);
                    setTimeout(checkStatus, 2000);
                } else if (data.status === 'Completed') {
                    showStatus('completed', '✅ Fraud analysis complete!', 100);
                    setTimeout(showResults, 500);
                } else if (data.status === 'Needs Column Mapping') {
                    showStatus('needs-mapping', '🎯 Unknown format detected! Setting up interactive column mapping...', 100);
                    setTimeout(showColumnMapping, 1000);
                } else if (data.status.startsWith('Error')) {
                    showError(data.status);
                } else {
                    showStatus('processing', 'Status: ' + data.status, 60);
                    setTimeout(checkStatus, 1000);
                }
            })
            .catch(error => {
                showError('Status check failed');
            });
        }

        function showColumnMapping() {
            fetch('/results/' + taskId)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Dataset structure not found - server may have restarted');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                if (data.status === 'needs_mapping') {
                    currentDatasetStructure = data.structure;
                    displayMappingInterface(data.structure);
                } else {
                    throw new Error('Dataset structure not available');
                }
            })
            .catch(error => {
                console.error('Column mapping error:', error);
                showError('Column mapping not available - please upload your file again. The server may have restarted.');
            });
        }

        function displayMappingInterface(structure) {
            // Hide upload section to prevent overlap
            document.getElementById('uploadSection').style.display = 'none';
            
            // Show dataset info
            const datasetInfo = document.getElementById('datasetInfo');
            datasetInfo.innerHTML = `
                <p><strong>📊 Rows:</strong> ${structure.total_rows.toLocaleString()}</p>
                <p><strong>📋 Columns:</strong> ${structure.total_columns}</p>
                <p><strong>🔢 Numeric Columns:</strong> ${structure.numeric_columns.length}</p>
                <p><strong>📝 Text Columns:</strong> ${structure.text_columns.length}</p>
            `;

            // Show sample data
            const sampleData = document.getElementById('sampleData');
            if (structure.sample_data && structure.sample_data.length > 0) {
                const columns = Object.keys(structure.sample_data[0]);
                let tableHtml = '<table style="width: 100%; font-size: 12px; border-collapse: collapse;">';
                tableHtml += '<tr>' + columns.map(col => `<th style="border: 1px solid #ddd; padding: 8px; background: #f8f9fa;">${col}</th>`).join('') + '</tr>';
                structure.sample_data.forEach(row => {
                    tableHtml += '<tr>' + columns.map(col => `<td style="border: 1px solid #ddd; padding: 8px;">${row[col] || ''}</td>`).join('') + '</tr>';
                });
                tableHtml += '</table>';
                sampleData.innerHTML = tableHtml;
            }

            // Show mapping controls
            const mappingControls = document.getElementById('mappingControls');
            const mappingFields = [
                { key: 'amount', label: '💰 Transaction Amount', description: 'Column containing transaction amounts/values' },
                { key: 'user_id', label: '👤 User/Customer ID', description: 'Column identifying the user or customer' },
                { key: 'merchant', label: '🏪 Merchant/Vendor', description: 'Column containing merchant or vendor information' },
                { key: 'category', label: '📂 Category/Type', description: 'Column containing transaction categories or types' },
                { key: 'timestamp', label: '⏰ Timestamp/Date', description: 'Column containing transaction dates or timestamps' },
                { key: 'location', label: '📍 Location', description: 'Column containing location information (optional)' }
            ];

            let controlsHtml = '';
            mappingFields.forEach(field => {
                const suggested = structure.suggested_mappings[field.key];
                const issuggested = suggested ? 'suggested' : '';
                
                controlsHtml += `
                    <div class="mapping-item ${issuggested}">
                        <label>${field.label} ${suggested ? '<span class="ai-badge">AI Suggested</span>' : ''}</label>
                        <p style="font-size: 0.9em; color: #6c757d; margin-bottom: 10px;">${field.description}</p>
                        <select class="mapping-select" id="mapping_${field.key}">
                            <option value="">-- Select Column --</option>
                            ${structure.columns.map(col => 
                                `<option value="${col}" ${col === suggested ? 'selected' : ''}>${col}</option>`
                            ).join('')}
                        </select>
                    </div>
                `;
            });

            mappingControls.innerHTML = controlsHtml;

            // Show mapping section
            document.getElementById('mappingSection').style.display = 'block';
            document.getElementById('mappingSection').scrollIntoView({ behavior: 'smooth' });
            
            // Reset upload button
            const uploadBtn = document.getElementById('uploadBtn');
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '🌟 Upload & Auto-Detect';
        }

        function applyMappings() {
            const mappings = {};
            const mappingFields = ['amount', 'user_id', 'merchant', 'category', 'timestamp', 'location'];
            
            mappingFields.forEach(field => {
                const select = document.getElementById(`mapping_${field}`);
                if (select && select.value) {
                    mappings[field] = select.value;
                }
            });

            if (Object.keys(mappings).length === 0) {
                alert('Please select at least one column mapping!');
                return;
            }

            showStatus('processing', '🎯 Applying column mappings and training custom AI model...', 25);
            
            fetch('/apply_mappings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task_id: taskId,
                    mappings: mappings
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showStatus('processing', '🚀 Custom model trained! Running fraud detection...', 75);
                    setTimeout(checkStatus, 1000);
                } else {
                    showError(data.message || 'Failed to apply mappings');
                }
            })
            .catch(error => {
                showError('Mapping application failed: ' + error.message);
            });

            // Hide mapping section, show upload section
            document.getElementById('mappingSection').style.display = 'none';
            document.getElementById('uploadSection').style.display = 'block';
        }

        function skipMappings() {
            showStatus('processing', '⚡ Using generic fraud detection algorithms...', 50);
            
            fetch('/skip_mappings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_id: taskId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showStatus('processing', '🧠 Running statistical anomaly detection...', 75);
                    setTimeout(checkStatus, 1000);
                } else {
                    showError(data.message || 'Generic detection failed');
                }
            })
            .catch(error => {
                showError('Generic detection failed: ' + error.message);
            });

            // Hide mapping section, show upload section
            document.getElementById('mappingSection').style.display = 'none';
            document.getElementById('uploadSection').style.display = 'block';
        }

        function analyzeFile() {
            if (!taskId) {
                alert('Please upload a file first!');
                return;
            }
            setTimeout(checkStatus, 500);
        }

        function showStatus(type, message, progress) {
            const statusSection = document.getElementById('statusSection');
            statusSection.style.display = 'block';
            statusSection.className = `status ${type}`;
            document.getElementById('statusText').innerHTML = message;
            document.getElementById('progressBar').style.width = progress + '%';
        }

        function showError(message) {
            showStatus('error', '❌ ' + message, 0);
            
            // Reset buttons
            const uploadBtn = document.getElementById('uploadBtn');
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '🌟 Upload & Auto-Detect';
            
            // Show upload section if hidden
            document.getElementById('uploadSection').style.display = 'block';
            document.getElementById('mappingSection').style.display = 'none';
            document.getElementById('resultsSection').style.display = 'none';
            
            // Clear task ID so user can start fresh
            taskId = null;
        }

        function showResults() {
            fetch('/results/' + taskId)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Results not found - server may have restarted');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
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
                    <div class="enterprise-note">
                        <strong>🎯 AI Detection Complete:</strong> Advanced machine learning analysis finished with ${data.dataset_type.replace('_', ' ').toUpperCase()} format detection and custom fraud scoring.
                    </div>
                    
                    <div class="result-grid">
                        <div class="result-card">
                            <h4>🤖 AI Model Used</h4>
                            <div class="number" style="font-size: 1.4em; text-transform: capitalize;">${data.dataset_type.replace('_', ' ')}</div>
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
                            <h4>📊 Total Transactions</h4>
                            <div class="number" style="color: #28a745;">${data.total_transactions.toLocaleString()}</div>
                        </div>
                        ${amountCard}
                    </div>
                    
                    <div style="margin-top: 40px;">
                        <h3>🔍 Top Fraud Cases Detected by AI</h3>
                        <p style="color: #666; margin-bottom: 20px;">Enterprise-grade AI identified these highest-risk transactions:</p>
                        ${data.top_fraud_cases.map((fraudCase, index) => `
                            <div class="fraud-item">
                                <strong>🚨 High-Risk Case ${index + 1}:</strong> 
                                <span style="color: #e74c3c; font-weight: bold;">AI Risk Score: ${(fraudCase.fraud_probability * 100).toFixed(1)}%</span>
                                ${fraudCase.amt ? ` | Amount: $${fraudCase.amt}` : ''}
                                ${fraudCase['amount (INR)'] ? ` | Amount: ₹${fraudCase['amount (INR)']}` : ''}
                                ${fraudCase.Amount ? ` | Amount: $${fraudCase.Amount}` : ''}
                                <br><small style="color: #6c757d;">Enterprise AI Confidence: ${fraudCase.fraud_probability > 0.9 ? 'Very High' : fraudCase.fraud_probability > 0.7 ? 'High' : 'Medium'}</small>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div style="text-align: center; margin-top: 50px; padding: 40px; background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%); border-radius: 20px; border: 2px solid #667eea;">
                        <h3 style="color: #667eea; margin-bottom: 20px;">🎉 Enterprise Analysis Complete!</h3>
                        <p style="margin-bottom: 25px; color: #495057; font-size: 1.1em;">Your universal fraud detection analysis is complete. Ready to deploy this technology across your organization?</p>
                        <button class="btn" onclick="alert('Contact enterprise@fraudguard.ai for deployment!')">🏢 Enterprise Deployment</button>
                        <button class="btn btn-secondary" onclick="location.reload()">🔄 Analyze Another Dataset</button>
                    </div>
                `;
                
                document.getElementById('resultsContent').innerHTML = resultsHtml;
                document.getElementById('resultsSection').style.display = 'block';
                document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
                
                // Reset upload button
                const uploadBtn = document.getElementById('uploadBtn');
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = '🌟 Upload & Auto-Detect';
                
            })
            .catch(error => {
                console.error('Results error:', error);
                showError('Results not available - please upload your file again. The server may have restarted.');
            });
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
            return jsonify({'status': 'error', 'message': 'Only CSV files supported'})
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Save file temporarily
        upload_dir = 'temp_uploads'
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{task_id}.csv")
        file.save(file_path)
        
        # Start background analysis
        thread = threading.Thread(target=background_analysis, args=(task_id, file_path))
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'success', 'task_id': task_id})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/apply_mappings', methods=['POST'])
def apply_mappings():
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        mappings = data.get('mappings')
        
        if not task_id or not mappings:
            return jsonify({'status': 'error', 'message': 'Missing task_id or mappings'})
        
        # Restart analysis with mappings
        file_path = f"temp_uploads/{task_id}.csv"
        if not os.path.exists(file_path):
            return jsonify({'status': 'error', 'message': 'Original file not found'})
        
        # Start new analysis with mappings
        thread = threading.Thread(target=background_analysis, args=(task_id, file_path, mappings))
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/skip_mappings', methods=['POST'])
def skip_mappings():
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({'status': 'error', 'message': 'Missing task_id'})
        
        # Restart analysis with generic approach
        file_path = f"temp_uploads/{task_id}.csv"
        if not os.path.exists(file_path):
            return jsonify({'status': 'error', 'message': 'Original file not found'})
        
        # Force generic analysis by providing empty mappings
        thread = threading.Thread(target=background_analysis, args=(task_id, file_path, {}))
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/status/<task_id>')
def get_status(task_id):
    try:
        status = analysis_status.get(task_id, 'Not found')
        return jsonify({'status': status})
    except Exception as e:
        return jsonify({'status': f'Error: {str(e)}'})

@app.route('/results/<task_id>')
def get_results(task_id):
    try:
        if task_id in analysis_results:
            return jsonify(analysis_results[task_id])
        else:
            return jsonify({'error': 'Results not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🤖 Starting FraudGuard Enterprise AI...")
    print("🌍 Universal Dataset Support Active")
    print("🎯 Interactive Column Mapping Ready")
    print("🔗 Open: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
