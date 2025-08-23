#!/usr/bin/env python3
"""
Simple Flask test to debug the universal fraud API
"""

from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Universal Fraud Detection - Test</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }
        .test-section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌟 Universal Fraud Detection System</h1>
        <p>System Status: ✅ Working</p>
    </div>
    
    <div class="test-section">
        <h2>🧪 System Test</h2>
        <p>If you can see this page, the Flask server is working correctly!</p>
        <p>Date: {{ current_time }}</p>
    </div>
    
    <div class="test-section">
        <h2>📁 File Upload Test</h2>
        <form action="/test-upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".csv" required>
            <br><br>
            <button type="submit" style="background-color: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px;">Test Upload</button>
        </form>
    </div>
</body>
</html>
    ''', current_time="August 22, 2025")

@app.route('/test-upload', methods=['POST'])
def test_upload():
    from flask import request
    try:
        if 'file' not in request.files:
            return "No file uploaded"
        
        file = request.files['file']
        if file.filename == '':
            return "No file selected"
        
        return f"✅ File upload test successful! Filename: {file.filename}"
        
    except Exception as e:
        return f"❌ Upload error: {str(e)}"

if __name__ == '__main__':
    print("🧪 Starting Flask Test Server...")
    print("🔗 Test at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
