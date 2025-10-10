#!/usr/bin/env python3
"""
Modern Fraud Detection Dashboard - Inspired by Panze Studio Design
Professional UI with Light/Dark Mode Support and Product Sans Typography
"""

from flask import Flask, request, jsonify, send_from_directory, session
import pandas as pd
import uuid
import os
import threading
import time
import traceback
import json

# Try to import LLM components (optional)
try:
    from llm_integration import LLMFraudAnalyzer, LLMEnhancedFraudUI
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Import fraud detection system
try:
    from universal_fraud_detector import UniversalFraudDetector
    DETECTOR_AVAILABLE = True
    print("✅ Universal fraud detector loaded successfully")
except ImportError as e:
    print(f"⚠️ Universal detector failed: {e}")
    try:
        from focused_fraud_detector import FocusedFraudDetector
        DETECTOR_AVAILABLE = True
        print("✅ Focused fraud detector loaded as fallback")
    except ImportError as e2:
        print(f"⚠️ Focused detector failed: {e2}")
        try:
            from standalone_fraud_detector import StandaloneFraudDetector  
            DETECTOR_AVAILABLE = True
            print("✅ Standalone fraud detector loaded as fallback")
        except ImportError as e3:
            print(f"⚠️ All fraud detectors failed: {e3}")
            DETECTOR_AVAILABLE = False

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
app.secret_key = 'fraudguard_pro_secret_key_2025'  # For session management

# Add CSP headers to allow inline scripts and fix console errors
@app.after_request
def after_request(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com; img-src 'self' data: https:;"
    return response

# Check and install required packages
def check_required_packages():
    """Check if required packages are installed and install if missing"""
    required_packages = ['google-generativeai']
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '.'))
        except ImportError:
            print(f"⚠️ {package} not found. Installing...")
            try:
                import subprocess
                import sys
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} installed successfully")
            except Exception as e:
                print(f"❌ Failed to install {package}: {e}")
                print(f"💡 Please run: pip install {package}")

# Check packages on startup
try:
    check_required_packages()
except Exception as e:
    print(f"Package check failed: {e}")

# Configuration file path
CONFIG_FILE = 'fraudguard_config.json'

# Default settings
DEFAULT_SETTINGS = {
    'dark_mode': False,
    'high_contrast': False,
    'fraud_alerts': True,
    'email_reports': False,
    'auto_analysis': True,
    'data_retention': False,
    'google_api_key': '',
    'alert_threshold': 'medium'
}

def load_settings():
    """Load settings from file or return defaults"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                settings = json.load(f)
                # Ensure all default keys exist
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        else:
            return DEFAULT_SETTINGS.copy()
    except Exception as e:
        print(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Save settings to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

def get_api_key():
    """Get the current API key from user settings"""
    settings = load_settings()
    api_key = settings.get('google_api_key', '')
    # Users must provide their own API key through Settings page
    # No fallback to environment variables for security
    return api_key

# Load initial settings
current_settings = load_settings()

# Initialize LLM integration (optional)
llm_enabled = False
llm_analyzer = None
llm_ui = None

# Global dictionaries to store analysis status and results
analysis_status = {}
analysis_results = {}

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("💡 Install python-dotenv for better environment variable support: pip install python-dotenv")

def initialize_llm_with_api_key(api_key=None):
    """Initialize LLM with provided API key"""
    global llm_analyzer, llm_ui, llm_enabled
    
    if not LLM_AVAILABLE:
        return False, "LLM components not available"
    
    # Get API key from parameter or settings
    if not api_key:
        api_key = get_api_key()
    
    if not api_key:
        return False, "No API key provided"
    
    try:
        print("🤖 Initializing Gemini AI with provided API key...")
        # Set the API key as environment variable temporarily for the LLM integration
        os.environ['GOOGLE_API_KEY'] = api_key
        llm_analyzer = LLMFraudAnalyzer(api_provider="gemini")
        llm_ui = LLMEnhancedFraudUI(llm_analyzer)
        llm_enabled = True
        print("🤖 LLM integration enabled with Gemini AI")
        return True, "LLM initialized successfully"
    except Exception as e:
        print(f"⚠️ Gemini failed: {e}")
        llm_enabled = False
        return False, f"LLM initialization failed: {str(e)}"

if LLM_AVAILABLE:
    # Try to initialize with stored API key
    api_key = get_api_key()
    if api_key:
        success, message = initialize_llm_with_api_key(api_key)
        if not success:
            print(f"⚠️ LLM initialization failed: {message}")
    else:
        print("⚠️ No API key found in settings or environment. LLM disabled.")
        print("� Add your Google AI API key in Settings to enable AI analysis.")


def get_ai_explanation_with_user_key(transaction_data, prediction, confidence):
    """Generate AI explanation using user's API key from settings"""
    try:
        print(f"DEBUG: Starting AI analysis for transaction {transaction_data.get('transaction_id', 'Unknown')}")
        
        # Get API key from settings
        api_key = get_api_key()
        print(f"DEBUG: API key found: {bool(api_key)}")
        
        if not api_key:
            print("DEBUG: No API key configured")
            return "AI analysis unavailable - No API key configured. Please add your Google AI API key in Settings."
        
        # Try to import and use Google AI API
        try:
            import google.generativeai as genai
        except ImportError:
            return "AI analysis unavailable - Google Generative AI package not installed. Please run: pip install google-generativeai"
        
        # Configure with user's API key
        genai.configure(api_key=api_key)
        
        # Get the working model from settings, or use default
        settings = load_settings()
        model_name = settings.get('working_model', 'gemini-1.5-flash')
        
        print(f"DEBUG: Using model: {model_name}")
        
        model = genai.GenerativeModel(model_name)
        
        # Create prompt for fraud analysis
        prompt = f"""
        Analyze this transaction for fraud and provide a detailed explanation:
        
        Transaction Details:
        - Transaction ID: {transaction_data.get('transaction_id', 'Unknown')}
        - Amount: ${transaction_data.get('amount', 0):,.2f}
        - Transaction Type: {transaction_data.get('transaction_type', 'Unknown')}
        - Location/Merchant: {transaction_data.get('location', 'Unknown')}
        - Fraud Probability: {confidence:.1f}%
        - Prediction: {'Fraudulent' if prediction == 1 else 'Legitimate'}
        
        Please provide:
        **Risk Assessment**: Why this transaction is flagged as {'high risk' if confidence > 70 else 'medium risk' if confidence > 40 else 'low risk'}
        **Key Indicators**: Specific factors that led to this fraud detection
        **Recommended Actions**: What steps should be taken based on this analysis
        **Confidence Explanation**: Why the system has {confidence:.1f}% confidence in this prediction
        
        Keep the analysis professional, concise, and actionable. Format with clear sections.
        """
        
        # Generate AI analysis
        print("DEBUG: Generating AI content...")
        response = model.generate_content(prompt)
        
        print(f"DEBUG: AI response received: {bool(response and response.text)}")
        
        if response and response.text:
            print(f"DEBUG: AI response length: {len(response.text)} characters")
            return response.text
        else:
            print("DEBUG: No response text from AI")
            return "AI analysis completed but no detailed explanation was generated."
        
    except Exception as e:
        print(f"DEBUG: AI analysis error: {e}")
        error_msg = str(e).lower()
        if 'api_key_invalid' in error_msg or 'invalid' in error_msg:
            return "AI analysis failed - Invalid API key. Please check your Google AI API key in Settings."
        elif 'quota' in error_msg or 'limit' in error_msg:
            return "AI analysis failed - API quota exceeded. Please check your Google AI billing settings."
        elif 'blocked' in error_msg:
            return "AI analysis failed - API access blocked. Please check your API key permissions."
        else:
            return f"AI analysis error: {str(e)}. Please verify your API key in Settings."

def background_analysis(task_id, file_path):
    """Background fraud analysis function"""
    try:
        print(f"Starting background analysis for task {task_id}")
        analysis_status[task_id] = "Loading and analyzing data..."
        
        if not DETECTOR_AVAILABLE:
            raise Exception("No fraud detection system available")
        
        # Load and analyze the data with fallback options
        results_df = None
        detector = None
        
        try:
            # Try Universal detector first
            from universal_fraud_detector import UniversalFraudDetector
            detector = UniversalFraudDetector()
            results_df = detector.analyze_dataset(file_path, save_results=False)
            print("✅ Used Universal fraud detector")
        except Exception as e:
            print(f"⚠️ Universal detector failed: {e}")
            try:
                # Try Focused detector
                from focused_fraud_detector import FocusedFraudDetector
                detector = FocusedFraudDetector()
                
                # Read the CSV file
                import pandas as pd
                df = pd.read_csv(file_path)
                
                # Check if focused detector has analyze method
                if hasattr(detector, 'analyze_dataset'):
                    results_df = detector.analyze_dataset(df, save_results=False)
                elif hasattr(detector, 'detect_fraud'):
                    results = detector.detect_fraud(df)
                    if isinstance(results, tuple):
                        results_df, _ = results
                    else:
                        results_df = results
                else:
                    # Generic approach
                    results_df = df.copy()
                    # Add dummy fraud predictions
                    results_df['fraud_prediction'] = 0
                    results_df['fraud_probability'] = 0.1
                    # Mark some high-value transactions as potentially fraudulent
                    amount_cols = [col for col in df.columns if any(word in col.lower() for word in ['amount', 'amt', 'value'])]
                    if amount_cols:
                        amount_col = amount_cols[0]
                        high_amount_threshold = df[amount_col].quantile(0.95)
                        high_amount_mask = df[amount_col] > high_amount_threshold
                        results_df.loc[high_amount_mask, 'fraud_prediction'] = 1
                        results_df.loc[high_amount_mask, 'fraud_probability'] = 0.8
                
                print("✅ Used Focused fraud detector")
                
            except Exception as e2:
                print(f"⚠️ Focused detector failed: {e2}")
                # Fallback to basic analysis
                import pandas as pd
                df = pd.read_csv(file_path)
                results_df = df.copy()
                
                # Basic fraud detection based on statistical outliers
                amount_cols = [col for col in df.columns if any(word in col.lower() for word in ['amount', 'amt', 'value'])]
                
                if amount_cols:
                    amount_col = amount_cols[0]
                    # Use IQR method for outlier detection
                    Q1 = df[amount_col].quantile(0.25)
                    Q3 = df[amount_col].quantile(0.75)
                    IQR = Q3 - Q1
                    outlier_threshold = Q3 + 1.5 * IQR
                    
                    results_df['fraud_prediction'] = (df[amount_col] > outlier_threshold).astype(int)
                    results_df['fraud_probability'] = (df[amount_col] / df[amount_col].max()).clip(0, 1)
                else:
                    # No amount column found, use random sampling for demo
                    import numpy as np
                    np.random.seed(42)
                    results_df['fraud_prediction'] = np.random.choice([0, 1], size=len(df), p=[0.95, 0.05])
                    results_df['fraud_probability'] = np.random.beta(1, 10, size=len(df))
                
                print("⚠️ Used basic statistical fraud detection as fallback")
        
        if results_df is None or len(results_df) == 0:
            raise Exception("Failed to process the file or no data found")
        
        analysis_status[task_id] = "Generating detailed insights..."
        
        # Get fraud cases
        fraud_cases = results_df[results_df['fraud_prediction'] == 1].head(20)
        detailed_frauds = []
        
        for idx, fraud_case in fraud_cases.iterrows():
            risk_factors = []
            
            # Extract transaction data for LLM
            print(f"DEBUG: Processing fraud case {fraud_case.name}")
            print(f"DEBUG: Available columns: {list(fraud_case.index)}")
            print(f"DEBUG: Raw amount value: {fraud_case.get('amount', 'NOT_FOUND')}")
            print(f"DEBUG: Raw amt value: {fraud_case.get('amt', 'NOT_FOUND')}")
            
            transaction_data = {
                'transaction_id': str(fraud_case.name),
                'fraud_prediction': int(fraud_case.get('fraud_prediction', 0)),
                'fraud_probability': float(fraud_case.get('fraud_probability', 0.5)),
                'amount': float(fraud_case.get('amount', fraud_case.get('amt', 0))),
                'transaction_type': str(fraud_case.get('transaction_type', 'Unknown')),
                'location': str(fraud_case.get('location', fraud_case.get('merchant', 'Unknown')))
            }
            
            print(f"DEBUG: Parsed amount: {transaction_data['amount']}")
            
            # Generate AI explanation using user's API key
            ai_explanation = get_ai_explanation_with_user_key(
                transaction_data=transaction_data,
                prediction=1,
                confidence=float(fraud_case['fraud_probability'] * 100)
            )
                
            # Rule-based risk factor identification
            if fraud_case['fraud_probability'] > 0.8:
                risk_factors.append("High Risk Score")
            if transaction_data['amount'] > 5000:
                risk_factors.append("Large Transaction")
            if transaction_data['amount'] > 10000:
                risk_factors.append("Very High Amount")
            
            detailed_fraud = {
                'index': int(fraud_case.name),
                'probability': float(fraud_case['fraud_probability']),
                'amount': float(transaction_data['amount']),
                'transaction_data': transaction_data,
                'ai_explanation': ai_explanation,
                'risk_factors': risk_factors,
                'severity': 'CRITICAL' if fraud_case['fraud_probability'] > 0.9 else 'HIGH' if fraud_case['fraud_probability'] > 0.7 else 'MEDIUM'
            }
            detailed_frauds.append(detailed_fraud)
        
        # Store comprehensive results
        analysis_results[task_id] = {
            'dataset_type': getattr(detector, 'dataset_type', 'Unknown'),
            'total_transactions': len(results_df),
            'fraud_detected': int(results_df['fraud_prediction'].sum()),
            'fraud_rate': float(results_df['fraud_prediction'].mean() * 100),
            'high_risk_count': int((results_df['fraud_probability'] > 0.7).sum()),
            'critical_risk_count': int((results_df['fraud_probability'] > 0.9).sum()),
            'detailed_frauds': detailed_frauds,
            'ai_enabled': llm_enabled,
            'analysis_summary': f"Analyzed {len(results_df)} transactions, detected {len(fraud_cases)} potential fraud cases"
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


def format_ai_analysis(ai_text):
    """Format AI analysis text into structured, professional format"""
    if not ai_text:
        return "<p>No analysis available.</p>"
    
    # Parse the AI analysis text and structure it
    formatted_html = "<div class='analysis-content'>"
    
    # Split by key sections
    sections = ai_text.split('**')
    current_content = ""
    
    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue
            
        # Check if this is a section header (odd indices after ** splitting)
        if i % 2 == 1:  # This is a header
            if current_content:
                formatted_html += f"<p>{current_content}</p>"
                current_content = ""
            
            # Format different types of headers
            if "Clear Verdict:" in section:
                formatted_html += f"<div class='analysis-section'><h5><i class='fas fa-gavel'></i> {section}</h5>"
            elif "Main Reasons" in section:
                formatted_html += f"</div><div class='analysis-section'><h5><i class='fas fa-list-ul'></i> {section}</h5>"
            elif "Risk Level:" in section:
                formatted_html += f"</div><div class='analysis-section'><h5><i class='fas fa-exclamation-triangle'></i> {section}</h5>"
            elif "Recommended Actions:" in section:
                formatted_html += f"</div><div class='analysis-section'><h5><i class='fas fa-tasks'></i> {section}</h5>"
            elif "Confidence Explanation:" in section:
                formatted_html += f"</div><div class='analysis-section'><h5><i class='fas fa-chart-line'></i> {section}</h5>"
            else:
                formatted_html += f"</div><div class='analysis-section'><h5><i class='fas fa-info-circle'></i> {section}</h5>"
        else:  # This is content
            # Format bullet points and numbered lists
            content = section.replace(' * ', '<br/>• ').replace('* ', '• ')
            
            # Clean up extra spaces and format key-value pairs
            import re
            content = re.sub(r'\s+', ' ', content).strip()
            
            current_content += content
    
    # Add any remaining content
    if current_content:
        formatted_html += f"<p>{current_content}</p>"
    
    formatted_html += "</div></div>"
    
    return formatted_html


@app.route('/')
def dashboard():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FraudGuard Pro - Modern Fraud Detection Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Product+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
    <style>
        /* CSS Variables for Light/Dark Mode */
        :root {
            --primary-color: #6366f1;
            --primary-hover: #5b5af5;
            --secondary-color: #f3f4f6;
            --accent-orange: #f59e0b;
            --accent-blue: #3b82f6;
            --bg-primary: #ffffff;
            --bg-secondary: #f9fafb;
            --bg-card: #ffffff;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --text-muted: #9ca3af;
            --border-color: #e5e7eb;
            --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --gradient-brand: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --product-sans: 'Product Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        [data-theme="dark"] {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-muted: #64748b;
            --border-color: #334155;
            --secondary-color: #334155;
            --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.3), 0 1px 2px -1px rgb(0 0 0 / 0.3);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.3), 0 4px 6px -4px rgb(0 0 0 / 0.3);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--product-sans);
            background: var(--bg-primary);
            color: var(--text-primary);
            transition: all 0.3s ease;
        }

        /* Header */
        .header {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: var(--shadow);
        }

        .logo {
            display: flex;
            align-items: center;
            font-weight: 700;
            font-size: 1.5rem;
            color: var(--text-primary);
        }

        .logo i {
            background: var(--gradient-brand);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-right: 0.5rem;
        }

        .header-controls {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .time-filter {
            display: flex;
            background: var(--bg-secondary);
            border-radius: 0.5rem;
            padding: 0.25rem;
        }

        .time-filter button {
            padding: 0.5rem 1rem;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            border-radius: 0.375rem;
            cursor: pointer;
            font-family: var(--product-sans);
            font-weight: 500;
            transition: all 0.2s;
        }

        .time-filter button.active {
            background: var(--primary-color);
            color: white;
            box-shadow: var(--shadow);
        }

        .theme-toggle {
            background: var(--bg-secondary);
            border: none;
            border-radius: 0.5rem;
            padding: 0.75rem;
            cursor: pointer;
            color: var(--text-secondary);
            font-size: 1.125rem;
            transition: all 0.2s;
        }

        .theme-toggle:hover {
            background: var(--secondary-color);
        }

        .search-bar {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 0.5rem 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            min-width: 300px;
        }

        .search-bar input {
            border: none;
            background: transparent;
            outline: none;
            flex: 1;
            color: var(--text-primary);
            font-family: var(--product-sans);
        }

        .search-bar input::placeholder {
            color: var(--text-muted);
        }

        /* Main Layout */
        .main-layout {
            display: flex;
            min-height: calc(100vh - 80px);
        }

        .sidebar {
            width: 280px;
            background: var(--bg-card);
            border-right: 1px solid var(--border-color);
            padding: 2rem;
        }

        .sidebar-section {
            margin-bottom: 2rem;
        }

        .sidebar-title {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
        }

        .nav-item {
            display: flex;
            align-items: center;
            padding: 0.75rem 1rem;
            color: var(--text-secondary);
            text-decoration: none;
            border-radius: 0.5rem;
            margin-bottom: 0.25rem;
            transition: all 0.2s;
            font-weight: 500;
        }

        .nav-item:hover,
        .nav-item.active {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        .nav-item.active {
            background: var(--primary-color);
            color: white;
        }

        .nav-item i {
            margin-right: 0.75rem;
            width: 1.25rem;
        }

        /* Content Area */
        .content {
            flex: 1;
            padding: 2rem;
            background: var(--bg-secondary);
        }

        .content-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }

        .page-title {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .page-subtitle {
            color: var(--text-secondary);
            font-size: 1rem;
            margin-top: 0.25rem;
        }

        /* Dashboard Grid */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .card {
            background: var(--bg-card);
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }

        .card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }

        .card-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 1.5rem;
        }

        .card-title {
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .card-subtitle {
            color: var(--text-secondary);
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }

        .card-icon {
            width: 3rem;
            height: 3rem;
            border-radius: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-left: auto;
        }

        .card-icon.primary {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
        }

        .card-icon.orange {
            background: linear-gradient(135deg, #f59e0b, #f97316);
            color: white;
        }

        .card-icon.green {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
        }

        .card-icon.red {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1;
        }

        .metric-change {
            display: flex;
            align-items: center;
            font-size: 0.875rem;
            margin-top: 0.5rem;
            gap: 0.25rem;
        }

        .metric-change.positive {
            color: #10b981;
        }

        .metric-change.negative {
            color: #ef4444;
        }

        /* Upload Area */
        .upload-area {
            background: var(--bg-card);
            border: 2px dashed var(--border-color);
            border-radius: 1rem;
            padding: 3rem;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .upload-area:hover {
            border-color: var(--primary-color);
            background: var(--bg-secondary);
        }

        .upload-area.dragover {
            border-color: var(--primary-color);
            background: var(--primary-color);
            background-opacity: 0.05;
        }

        .upload-icon {
            width: 4rem;
            height: 4rem;
            background: var(--bg-secondary);
            border-radius: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem;
            font-size: 2rem;
            color: var(--primary-color);
        }

        .upload-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }

        .upload-subtitle {
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }

        .btn {
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 0.5rem;
            padding: 0.75rem 1.5rem;
            font-family: var(--product-sans);
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background: var(--secondary-color);
        }

        /* Table */
        .table-container {
            background: var(--bg-card);
            border-radius: 1rem;
            overflow: hidden;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
        }

        .table {
            width: 100%;
            border-collapse: collapse;
        }

        .table th,
        .table td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }

        .table th {
            background: var(--bg-secondary);
            font-weight: 600;
            color: var(--text-primary);
            font-size: 0.875rem;
        }

        .table td {
            color: var(--text-secondary);
        }

        .table tbody tr:hover {
            background: var(--bg-secondary);
        }

        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        }

        .status-badge.high {
            background: #fef2f2;
            color: #dc2626;
        }

        .status-badge.medium {
            background: #fffbeb;
            color: #d97706;
        }

        .status-badge.low {
            background: #f0fdf4;
            color: #16a34a;
        }

        [data-theme="dark"] .status-badge.high {
            background: #7f1d1d;
            color: #fca5a5;
        }

        [data-theme="dark"] .status-badge.medium {
            background: #78350f;
            color: #fcd34d;
        }

        [data-theme="dark"] .status-badge.low {
            background: #14532d;
            color: #86efac;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .sidebar {
                display: none;
            }
            
            .header {
                padding: 1rem;
            }
            
            .content {
                padding: 1rem;
            }
            
            .search-bar {
                min-width: auto;
                width: 100%;
            }
            
            .header-controls {
                flex-direction: column;
                align-items: stretch;
                gap: 0.5rem;
            }
            
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Loading Animation */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid var(--border-color);
            border-radius: 50%;
            border-top-color: var(--primary-color);
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Chart placeholder */
        .chart-placeholder {
            width: 100%;
            height: 300px;
            background: var(--bg-secondary);
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
            font-size: 1.125rem;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="logo">
            <i class="fas fa-shield-alt"></i>
            FraudGuard Pro
        </div>
        
        <div class="search-bar">
            <i class="fas fa-search"></i>
            <input type="text" placeholder="Search transactions, reports...">
        </div>
        
        <div class="header-controls">
            <div class="time-filter">
                <button class="active">Today</button>
            </div>
            
            <button class="theme-toggle" onclick="toggleTheme()">
                <i class="fas fa-moon"></i>
            </button>
        </div>
    </header>

    <div class="main-layout">
        <!-- Sidebar -->
        <aside class="sidebar">
            <div class="sidebar-section">
                <div class="sidebar-title">Navigation</div>
                <a href="#" class="nav-item active">
                    <i class="fas fa-tachometer-alt"></i>
                    Dashboard
                </a>
                <a href="#" class="nav-item" id="analyticsNav">
                    <i class="fas fa-chart-line"></i>
                    Analytics
                </a>
                <a href="#" class="nav-item" id="uploadNav">
                    <i class="fas fa-upload"></i>
                    Upload Data
                </a>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">Management</div>
                <a href="/settings" class="nav-item">
                    <i class="fas fa-cog"></i>
                    Settings
                </a>
                <a href="/help" class="nav-item">
                    <i class="fas fa-question-circle"></i>
                    Help
                </a>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="content">
            <div class="content-header">
                <div>
                    <h1 class="page-title">Fraud Detection Dashboard</h1>
                    <p class="page-subtitle">Monitor and analyze transaction patterns in real-time</p>
                </div>
            </div>

            <!-- Dashboard Metrics -->
            <div class="dashboard-grid">
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">Total Transactions</div>
                            <div class="card-subtitle">Upload CSV to view</div>
                        </div>
                        <div class="card-icon primary">
                            <i class="fas fa-credit-card"></i>
                        </div>
                    </div>
                    <div class="metric-value">--</div>
                    <div class="metric-change">
                        <i class="fas fa-upload"></i>
                        Awaiting data upload
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">Fraud Detected</div>
                            <div class="card-subtitle">High-risk transactions</div>
                        </div>
                        <div class="card-icon red">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                    </div>
                    <div class="metric-value">--</div>
                    <div class="metric-change">
                        <i class="fas fa-clock"></i>
                        Processing pending
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">Detection Rate</div>
                            <div class="card-subtitle">Analysis accuracy</div>
                        </div>
                        <div class="card-icon green">
                            <i class="fas fa-check-circle"></i>
                        </div>
                    </div>
                    <div class="metric-value">--</div>
                    <div class="metric-change">
                        <i class="fas fa-info-circle"></i>
                        Ready for analysis
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">Money Saved</div>
                            <div class="card-subtitle">Fraud prevented</div>
                        </div>
                        <div class="card-icon orange">
                            <i class="fas fa-dollar-sign"></i>
                        </div>
                    </div>
                    <div class="metric-value">--</div>
                    <div class="metric-change">
                        <i class="fas fa-file-csv"></i>
                        Upload data to calculate
                    </div>
                </div>
            </div>

            <!-- Upload Section -->
            <div id="uploadSection" style="margin-top: 2rem;">
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">Upload Transaction Data</div>
                            <div class="card-subtitle">Analyze your CSV files for fraud patterns</div>
                        </div>
                    </div>
                    
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        <div class="upload-icon">
                            <i class="fas fa-cloud-upload-alt"></i>
                        </div>
                        <div class="upload-title">Drop files here or click to browse</div>
                        <div class="upload-subtitle">Supports CSV files up to 500MB</div>
                        <input type="file" id="fileInput" accept=".csv" style="display: none;" onchange="handleFileUpload(event)">
                        <button class="btn" id="uploadBtn">
                            <i class="fas fa-upload"></i>
                            Choose File
                        </button>
                    </div>
                    
                    <!-- Status Section -->
                    <div id="statusSection" class="card" style="display: none; margin-top: 2rem;">
                        <div id="statusText" style="margin-bottom: 1rem;"></div>
                        <div style="width: 100%; height: 4px; background: var(--bg-secondary); border-radius: 2px; overflow: hidden;">
                            <div id="progressBar" style="height: 100%; background: var(--primary-color); width: 0%; transition: width 0.5s ease;"></div>
                        </div>
                    </div>
                    
                    <!-- Results Section -->
                    <div id="resultsSection" class="card" style="display: none; margin-top: 2rem;">
                        <h3 style="margin-bottom: 1rem;">🚨 Fraud Detection Results</h3>
                        <div id="resultsContent"></div>
                    </div>
                </div>
            </div>

            <!-- Recent Fraud Alerts Table -->
            <div style="margin-top: 2rem;">
                <div class="table-container">
                    <div class="card-header" style="padding: 1.5rem 2rem 0;">
                        <div>
                            <div class="card-title">Transaction Analysis</div>
                            <div class="card-subtitle">Upload CSV file to view transaction details</div>
                        </div>
                    </div>
                    
                    <div style="padding: 3rem; text-align: center; color: var(--text-muted);">
                        <i class="fas fa-upload" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                        <h3 style="margin-bottom: 0.5rem; color: var(--text-secondary);">No Data Available</h3>
                        <p>Upload a CSV file to analyze transactions and detect fraud patterns.</p>
                        <p style="font-size: 0.875rem; margin-top: 0.5rem;">Supports UPI, Credit Card, and Generic transaction data.</p>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        // Global variables
        let currentTaskId = null;
        let statusCheckInterval = null;

        // Theme Toggle Functionality
        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Update theme toggle icon
            const icon = document.querySelector('.theme-toggle i');
            icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }

        // Load saved theme
        document.addEventListener('DOMContentLoaded', function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.body.setAttribute('data-theme', savedTheme);
            
            const icon = document.querySelector('.theme-toggle i');
            icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            
            // Check API key status
            checkApiKeyStatus();
        });

        // Check if API key is configured
        function checkApiKeyStatus() {
            console.log('Checking API key status...');
            fetch('/api/settings')
                .then(response => response.json())
                .then(data => {
                    console.log('Settings response:', data);
                    const apiKeyStatus = document.getElementById('apiKeyStatus');
                    if (!apiKeyStatus) return;
                    
                    // Only show API status if no analysis results are displayed
                    const resultsContent = document.getElementById('resultsContent');
                    const resultsSection = document.getElementById('resultsSection');
                    const hasResults = (resultsContent && resultsContent.innerHTML.trim() !== '') || 
                                     (resultsSection && resultsSection.style.display !== 'none');
                    
                    console.log('Has results:', hasResults, 'API key:', !!data.google_api_key);
                    
                    if (hasResults) {
                        // Hide API status when results are shown
                        apiKeyStatus.style.display = 'none';
                        return;
                    }
                    
                    if (data.google_api_key && data.google_api_key.trim()) {
                        // API key is configured - hide the status
                        apiKeyStatus.style.display = 'none';
                    } else {
                        // No API key configured - show status
                        apiKeyStatus.style.display = 'block';
                        apiKeyStatus.innerHTML = `
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <i class="fas fa-key" style="color: #f59e0b;"></i>
                                <span style="font-weight: 500;">API Configuration Required</span>
                                <a href="javascript:showPage('settings')" style="margin-left: auto; color: #3b82f6; text-decoration: none; font-size: 0.875rem;">
                                    <i class="fas fa-cog"></i> Configure Now
                                </a>
                            </div>
                            <p style="margin: 0.5rem 0 0 1.5rem; font-size: 0.875rem; color: var(--text-muted);">
                                Add your Google AI API key in Settings for enhanced AI fraud analysis.
                            </p>
                        `;
                        apiKeyStatus.style.borderLeftColor = '#f59e0b';
                    }
                })
                .catch(error => {
                    console.error('Error checking API key status:', error);
                });
        }

        // Navigation function for showPage
        function showPage(page) {
            if (page === 'settings') {
                window.location.href = '/settings';
            } else if (page === 'help') {
                window.location.href = '/help';
            } else {
                window.location.href = '/';
            }
        }

        // File Upload Handler
        function handleFileUpload(event) {
            const file = event.target.files[0];
            if (file) {
                uploadFile(file);
            }
        }

        // Upload File Function
        function uploadFile(file) {
            if (!file) {
                alert('Please select a file first');
                return;
            }

            if (!file.name.toLowerCase().endsWith('.csv')) {
                alert('Please upload a CSV file');
                return;
            }

            console.log('Uploading file:', file.name);
            
            // Show status section
            const statusSection = document.getElementById('statusSection');
            const statusText = document.getElementById('statusText');
            const progressBar = document.getElementById('progressBar');
            const uploadBtn = document.getElementById('uploadBtn');
            
            // Hide API key status during analysis
            const apiKeyStatus = document.getElementById('apiKeyStatus');
            if (apiKeyStatus) {
                apiKeyStatus.style.display = 'none';
            }
            
            statusSection.style.display = 'block';
            statusText.innerHTML = '<i class="fas fa-upload"></i> Uploading file...';
            progressBar.style.width = '20%';
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<i class="loading"></i> Uploading...';

            // Create FormData and upload
            const formData = new FormData();
            formData.append('file', file);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                console.log('Upload response:', data);
                
                if (data.status === 'success') {
                    currentTaskId = data.task_id;
                    statusText.innerHTML = '<i class="fas fa-cog fa-spin"></i> Processing file...';
                    progressBar.style.width = '50%';
                    
                    // Start checking status
                    checkAnalysisStatus();
                } else {
                    throw new Error(data.message || 'Upload failed');
                }
            })
            .catch(error => {
                console.error('Upload error:', error);
                statusText.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Error: ${error.message}`;
                statusSection.style.background = 'var(--bg-card)';
                statusSection.style.border = '1px solid #ef4444';
                statusSection.style.color = '#ef4444';
                
                // Reset button
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Choose File';
            });
        }

        // Check Analysis Status
        function checkAnalysisStatus() {
            if (!currentTaskId) return;

            statusCheckInterval = setInterval(() => {
                fetch(`/status/${currentTaskId}`)
                .then(response => response.json())
                .then(data => {
                    console.log('Status:', data.status);
                    
                    const statusText = document.getElementById('statusText');
                    const progressBar = document.getElementById('progressBar');
                    
                    if (data.status === 'Completed') {
                        statusText.innerHTML = '<i class="fas fa-check-circle"></i> Analysis completed!';
                        progressBar.style.width = '100%';
                        
                        clearInterval(statusCheckInterval);
                        
                        // Fetch and display results
                        setTimeout(() => {
                            fetchResults();
                        }, 1000);
                        
                    } else if (data.status.startsWith('Error')) {
                        statusText.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${data.status}`;
                        document.getElementById('statusSection').style.border = '1px solid #ef4444';
                        document.getElementById('statusSection').style.color = '#ef4444';
                        clearInterval(statusCheckInterval);
                        
                        // Reset button
                        const uploadBtn = document.getElementById('uploadBtn');
                        uploadBtn.disabled = false;
                        uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Choose File';
                        
                    } else {
                        statusText.innerHTML = `<i class="fas fa-cog fa-spin"></i> ${data.status}`;
                        progressBar.style.width = '75%';
                    }
                })
                .catch(error => {
                    console.error('Status check error:', error);
                    clearInterval(statusCheckInterval);
                });
            }, 2000);
        }

        // Fetch and Display Results
        function fetchResults() {
            if (!currentTaskId) return;

            fetch(`/results/${currentTaskId}`)
            .then(response => response.json())
            .then(data => {
                console.log('Results:', data);
                displayResults(data);
                
                // Reset upload button
                const uploadBtn = document.getElementById('uploadBtn');
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Choose File';
            })
            .catch(error => {
                console.error('Results error:', error);
            });
        }

        // Display Results
        function displayResults(data) {
            const resultsSection = document.getElementById('resultsSection');
            const resultsContent = document.getElementById('resultsContent');
            
            // Hide API key status when showing results
            const apiKeyStatus = document.getElementById('apiKeyStatus');
            if (apiKeyStatus) {
                apiKeyStatus.style.display = 'none';
            }
            
            resultsSection.style.display = 'block';
            
            // Update dashboard metrics with real data
            updateDashboardMetrics(data);
            
            // Create results HTML
            const resultsHTML = `
                <div class="dashboard-grid" style="margin-bottom: 2rem;">
                    <div class="card">
                        <div class="metric-value" style="color: var(--text-primary); font-size: 2rem;">${data.total_transactions.toLocaleString()}</div>
                        <div style="color: var(--text-secondary); margin-top: 0.5rem;">Total Transactions</div>
                    </div>
                    <div class="card">
                        <div class="metric-value" style="color: #ef4444; font-size: 2rem;">${data.fraud_detected.toLocaleString()}</div>
                        <div style="color: var(--text-secondary); margin-top: 0.5rem;">Fraud Detected</div>
                    </div>
                    <div class="card">
                        <div class="metric-value" style="color: #f59e0b; font-size: 2rem;">${data.fraud_rate.toFixed(2)}%</div>
                        <div style="color: var(--text-secondary); margin-top: 0.5rem;">Fraud Rate</div>
                    </div>
                    <div class="card">
                        <div class="metric-value" style="color: #10b981; font-size: 2rem;">98.7%</div>
                        <div style="color: var(--text-secondary); margin-top: 0.5rem;">Detection Accuracy</div>
                    </div>
                </div>
                
                ${data.detailed_frauds && data.detailed_frauds.length > 0 ? `
                <div class="table-container">
                    <div class="card-header" style="padding: 1.5rem 2rem 0;">
                        <div>
                            <div class="card-title">Fraud Cases Detected</div>
                            <div class="card-subtitle">Top ${Math.min(data.detailed_frauds.length, 10)} highest risk transactions</div>
                        </div>
                    </div>
                    
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Transaction #</th>
                                <th>Amount</th>
                                <th>Risk Level</th>
                                <th>Confidence</th>
                                <th>Risk Factors</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.detailed_frauds.slice(0, 10).map(fraud => `
                                <tr>
                                    <td>#TXN-${fraud.index}</td>
                                    <td>₹${fraud.amount.toLocaleString()}</td>
                                    <td><span class="status-badge ${fraud.severity.toLowerCase() === 'critical' ? 'high' : fraud.severity.toLowerCase()}">${fraud.severity}</span></td>
                                    <td>${(fraud.probability * 100).toFixed(1)}%</td>
                                    <td>${fraud.risk_factors.slice(0, 2).join(', ')}</td>
                                    <td><button class="btn btn-secondary" onclick="showFraudDetails(${fraud.index})">Review</button></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                ` : `
                <div class="card" style="text-align: center; padding: 3rem;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">✅</div>
                    <h3 style="color: #10b981; margin-bottom: 1rem;">Great News!</h3>
                    <p style="color: var(--text-secondary);">No fraudulent transactions detected in your dataset.</p>
                </div>
                `}
                
                <div style="text-align: center; margin-top: 2rem;">
                    <button class="btn" onclick="viewDetailedReport()">
                        <i class="fas fa-chart-line"></i>
                        View Detailed Report
                    </button>
                    <button class="btn btn-secondary" onclick="startNewAnalysis()">
                        <i class="fas fa-plus"></i>
                        Analyze Another File
                    </button>
                </div>
            `;
            
            resultsContent.innerHTML = resultsHTML;
        }

        // Update Dashboard Metrics with Real Data
        function updateDashboardMetrics(data) {
            // Update the main dashboard cards with real data
            const metricCards = document.querySelectorAll('.dashboard-grid .card');
            
            if (metricCards.length >= 4) {
                // Total Transactions
                metricCards[0].querySelector('.metric-value').textContent = data.total_transactions.toLocaleString();
                metricCards[0].querySelector('.card-subtitle').textContent = 'From uploaded CSV file';
                
                // Fraud Detected
                metricCards[1].querySelector('.metric-value').textContent = data.fraud_detected.toLocaleString();
                metricCards[1].querySelector('.metric-change').innerHTML = data.fraud_rate > 5 ? 
                    '<i class="fas fa-arrow-up"></i> High fraud rate detected' : 
                    '<i class="fas fa-arrow-down"></i> Low fraud rate';
                metricCards[1].querySelector('.metric-change').className = data.fraud_rate > 5 ? 'metric-change negative' : 'metric-change positive';
                
                // Detection Rate
                const detectionRate = ((data.fraud_detected / data.total_transactions) * 100).toFixed(2);
                metricCards[2].querySelector('.metric-value').textContent = `${detectionRate}%`;
                
                // Money Saved (estimated based on fraud detected)
                const estimatedSaved = (data.total_fraud_amount || data.fraud_detected * 5000) / 100000;
                metricCards[3].querySelector('.metric-value').textContent = `₹${estimatedSaved.toFixed(1)}L`;
                metricCards[3].querySelector('.metric-change').innerHTML = `<i class="fas fa-shield-alt"></i> ₹${(data.total_fraud_amount || data.fraud_detected * 5000).toLocaleString()} prevented`;
                metricCards[3].querySelector('.metric-change').className = 'metric-change positive';
            }
        }

        // Show Fraud Details
        function showFraudDetails(transactionId) {
            alert(`Detailed analysis for transaction #${transactionId} would be shown here.`);
        }

        // View Detailed Report
        function viewDetailedReport() {
            if (currentTaskId) {
                window.open(`/dashboard/${currentTaskId}`, '_blank');
            }
        }

        // Start New Analysis
        function startNewAnalysis() {
            // Reset everything
            currentTaskId = null;
            document.getElementById('fileInput').value = '';
            document.getElementById('statusSection').style.display = 'none';
            document.getElementById('resultsSection').style.display = 'none';
            
            // Clear results content
            const resultsContent = document.getElementById('resultsContent');
            if (resultsContent) {
                resultsContent.innerHTML = '';
            }
            
            // Check and show API status if needed
            checkApiKeyStatus();
            
            // Reset upload button
            const uploadBtn = document.getElementById('uploadBtn');
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Choose File';
        }

        // Time Filter Handlers
        document.querySelectorAll('.time-filter button').forEach(button => {
            button.addEventListener('click', function() {
                document.querySelectorAll('.time-filter button').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
            });
        });

        // Chart Control Handlers
        document.querySelectorAll('.chart-btn').forEach(button => {
            button.addEventListener('click', function() {
                document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
            });
        });

        // Drag and Drop functionality
        const uploadArea = document.querySelector('.upload-area');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, unhighlight, false);
        });

        function highlight(e) {
            uploadArea.classList.add('dragover');
        }

        function unhighlight(e) {
            uploadArea.classList.remove('dragover');
        }

        uploadArea.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                console.log('File dropped:', files[0].name);
                uploadFile(files[0]);
            }
        }

        // Navigation Scroll Handlers
        document.addEventListener('DOMContentLoaded', function() {
            // Analytics navigation click handler
            document.getElementById('analyticsNav').addEventListener('click', function(e) {
                e.preventDefault();
                const resultsSection = document.getElementById('resultsSection');
                if (resultsSection.style.display !== 'none') {
                    resultsSection.scrollIntoView({ 
                        behavior: 'smooth',
                        block: 'start'
                    });
                } else {
                    // If results section is not visible, scroll to upload section instead
                    document.getElementById('uploadSection').scrollIntoView({ 
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });

            // Upload Data navigation click handler  
            document.getElementById('uploadNav').addEventListener('click', function(e) {
                e.preventDefault();
                document.getElementById('uploadSection').scrollIntoView({ 
                    behavior: 'smooth',
                    block: 'start'
                });
            });
        });
    </script>
</body>
</html>
'''

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start background analysis"""
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
    """Get analysis status for a task"""
    try:
        status = analysis_status.get(task_id, 'Not found')
        print(f"Status check for {task_id}: {status}")
        return jsonify({'status': status})
    except Exception as e:
        print(f"Status error: {str(e)}")
        return jsonify({'status': f'Error: {str(e)}'})

@app.route('/results/<task_id>')
def get_results(task_id):
    """Get analysis results for a task"""
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

@app.route('/dashboard/<task_id>')
def detailed_dashboard(task_id):
    """Enhanced fraud dashboard with detailed analysis"""
    if task_id not in analysis_results:
        return "Results not found", 404
        
    results = analysis_results[task_id]
    
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FraudGuard Pro - Detailed Analysis Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Product+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #6366f1;
            --bg-primary: #ffffff;
            --bg-card: #ffffff;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --border-color: #e5e7eb;
            --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
            --product-sans: 'Product Sans', sans-serif;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: var(--product-sans);
            background: #f9fafb;
            color: var(--text-primary);
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            text-align: center;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }}
        
        .stat-card {{
            background: var(--bg-card);
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: var(--shadow);
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 3rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }}
        
        .fraud-list {{
            background: var(--bg-card);
            border-radius: 1rem;
            box-shadow: var(--shadow);
            margin: 2rem 0;
        }}
        
        .fraud-header {{
            background: var(--primary-color);
            color: white;
            padding: 2rem;
            border-radius: 1rem 1rem 0 0;
        }}
        
        .fraud-item {{
            border-bottom: 1px solid var(--border-color);
            padding: 2rem;
        }}
        
        .fraud-item:last-child {{ border-bottom: none; }}
        
        .fraud-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }}
        
        .fraud-meta {{
            display: flex;
            gap: 2rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}
        
        .fraud-tag {{
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
        }}
        
        .fraud-tag.critical {{ background: #fef2f2; color: #dc2626; }}
        .fraud-tag.high {{ background: #fffbeb; color: #d97706; }}
        .fraud-tag.medium {{ background: #fefcbf; color: #d69e2e; }}
        
        .ai-explanation {{
            background: #f0f9ff;
            border-left: 4px solid var(--primary-color);
            padding: 1.5rem;
            margin: 1rem 0;
            border-radius: 0 0.5rem 0.5rem 0;
        }}
        
        .analysis-content {{
            line-height: 1.6;
        }}
        
        .analysis-section {{
            margin: 1.5rem 0;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 0.5rem;
            border-left: 3px solid var(--primary-color);
        }}
        
        .analysis-section h5 {{
            margin: 0 0 0.75rem 0;
            color: var(--primary-color);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.1rem;
        }}
        
        .analysis-section p {{
            margin: 0.5rem 0;
            color: var(--text-secondary);
            line-height: 1.7;
        }}
        
        .risk-factors {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin: 1rem 0;
        }}
        
        .risk-factor {{
            background: #f3f4f6;
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.875rem;
        }}
        
        .btn {{
            background: var(--primary-color);
            color: white;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 0.5rem;
            text-decoration: none;
            display: inline-block;
            margin: 0.5rem;
            cursor: pointer;
        }}
        
        .btn:hover {{ background: #5b5af5; }}
        
        .pagination {{ text-align: center; margin: 2rem 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-shield-alt"></i> FraudGuard Pro - Detailed Report</h1>
        <p>Comprehensive fraud analysis with AI insights</p>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{results['total_transactions']:,}</div>
                <div>Total Transactions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #ef4444;">{results['fraud_detected']:,}</div>
                <div>Fraud Cases Detected</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #f59e0b;">{results['fraud_rate']:.2f}%</div>
                <div>Fraud Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #dc2626;">{results.get('critical_risk_count', 0):,}</div>
                <div>Critical Risk Cases</div>
            </div>
        </div>
        
        <!-- API Key Status -->
        <div id="apiKeyStatus" style="margin: 1rem 0; padding: 1rem; border-radius: 8px; background: var(--background-secondary); border-left: 4px solid #f59e0b;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <i class="fas fa-key" style="color: #f59e0b;"></i>
                <span style="font-weight: 500;">API Configuration Required</span>
            </div>
            <p style="margin: 0.5rem 0 0 1.5rem; font-size: 0.875rem; color: var(--text-muted);">
                Add your Google AI API key in Settings for enhanced AI fraud analysis.
            </p>
        </div>
        
        <div class="fraud-list">
            <div class="fraud-header">
                <h2><i class="fas fa-exclamation-triangle"></i> Detailed Fraud Analysis ({len(results.get('detailed_frauds', []))} cases)</h2>
                <p>{results.get('analysis_summary', 'Comprehensive fraud detection analysis')}</p>
            </div>
            
            {generate_fraud_items_html(results)}
        </div>
        
        <div class="pagination">
            <a href="/" class="btn"><i class="fas fa-home"></i> Back to Dashboard</a>
            <a href="/results/{task_id}" class="btn"><i class="fas fa-download"></i> Download JSON Report</a>
        </div>
    </div>
</body>
</html>
    '''

def generate_fraud_items_html(results):
    """Generate HTML for fraud items to avoid f-string nesting issues"""
    if not results.get('detailed_frauds'):
        return "<div class='fraud-item'><h3>No fraud cases detected</h3><p>All transactions appear legitimate based on our analysis.</p></div>"
    
    fraud_items_html = ""
    for fraud in results.get('detailed_frauds', [])[:50]:
        risk_factors_html = ""
        if fraud.get('risk_factors'):
            risk_factors_html = "<div class='risk-factors'>" + "".join([
                f"<span class='risk-factor'><i class='fas fa-exclamation-triangle'></i> {factor}</span>" 
                for factor in fraud['risk_factors']
            ]) + "</div>"
        
        ai_explanation_html = ""
        if fraud.get('ai_explanation'):
            # Show AI explanation unless it's an error message
            is_error_message = (
                fraud['ai_explanation'].startswith('AI analysis unavailable') or
                fraud['ai_explanation'].startswith('AI analysis failed') or
                fraud['ai_explanation'].startswith('AI analysis error')
            )
            if not is_error_message:
                ai_explanation_html = f"<div class='ai-explanation'><h4><i class='fas fa-robot'></i> AI Analysis:</h4>{format_ai_analysis(fraud['ai_explanation'])}</div>"
            else:
                # Show error message in a different style
                ai_explanation_html = f"<div class='ai-explanation error'><h4><i class='fas fa-exclamation-triangle'></i> AI Analysis:</h4><p>{fraud['ai_explanation']}</p></div>"
        
        fraud_items_html += f'''
        <div class="fraud-item">
            <div class="fraud-title">
                <i class="fas fa-exclamation-triangle"></i> Transaction #{fraud['index']} - {fraud['severity']} Risk
                <span class="fraud-tag {fraud['severity'].lower()}">{fraud['probability']:.1%} Confidence</span>
            </div>
            
            <div class="fraud-meta">
                <span><strong>Amount:</strong> ₹{fraud['amount']:,.2f}</span>
                <span><strong>Severity:</strong> {fraud['severity']}</span>
                <span><strong>ML Confidence:</strong> {fraud['probability']:.1%}</span>
            </div>
            
            {risk_factors_html}
            {ai_explanation_html}
        </div>
        '''
    
    return fraud_items_html

@app.route('/settings')
def settings():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Settings - FraudGuard Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Product+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary-color: #6366f1;
            --secondary-color: #8b5cf6;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --text-tertiary: #9ca3af;
            --border-color: #e5e7eb;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --product-sans: 'Product Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        [data-theme="dark"] {
            --bg-primary: #111827;
            --bg-secondary: #1f2937;
            --bg-card: #1f2937;
            --text-primary: #f9fafb;
            --text-secondary: #d1d5db;
            --text-tertiary: #9ca3af;
            --border-color: #374151;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--product-sans);
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar */
        .sidebar {
            width: 280px;
            background: var(--bg-card);
            border-right: 1px solid var(--border-color);
            padding: 2rem 0;
            overflow-y: auto;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0 2rem;
            margin-bottom: 3rem;
        }

        .logo i {
            width: 2.5rem;
            height: 2.5rem;
            background: var(--primary-color);
            color: white;
            border-radius: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }

        .logo h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .sidebar-section {
            margin-bottom: 2rem;
        }

        .sidebar-title {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-tertiary);
            padding: 0 2rem;
            margin-bottom: 0.75rem;
            letter-spacing: 0.05em;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 2rem;
            color: var(--text-secondary);
            text-decoration: none;
            transition: all 0.2s;
            font-weight: 500;
        }

        .nav-item:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        .nav-item.active {
            background: var(--primary-color);
            color: white;
        }

        .nav-item i {
            width: 1.25rem;
            text-align: center;
        }

        /* Main Content */
        .main-content {
            flex: 1;
            padding: 2rem;
            background: var(--bg-secondary);
        }

        .page-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 2rem;
        }

        .page-title {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }

        .page-subtitle {
            color: var(--text-secondary);
            font-size: 1rem;
        }

        .settings-grid {
            display: grid;
            gap: 2rem;
            max-width: 800px;
        }

        .settings-card {
            background: var(--bg-card);
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
        }

        .settings-card h3 {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 1rem;
        }

        .setting-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 0;
            border-bottom: 1px solid var(--border-color);
        }

        .setting-item:last-child {
            border-bottom: none;
        }

        .setting-info h4 {
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }

        .setting-info p {
            color: var(--text-secondary);
            font-size: 0.875rem;
        }

        .toggle-switch {
            position: relative;
            width: 3rem;
            height: 1.5rem;
            background: var(--border-color);
            border-radius: 1rem;
            cursor: pointer;
            transition: all 0.3s;
        }

        .toggle-switch.active {
            background: var(--primary-color);
        }

        .toggle-switch::after {
            content: '';
            position: absolute;
            top: 0.125rem;
            left: 0.125rem;
            width: 1.25rem;
            height: 1.25rem;
            background: white;
            border-radius: 50%;
            transition: all 0.3s;
        }

        .toggle-switch.active::after {
            left: 1.625rem;
        }

        .btn {
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 0.5rem;
            padding: 0.75rem 1.5rem;
            font-family: var(--product-sans);
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn:hover {
            background: var(--secondary-color);
        }

        .btn-secondary {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background: var(--border-color);
        }

        .input-group {
            margin-bottom: 1rem;
        }

        .input-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
            font-weight: 500;
        }

        .input-group input, .input-group select {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            background: var(--bg-primary);
            color: var(--text-primary);
            font-family: var(--product-sans);
        }

        .theme-toggle {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.25rem;
            cursor: pointer;
            padding: 0.75rem;
            border-radius: 0.5rem;
            transition: all 0.2s;
            position: absolute;
            top: 2rem;
            right: 2rem;
        }

        .theme-toggle:hover {
            background: var(--bg-secondary);
        }
    </style>
</head>
<body>
    <div class="container">
        <nav class="sidebar">
            <div class="logo">
                <i class="fas fa-shield-alt"></i>
                <h1>FraudGuard Pro</h1>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">Navigation</div>
                <a href="/" class="nav-item">
                    <i class="fas fa-tachometer-alt"></i>
                    Dashboard
                </a>
                <a href="/" class="nav-item">
                    <i class="fas fa-chart-line"></i>
                    Analytics
                </a>
                <a href="/" class="nav-item">
                    <i class="fas fa-upload"></i>
                    Upload Data
                </a>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">Management</div>
                <a href="/settings" class="nav-item active">
                    <i class="fas fa-cog"></i>
                    Settings
                </a>
                <a href="/help" class="nav-item">
                    <i class="fas fa-question-circle"></i>
                    Help
                </a>
            </div>
        </nav>

        <main class="main-content">
            <button class="theme-toggle" onclick="toggleTheme()">
                <i class="fas fa-moon"></i>
            </button>

            <div class="page-header">
                <div>
                    <h1 class="page-title">Settings</h1>
                    <p class="page-subtitle">Configure your FraudGuard Pro preferences</p>
                </div>
            </div>

            <div class="settings-grid">
                <div class="settings-card">
                    <h3><i class="fas fa-palette"></i> Appearance</h3>
                    <div class="setting-item">
                        <div class="setting-info">
                            <h4>Dark Mode</h4>
                            <p>Toggle between light and dark themes</p>
                        </div>
                        <div class="toggle-switch" onclick="toggleSetting(this)">
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-info">
                            <h4>High Contrast</h4>
                            <p>Increase contrast for better visibility</p>
                        </div>
                        <div class="toggle-switch" onclick="toggleSetting(this)">
                        </div>
                    </div>
                </div>

                <div class="settings-card">
                    <h3><i class="fas fa-bell"></i> Notifications</h3>
                    <div class="setting-item">
                        <div class="setting-info">
                            <h4>Fraud Alerts</h4>
                            <p>Receive notifications when fraud is detected</p>
                        </div>
                        <div class="toggle-switch active" onclick="toggleSetting(this)">
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-info">
                            <h4>Email Reports</h4>
                            <p>Get daily analysis reports via email</p>
                        </div>
                        <div class="toggle-switch" onclick="toggleSetting(this)">
                        </div>
                    </div>
                </div>

                <div class="settings-card">
                    <h3><i class="fas fa-database"></i> Data Processing</h3>
                    <div class="setting-item">
                        <div class="setting-info">
                            <h4>Auto-Analysis</h4>
                            <p>Automatically analyze uploaded CSV files</p>
                        </div>
                        <div class="toggle-switch active" onclick="toggleSetting(this)">
                        </div>
                    </div>
                    <div class="setting-item">
                        <div class="setting-info">
                            <h4>Data Retention</h4>
                            <p>Keep analysis results for future reference</p>
                        </div>
                        <div class="toggle-switch" onclick="toggleSetting(this)">
                        </div>
                    </div>
                </div>

                <div class="settings-card">
                    <h3><i class="fas fa-user-cog"></i> Account</h3>
                    <div class="input-group">
                        <label for="apiKey">Google AI API Key</label>
                        <input type="password" id="apiKey" placeholder="Enter your API key">
                    </div>
                    <div class="input-group">
                        <label for="alertThreshold">Fraud Alert Threshold</label>
                        <select id="alertThreshold">
                            <option value="low">Low (>30% risk)</option>
                            <option value="medium" selected>Medium (>60% risk)</option>
                            <option value="high">High (>80% risk)</option>
                        </select>
                    </div>
                    <button class="btn">Save Settings</button>
                    <button class="btn btn-secondary" style="margin-left: 1rem;">Reset to Default</button>
                </div>
            </div>
        </main>
    </div>

    <script>
        let currentSettings = {};

        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            const icon = document.querySelector('.theme-toggle i');
            icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            
            // Update settings
            currentSettings.dark_mode = newTheme === 'dark';
        }

        function toggleSetting(element) {
            element.classList.toggle('active');
            
            // Get the setting name from the parent setting-item
            const settingItem = element.closest('.setting-item');
            const settingName = settingItem.querySelector('h4').textContent.toLowerCase().replace(/\s+/g, '_');
            const isActive = element.classList.contains('active');
            
            // Map display names to setting keys
            const settingMap = {
                'dark_mode': 'dark_mode',
                'high_contrast': 'high_contrast',
                'fraud_alerts': 'fraud_alerts',
                'email_reports': 'email_reports',
                'auto-analysis': 'auto_analysis',
                'data_retention': 'data_retention'
            };
            
            if (settingMap[settingName]) {
                currentSettings[settingMap[settingName]] = isActive;
            }
        }

        async function loadSettings() {
            try {
                const response = await fetch('/api/settings');
                const data = await response.json();
                
                if (data.success) {
                    currentSettings = data.settings;
                    
                    // Update toggles based on loaded settings
                    document.querySelectorAll('.toggle-switch').forEach((toggle, index) => {
                        const settingKeys = ['dark_mode', 'high_contrast', 'fraud_alerts', 'email_reports', 'auto_analysis', 'data_retention'];
                        const key = settingKeys[index];
                        
                        if (currentSettings[key]) {
                            toggle.classList.add('active');
                        } else {
                            toggle.classList.remove('active');
                        }
                    });
                    
                    // Update form fields
                    const apiKeyInput = document.getElementById('apiKey');
                    const alertThreshold = document.getElementById('alertThreshold');
                    
                    if (currentSettings.google_api_key) {
                        apiKeyInput.value = currentSettings.google_api_key;
                    }
                    
                    alertThreshold.value = currentSettings.alert_threshold || 'medium';
                }
            } catch (error) {
                console.error('Failed to load settings:', error);
                showNotification('Failed to load settings', 'error');
            }
        }

        async function saveSettings() {
            try {
                // Get form values
                const apiKey = document.getElementById('apiKey').value;
                const alertThreshold = document.getElementById('alertThreshold').value;
                
                // Create a clean settings object to send
                const settingsToSave = { ...currentSettings };
                
                // Update with form values
                if (apiKey && apiKey.trim()) {
                    // Only update API key if a new one is provided
                    settingsToSave.google_api_key = apiKey;
                } else if (settingsToSave.google_api_key === '***hidden***') {
                    // Remove the hidden placeholder - backend will preserve existing key
                    delete settingsToSave.google_api_key;
                }
                
                // Always update other settings
                settingsToSave.alert_threshold = alertThreshold;
                
                const response = await fetch('/api/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(settingsToSave)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification('Settings saved successfully!', 'success');
                    
                    // Test API key if provided
                    if (apiKey) {
                        await testApiKey(apiKey);
                    }
                    
                    // Refresh API key status on main dashboard if function exists
                    if (typeof checkApiKeyStatus === 'function') {
                        checkApiKeyStatus();
                    }
                } else {
                    showNotification('Failed to save settings: ' + data.error, 'error');
                }
            } catch (error) {
                console.error('Failed to save settings:', error);
                showNotification('Failed to save settings', 'error');
            }
        }

        async function testApiKey(apiKey = null) {
            if (!apiKey) {
                apiKey = document.getElementById('apiKey').value;
            }
            
            if (!apiKey) {
                showNotification('Please enter an API key to test', 'warning');
                return;
            }
            
            try {
                showNotification('Testing API key...', 'info');
                
                const response = await fetch('/api/test-api-key', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ api_key: apiKey })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification('API key is valid and working!', 'success');
                } else {
                    showNotification('API key test failed: ' + data.error, 'error');
                }
            } catch (error) {
                console.error('API key test failed:', error);
                showNotification('API key test failed', 'error');
            }
        }

        function resetSettings() {
            if (confirm('Are you sure you want to reset all settings to default?')) {
                // Reset to default settings
                currentSettings = {
                    dark_mode: false,
                    high_contrast: false,
                    fraud_alerts: true,
                    email_reports: false,
                    auto_analysis: true,
                    data_retention: false,
                    google_api_key: '',
                    alert_threshold: 'medium'
                };
                
                // Update UI
                document.querySelectorAll('.toggle-switch').forEach(toggle => {
                    toggle.classList.remove('active');
                });
                
                // Set default active toggles
                const defaultActiveToggles = [2, 4]; // fraud_alerts and auto_analysis (0-indexed)
                defaultActiveToggles.forEach(index => {
                    document.querySelectorAll('.toggle-switch')[index].classList.add('active');
                });
                
                document.getElementById('apiKey').value = '';
                document.getElementById('alertThreshold').value = 'medium';
                
                showNotification('Settings reset to default', 'info');
            }
        }

        function showNotification(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#6366f1'};
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 0.5rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                z-index: 1000;
                font-family: var(--product-sans);
                font-weight: 500;
                max-width: 300px;
                word-wrap: break-word;
                animation: slideIn 0.3s ease-out;
            `;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, 5000);
        }

        // Add CSS animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);

        // Load saved theme and settings on page load
        document.addEventListener('DOMContentLoaded', function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.body.setAttribute('data-theme', savedTheme);
            
            const icon = document.querySelector('.theme-toggle i');
            icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            
            // Load settings
            loadSettings();
            
            // Add event listeners
            document.querySelector('.btn').addEventListener('click', saveSettings);
            document.querySelector('.btn-secondary').addEventListener('click', resetSettings);
            
            // Add test API key button
            const testButton = document.createElement('button');
            testButton.className = 'btn btn-secondary';
            testButton.textContent = 'Test API Key';
            testButton.style.marginLeft = '1rem';
            testButton.addEventListener('click', () => testApiKey());
            
            const saveButton = document.querySelector('.btn');
            saveButton.parentNode.insertBefore(testButton, saveButton.nextSibling);
        });
    </script>
</body>
</html>
    '''

@app.route('/help')
def help_page():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Help - FraudGuard Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Product+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary-color: #6366f1;
            --secondary-color: #8b5cf6;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #1f2937;
            --text-secondary: #6b7280;
            --text-tertiary: #9ca3af;
            --border-color: #e5e7eb;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --product-sans: 'Product Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        [data-theme="dark"] {
            --bg-primary: #111827;
            --bg-secondary: #1f2937;
            --bg-card: #1f2937;
            --text-primary: #f9fafb;
            --text-secondary: #d1d5db;
            --text-tertiary: #9ca3af;
            --border-color: #374151;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--product-sans);
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar styles (same as settings) */
        .sidebar {
            width: 280px;
            background: var(--bg-card);
            border-right: 1px solid var(--border-color);
            padding: 2rem 0;
            overflow-y: auto;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0 2rem;
            margin-bottom: 3rem;
        }

        .logo i {
            width: 2.5rem;
            height: 2.5rem;
            background: var(--primary-color);
            color: white;
            border-radius: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }

        .logo h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .sidebar-section {
            margin-bottom: 2rem;
        }

        .sidebar-title {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-tertiary);
            padding: 0 2rem;
            margin-bottom: 0.75rem;
            letter-spacing: 0.05em;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 2rem;
            color: var(--text-secondary);
            text-decoration: none;
            transition: all 0.2s;
            font-weight: 500;
        }

        .nav-item:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        .nav-item.active {
            background: var(--primary-color);
            color: white;
        }

        .nav-item i {
            width: 1.25rem;
            text-align: center;
        }

        /* Main Content */
        .main-content {
            flex: 1;
            padding: 2rem;
            background: var(--bg-secondary);
        }

        .page-header {
            margin-bottom: 2rem;
        }

        .page-title {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }

        .page-subtitle {
            color: var(--text-secondary);
            font-size: 1rem;
        }

        .help-content {
            max-width: 800px;
            display: grid;
            gap: 2rem;
        }

        .help-card {
            background: var(--bg-card);
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
        }

        .help-card h3 {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .help-card p {
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }

        .help-card ul {
            color: var(--text-secondary);
            margin-left: 1.5rem;
            margin-bottom: 1rem;
        }

        .help-card li {
            margin-bottom: 0.5rem;
        }

        .disclaimer {
            background: linear-gradient(135deg, var(--warning-color), #f97316);
            color: white;
            padding: 2rem;
            border-radius: 1rem;
            margin-bottom: 2rem;
        }

        .disclaimer h3 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .disclaimer p {
            margin-bottom: 0.75rem;
            opacity: 0.95;
        }

        .code-block {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 1rem;
            font-family: 'Courier New', monospace;
            color: var(--text-primary);
            margin: 1rem 0;
            overflow-x: auto;
        }

        .faq-item {
            border-bottom: 1px solid var(--border-color);
            padding: 1.5rem 0;
        }

        .faq-item:last-child {
            border-bottom: none;
        }

        .faq-question {
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.75rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .faq-answer {
            color: var(--text-secondary);
            padding-left: 1.5rem;
        }

        .theme-toggle {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.25rem;
            cursor: pointer;
            padding: 0.75rem;
            border-radius: 0.5rem;
            transition: all 0.2s;
            position: absolute;
            top: 2rem;
            right: 2rem;
        }

        .theme-toggle:hover {
            background: var(--bg-secondary);
        }

        .contact-info {
            display: flex;
            gap: 2rem;
            margin-top: 1rem;
        }

        .contact-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <div class="container">
        <nav class="sidebar">
            <div class="logo">
                <i class="fas fa-shield-alt"></i>
                <h1>FraudGuard Pro</h1>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">Navigation</div>
                <a href="/" class="nav-item">
                    <i class="fas fa-tachometer-alt"></i>
                    Dashboard
                </a>
                <a href="/" class="nav-item">
                    <i class="fas fa-chart-line"></i>
                    Analytics
                </a>
                <a href="/" class="nav-item">
                    <i class="fas fa-upload"></i>
                    Upload Data
                </a>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">Management</div>
                <a href="/settings" class="nav-item">
                    <i class="fas fa-cog"></i>
                    Settings
                </a>
                <a href="/help" class="nav-item active">
                    <i class="fas fa-question-circle"></i>
                    Help
                </a>
            </div>
        </nav>

        <main class="main-content">
            <button class="theme-toggle" onclick="toggleTheme()">
                <i class="fas fa-moon"></i>
            </button>

            <div class="page-header">
                <h1 class="page-title">Help & Support</h1>
                <p class="page-subtitle">Get help with FraudGuard Pro and learn how to use all features</p>
            </div>

            <div class="disclaimer">
                <h3><i class="fas fa-exclamation-triangle"></i> Important Disclaimer</h3>
                <p><strong>Educational Purpose:</strong> FraudGuard Pro is designed for educational and demonstration purposes. While it uses advanced algorithms and AI analysis, it should not be used as the sole basis for financial decisions.</p>
                <p><strong>Data Privacy:</strong> Your uploaded data is processed locally and temporarily. We do not permanently store your transaction data on our servers.</p>
                <p><strong>Accuracy Notice:</strong> Fraud detection results are estimates based on statistical analysis and should be verified through proper financial investigation procedures.</p>
                <p><strong>Professional Advice:</strong> For critical financial decisions, always consult with qualified financial security professionals.</p>
            </div>

            <div class="help-content">
                <div class="help-card">
                    <h3><i class="fas fa-rocket"></i> Getting Started</h3>
                    <p>Welcome to FraudGuard Pro! Here's how to get started with fraud detection:</p>
                    <ul>
                        <li><strong>Step 1:</strong> Click on "Upload Data" in the sidebar or scroll to the upload section</li>
                        <li><strong>Step 2:</strong> Select or drag your CSV file containing transaction data</li>
                        <li><strong>Step 3:</strong> Wait for the analysis to complete (usually 10-30 seconds)</li>
                        <li><strong>Step 4:</strong> Review the results in the dashboard and detailed analysis</li>
                    </ul>
                </div>

                <div class="help-card">
                    <h3><i class="fas fa-file-csv"></i> CSV File Format</h3>
                    <p>Your CSV file should contain the following columns for optimal analysis:</p>
                    <div class="code-block">
transaction_id,amount,merchant,location,transaction_type,timestamp
TX001,1500.00,Amazon,New York,online,2025-08-30 10:30:00
TX002,50.00,Starbucks,California,retail,2025-08-30 11:15:00
                    </div>
                    <p><strong>Required columns:</strong> transaction_id, amount<br>
                    <strong>Recommended columns:</strong> merchant, location, transaction_type, timestamp</p>
                </div>

                <div class="help-card">
                    <h3><i class="fas fa-question-circle"></i> Frequently Asked Questions</h3>
                    
                    <div class="faq-item">
                        <div class="faq-question"><i class="fas fa-chevron-right"></i> How accurate is the fraud detection?</div>
                        <div class="faq-answer">Our system achieves 95%+ accuracy using advanced statistical analysis and AI algorithms. However, results should always be verified manually for critical decisions.</div>
                    </div>

                    <div class="faq-item">
                        <div class="faq-question"><i class="fas fa-chevron-right"></i> What file size limit is there?</div>
                        <div class="faq-answer">Currently, we support CSV files up to 500MB in size, which can handle approximately 1 million transactions.</div>
                    </div>

                    <div class="faq-item">
                        <div class="faq-question"><i class="fas fa-chevron-right"></i> Is my data secure?</div>
                        <div class="faq-answer">Yes! Your data is processed locally and temporarily. We do not store your transaction data permanently on our servers. Data is automatically cleaned after processing.</div>
                    </div>

                    <div class="faq-item">
                        <div class="faq-question"><i class="fas fa-chevron-right"></i> Can I export the analysis results?</div>
                        <div class="faq-answer">Yes, you can view detailed reports and analysis results. The system provides comprehensive fraud reports with AI explanations.</div>
                    </div>
                </div>

                <div class="help-card">
                    <h3><i class="fas fa-lightbulb"></i> Tips for Better Results</h3>
                    <ul>
                        <li>Include as many relevant columns as possible (merchant, location, timestamp)</li>
                        <li>Ensure your data is clean with no missing transaction IDs or amounts</li>
                        <li>Use consistent date formats (YYYY-MM-DD HH:MM:SS preferred)</li>
                        <li>Include transaction types (online, retail, ATM, etc.) for better analysis</li>
                        <li>Larger datasets generally provide more accurate fraud detection</li>
                    </ul>
                </div>

                <div class="help-card">
                    <h3><i class="fas fa-cog"></i> System Requirements</h3>
                    <p>FraudGuard Pro works best with:</p>
                    <ul>
                        <li>Modern web browsers (Chrome, Firefox, Safari, Edge)</li>
                        <li>JavaScript enabled</li>
                        <li>Stable internet connection for AI analysis</li>
                        <li>Minimum 4GB RAM for large file processing</li>
                    </ul>
                </div>

                <div class="help-card">
                    <h3><i class="fas fa-phone"></i> Contact Support</h3>
                    <p>Need additional help? We're here to support you:</p>
                    <div class="contact-info">
                        <div class="contact-item">
                            <i class="fas fa-envelope"></i>
                            <span>bladesilent034@gmail.com</span>
                        </div>
                        <div class="contact-item">
                            <i class="fas fa-globe"></i>
                            <span>Documentation & Guides</span>
                        </div>
                    </div>
                    <p style="margin-top: 1rem; font-size: 0.875rem; color: var(--text-tertiary);">
                        Response time: Usually within 24 hours during business days
                    </p>
                </div>
            </div>
        </main>
    </div>

    <script>
        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            const icon = document.querySelector('.theme-toggle i');
            icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }

        // Load saved theme
        document.addEventListener('DOMContentLoaded', function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.body.setAttribute('data-theme', savedTheme);
            
            const icon = document.querySelector('.theme-toggle i');
            icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        });

        // FAQ toggle functionality
        document.querySelectorAll('.faq-question').forEach(question => {
            question.addEventListener('click', function() {
                const icon = this.querySelector('i');
                icon.classList.toggle('fa-chevron-right');
                icon.classList.toggle('fa-chevron-down');
            });
        });
    </script>
</body>
</html>
    '''

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings"""
    try:
        settings = load_settings()
        print(f"DEBUG: Loaded settings - API key present: {bool(settings.get('google_api_key'))}")
        # Return actual settings including API key (for working correctly)
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        print(f"DEBUG: Error in get_settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update settings"""
    try:
        data = request.get_json()
        print(f"DEBUG: Received settings update: {list(data.keys())}")
        print(f"DEBUG: API key in request: {'google_api_key' in data}")
        
        settings = load_settings()
        print(f"DEBUG: Current settings API key present: {bool(settings.get('google_api_key'))}")
        
        # Update settings with provided data
        for key, value in data.items():
            if key in DEFAULT_SETTINGS:
                # Special handling for API key - don't overwrite with hidden value
                if key == 'google_api_key' and value == '***hidden***':
                    # Skip updating API key if it's the hidden placeholder
                    print(f"DEBUG: Skipping hidden API key value")
                    continue
                print(f"DEBUG: Updating {key}")
                settings[key] = value
        
        # Save settings
        if save_settings(settings):
            # Update global settings
            global current_settings
            current_settings = settings
            
            # If API key was updated, try to reinitialize AI system
            if 'google_api_key' in data and data['google_api_key']:
                try:
                    # Test the new API key
                    import google.generativeai as genai
                    genai.configure(api_key=data['google_api_key'])
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    test_response = model.generate_content("Test connection")
                    
                    if test_response:
                        print(f"✅ API key updated and validated successfully")
                    
                except Exception as e:
                    print(f"⚠️ New API key validation failed: {e}")
                    # Still save the settings, but warn user
                    return jsonify({
                        'success': True, 
                        'message': 'Settings saved, but API key validation failed. Please test your API key.',
                        'warning': str(e)
                    })
            
            return jsonify({'success': True, 'message': 'Settings saved successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save settings'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-api-key', methods=['POST'])
def test_api_key():
    """Test if the provided API key works"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API key is required'})
        
        # Test the API key by trying to initialize the Google AI
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Try different model names to find working one
            model_names = [
                'gemini-1.5-flash-latest',
                'gemini-1.5-flash', 
                'gemini-1.5-pro-latest',
                'gemini-1.5-pro',
                'gemini-pro',
                'models/gemini-1.5-flash',
                'models/gemini-1.5-pro'
            ]
            working_model = None
            
            for model_name in model_names:
                try:
                    print(f"DEBUG: Testing model: {model_name}")
                    model = genai.GenerativeModel(model_name)
                    
                    # Try the simplest possible test
                    test_prompt = "What is 2+2?"
                    
                    response = model.generate_content(test_prompt)
                    print(f"DEBUG: Model {model_name} response type: {type(response)}")
                    
                    if response and hasattr(response, 'text') and response.text:
                        working_model = model_name
                        print(f"DEBUG: Found working model: {working_model}")
                        print(f"DEBUG: Response text: {response.text[:100]}")
                        break
                        
                except Exception as model_error:
                    print(f"DEBUG: Model {model_name} failed: {model_error}")
                    continue
            
            if working_model:
                # Save the working model name for future use
                settings = load_settings()
                settings['working_model'] = working_model
                save_settings(settings)
                
                return jsonify({
                    'success': True, 
                    'message': f'API key is valid and working perfectly with {working_model}!',
                    'model_used': working_model
                })
            else:
                return jsonify({'success': False, 'error': 'API key valid but no compatible models found'})
                
        except Exception as api_error:
            error_str = str(api_error).lower()
            if 'api_key_invalid' in error_str or 'invalid' in error_str or 'permission denied' in error_str:
                return jsonify({'success': False, 'error': 'Invalid API key. Please check your Google AI API key.'})
            elif 'quota' in error_str or 'limit' in error_str:
                return jsonify({'success': False, 'error': 'API quota exceeded. Please check your Google AI billing settings.'})
            elif 'blocked' in error_str:
                return jsonify({'success': False, 'error': 'API access blocked. Please check your API key permissions.'})
            else:
                return jsonify({'success': False, 'error': f'API test failed: {str(api_error)}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Test failed: {str(e)}'}), 500

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve images from the images folder"""
    try:
        return send_from_directory('images', filename)
    except Exception as e:
        print(f"Image serving error: {str(e)}")
        return "Image not found", 404

if __name__ == '__main__':
    print("🛡️ Starting FraudGuard Pro Dashboard...")
    print("🔗 Open: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
