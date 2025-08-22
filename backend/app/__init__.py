from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'hackathon-fraud-detection-2025'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fraud_detection.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    from routes.main_routes import main_bp
    from routes.ml_routes import ml_bp
    from routes.transaction_routes import transaction_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(ml_bp, url_prefix='/api/ml')
    app.register_blueprint(transaction_bp, url_prefix='/api/transactions')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
