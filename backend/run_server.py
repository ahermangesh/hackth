import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

if __name__ == '__main__':
    app = create_app()
    print("🚀 Fraud Detection API Server Starting...")
    print("📊 Dashboard: http://localhost:3000")
    print("🔌 API Endpoints: http://localhost:5000")
    print("📚 API Docs: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
