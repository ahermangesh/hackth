from flask import Flask, jsonify
import traceback

print("Starting Flask app...")

try:
    app = Flask(__name__)
    print("Flask app created successfully")
    
    @app.route('/')
    def home():
        return jsonify({
            "message": "Fraud Detection API is running!",
            "status": "success"
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "message": "API is working"
        })
    
    print("Routes defined successfully")
    
    if __name__ == '__main__':
        print("Starting server on port 5000...")
        app.run(debug=True, host='127.0.0.1', port=5000)
        
except Exception as e:
    print(f"Error occurred: {e}")
    traceback.print_exc()
