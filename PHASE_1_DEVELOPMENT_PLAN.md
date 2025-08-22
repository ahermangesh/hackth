# PHASE 1: Project Foundation & Environment Setup
## **Duration: 2 Weeks | Priority: Critical Foundation**

---

## **FREE TECHNOLOGY STACK**

### **Frontend:**
- **React.js** (Create React App) - Free, open-source
- **Material-UI** or **Tailwind CSS** - Free UI frameworks
- **Chart.js** or **Recharts** - Free charting libraries
- **Axios** - HTTP client

### **Backend:**
- **Python Flask** - Lightweight, free framework
- **SQLite** (development) → **PostgreSQL** (production) - Free databases
- **Redis** - Free in-memory store (for caching)
- **Flask-SQLAlchemy** - ORM
- **Flask-JWT-Extended** - Authentication

### **Machine Learning:**
- **Scikit-learn** - Free ML library
- **Pandas** + **NumPy** - Data processing
- **Matplotlib** + **Seaborn** - Visualization
- **SHAP** - Model explainability
- **Jupyter Notebooks** - Development environment

### **DevOps & Deployment:**
- **Docker** + **Docker Compose** - Containerization
- **GitHub Actions** - Free CI/CD
- **Railway** or **Render** - Free hosting (with limitations)
- **Vercel** - Free frontend hosting

### **Data Processing:**
- **Apache Kafka** (local) or **Redis Streams** - Message queuing
- **Celery** - Background tasks
- **Pandas** - Data processing

---

## **WEEK 1: ENVIRONMENT & PROJECT SETUP**

### **Day 1-2: Development Environment**

#### **Tasks:**
1. **Install Required Software**
   ```bash
   # Python environment
   python -m venv fraud_detection_env
   source fraud_detection_env/bin/activate  # Windows: fraud_detection_env\Scripts\activate
   
   # Node.js for frontend
   # Download from nodejs.org (LTS version)
   
   # Docker Desktop
   # Download from docker.com
   
   # Git setup
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

2. **Project Structure Setup**
   ```
   fraud-detection-system/
   ├── backend/
   │   ├── app/
   │   │   ├── __init__.py
   │   │   ├── models/
   │   │   ├── routes/
   │   │   ├── ml/
   │   │   └── utils/
   │   ├── requirements.txt
   │   ├── Dockerfile
   │   └── config.py
   ├── frontend/
   │   ├── public/
   │   ├── src/
   │   │   ├── components/
   │   │   ├── pages/
   │   │   ├── services/
   │   │   └── utils/
   │   ├── package.json
   │   └── Dockerfile
   ├── ml_notebooks/
   │   ├── data_exploration.ipynb
   │   ├── feature_engineering.ipynb
   │   └── model_training.ipynb
   ├── data/
   │   ├── raw/
   │   ├── processed/
   │   └── models/
   ├── docker-compose.yml
   ├── .github/
   │   └── workflows/
   └── README.md
   ```

3. **Git Repository Initialization**
   ```bash
   git init
   git add .
   git commit -m "Initial project structure"
   git branch -M main
   git remote add origin https://github.com/yourusername/fraud-detection-system.git
   git push -u origin main
   ```

#### **Deliverables:**
- [ ] Complete development environment
- [ ] Project repository structure
- [ ] Initial Git setup with remote repository

### **Day 3-4: Backend Foundation**

#### **Tasks:**
1. **Flask Application Setup**
   ```python
   # backend/requirements.txt
   Flask==2.3.2
   Flask-SQLAlchemy==3.0.5
   Flask-JWT-Extended==4.5.2
   Flask-CORS==4.0.0
   pandas==2.0.3
   scikit-learn==1.3.0
   numpy==1.24.3
   python-dotenv==1.0.0
   redis==4.6.0
   celery==5.3.1
   gunicorn==21.2.0
   ```

2. **Basic Flask Application Structure**
   ```python
   # backend/app/__init__.py
   from flask import Flask
   from flask_sqlalchemy import SQLAlchemy
   from flask_jwt_extended import JWTManager
   from flask_cors import CORS
   
   db = SQLAlchemy()
   jwt = JWTManager()
   
   def create_app():
       app = Flask(__name__)
       app.config.from_object('config.Config')
       
       db.init_app(app)
       jwt.init_app(app)
       CORS(app)
       
       # Register blueprints
       from app.routes import main
       app.register_blueprint(main)
       
       return app
   ```

3. **Database Models Setup**
   ```python
   # backend/app/models/transaction.py
   from app import db
   from datetime import datetime
   
   class Transaction(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       amount = db.Column(db.Float, nullable=False)
       timestamp = db.Column(db.DateTime, default=datetime.utcnow)
       merchant_id = db.Column(db.String(100))
       user_id = db.Column(db.String(100))
       is_fraud = db.Column(db.Boolean, default=False)
       fraud_score = db.Column(db.Float)
       created_at = db.Column(db.DateTime, default=datetime.utcnow)
   ```

#### **Deliverables:**
- [ ] Flask application with basic structure
- [ ] Database models defined
- [ ] Basic API endpoints structure

### **Day 5-6: Frontend Foundation**

#### **Tasks:**
1. **React Application Setup**
   ```bash
   cd frontend
   npx create-react-app . --template typescript
   npm install @mui/material @emotion/react @emotion/styled
   npm install @mui/icons-material
   npm install axios react-router-dom
   npm install recharts
   ```

2. **Basic Component Structure**
   ```jsx
   // frontend/src/components/Dashboard.tsx
   import React from 'react';
   import { Container, Grid, Paper, Typography } from '@mui/material';
   
   const Dashboard: React.FC = () => {
     return (
       <Container maxWidth="lg">
         <Grid container spacing={3}>
           <Grid item xs={12}>
             <Paper>
               <Typography variant="h4">
                 Fraud Detection Dashboard
               </Typography>
             </Paper>
           </Grid>
         </Grid>
       </Container>
     );
   };
   
   export default Dashboard;
   ```

3. **Routing Setup**
   ```jsx
   // frontend/src/App.tsx
   import React from 'react';
   import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
   import Dashboard from './components/Dashboard';
   import TransactionList from './components/TransactionList';
   
   function App() {
     return (
       <Router>
         <Routes>
           <Route path="/" element={<Dashboard />} />
           <Route path="/transactions" element={<TransactionList />} />
         </Routes>
       </Router>
     );
   }
   
   export default App;
   ```

#### **Deliverables:**
- [ ] React application with TypeScript
- [ ] Basic component structure
- [ ] Routing configuration
- [ ] UI framework integration

### **Day 7: Docker Setup**

#### **Tasks:**
1. **Backend Dockerfile**
   ```dockerfile
   # backend/Dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 5000
   
   CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
   ```

2. **Frontend Dockerfile**
   ```dockerfile
   # frontend/Dockerfile
   FROM node:18-alpine
   
   WORKDIR /app
   
   COPY package*.json ./
   RUN npm ci --only=production
   
   COPY . .
   RUN npm run build
   
   EXPOSE 3000
   
   CMD ["npm", "start"]
   ```

3. **Docker Compose Configuration**
   ```yaml
   # docker-compose.yml
   version: '3.8'
   
   services:
     backend:
       build: ./backend
       ports:
         - "5000:5000"
       environment:
         - DATABASE_URL=postgresql://user:password@db:5432/frauddb
         - REDIS_URL=redis://redis:6379
       depends_on:
         - db
         - redis
   
     frontend:
       build: ./frontend
       ports:
         - "3000:3000"
       depends_on:
         - backend
   
     db:
       image: postgres:15
       environment:
         POSTGRES_DB: frauddb
         POSTGRES_USER: user
         POSTGRES_PASSWORD: password
       volumes:
         - postgres_data:/var/lib/postgresql/data
   
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
   
   volumes:
     postgres_data:
   ```

#### **Deliverables:**
- [ ] Dockerized backend and frontend
- [ ] Docker Compose configuration
- [ ] Local development environment ready

---

## **WEEK 2: DATA FOUNDATION & INITIAL ML SETUP**

### **Day 8-9: Data Acquisition & Setup**

#### **Tasks:**
1. **Kaggle Dataset Download**
   ```python
   # Create notebook: ml_notebooks/data_acquisition.ipynb
   import pandas as pd
   import numpy as np
   from sklearn.model_selection import train_test_split
   
   # Instructions to download datasets:
   # 1. Credit Card Fraud Detection: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
   # 2. PaySim Synthetic: https://www.kaggle.com/datasets/ealaxi/paysim1
   
   # Load and initial exploration
   def load_creditcard_data():
       df = pd.read_csv('../data/raw/creditcard.csv')
       print(f"Dataset shape: {df.shape}")
       print(f"Fraud percentage: {df['Class'].mean()*100:.2f}%")
       return df
   
   def basic_eda(df):
       print("Basic Statistics:")
       print(df.describe())
       print("\nMissing Values:")
       print(df.isnull().sum())
       return df
   ```

2. **Data Storage Setup**
   ```python
   # backend/app/utils/data_loader.py
   import pandas as pd
   from app.models.transaction import Transaction
   from app import db
   
   def load_sample_data():
       """Load sample data into database for testing"""
       # Implementation for loading sample transactions
       pass
   
   def create_synthetic_transactions(n=1000):
       """Create synthetic transactions for testing"""
       # Implementation for generating test data
       pass
   ```

#### **Deliverables:**
- [ ] Downloaded fraud detection datasets
- [ ] Initial data exploration notebooks
- [ ] Data loading utilities

### **Day 10-11: Basic ML Pipeline**

#### **Tasks:**
1. **Feature Engineering Foundation**
   ```python
   # backend/app/ml/feature_engineering.py
   import pandas as pd
   import numpy as np
   from sklearn.preprocessing import StandardScaler, LabelEncoder
   
   class FeatureEngineer:
       def __init__(self):
           self.scaler = StandardScaler()
           self.encoders = {}
       
       def create_features(self, df):
           """Create basic features for fraud detection"""
           features = df.copy()
           
           # Amount-based features
           features['amount_log'] = np.log1p(features['Amount'])
           
           # Time-based features (if Time column exists)
           if 'Time' in features.columns:
               features['hour'] = (features['Time'] / 3600) % 24
           
           return features
       
       def fit_transform(self, X):
           """Fit and transform features"""
           return self.scaler.fit_transform(X)
       
       def transform(self, X):
           """Transform features using fitted scaler"""
           return self.scaler.transform(X)
   ```

2. **Basic Model Training**
   ```python
   # backend/app/ml/models.py
   from sklearn.ensemble import IsolationForest, RandomForestClassifier
   from sklearn.metrics import classification_report, roc_auc_score
   import joblib
   import os
   
   class FraudDetectionModel:
       def __init__(self, model_type='isolation_forest'):
           self.model_type = model_type
           if model_type == 'isolation_forest':
               self.model = IsolationForest(contamination=0.1, random_state=42)
           elif model_type == 'random_forest':
               self.model = RandomForestClassifier(n_estimators=100, random_state=42)
       
       def train(self, X_train, y_train=None):
           """Train the model"""
           if self.model_type == 'isolation_forest':
               self.model.fit(X_train)
           else:
               self.model.fit(X_train, y_train)
       
       def predict(self, X):
           """Make predictions"""
           if self.model_type == 'isolation_forest':
               # Convert -1/1 to 0/1 for fraud/normal
               predictions = self.model.predict(X)
               return (predictions == -1).astype(int)
           else:
               return self.model.predict(X)
       
       def predict_proba(self, X):
           """Get prediction probabilities"""
           if hasattr(self.model, 'predict_proba'):
               return self.model.predict_proba(X)[:, 1]
           else:
               # For Isolation Forest, use decision_function
               scores = self.model.decision_function(X)
               # Normalize to 0-1 range
               return (scores - scores.min()) / (scores.max() - scores.min())
       
       def save_model(self, filepath):
           """Save trained model"""
           os.makedirs(os.path.dirname(filepath), exist_ok=True)
           joblib.dump(self.model, filepath)
       
       def load_model(self, filepath):
           """Load trained model"""
           self.model = joblib.load(filepath)
   ```

#### **Deliverables:**
- [ ] Feature engineering pipeline
- [ ] Basic ML model implementation
- [ ] Model training and evaluation utilities

### **Day 12-13: API Integration**

#### **Tasks:**
1. **Prediction API Endpoint**
   ```python
   # backend/app/routes/ml_routes.py
   from flask import Blueprint, request, jsonify
   from app.ml.models import FraudDetectionModel
   from app.ml.feature_engineering import FeatureEngineer
   import numpy as np
   
   ml_bp = Blueprint('ml', __name__)
   
   # Load pre-trained model and feature engineer
   model = FraudDetectionModel()
   feature_engineer = FeatureEngineer()
   
   @ml_bp.route('/predict', methods=['POST'])
   def predict_fraud():
       try:
           data = request.get_json()
           
           # Extract features from request
           features = np.array([data['features']])
           
           # Engineer features
           processed_features = feature_engineer.transform(features)
           
           # Make prediction
           prediction = model.predict(processed_features)[0]
           probability = model.predict_proba(processed_features)[0]
           
           return jsonify({
               'is_fraud': bool(prediction),
               'fraud_probability': float(probability),
               'status': 'success'
           })
       
       except Exception as e:
           return jsonify({
               'error': str(e),
               'status': 'error'
           }), 400
   
   @ml_bp.route('/model/status', methods=['GET'])
   def model_status():
       return jsonify({
           'model_loaded': True,
           'model_type': model.model_type,
           'status': 'ready'
       })
   ```

2. **Transaction Processing API**
   ```python
   # backend/app/routes/transaction_routes.py
   from flask import Blueprint, request, jsonify
   from app.models.transaction import Transaction
   from app import db
   from datetime import datetime
   
   transaction_bp = Blueprint('transactions', __name__)
   
   @transaction_bp.route('/transactions', methods=['POST'])
   def create_transaction():
       try:
           data = request.get_json()
           
           # Create new transaction
           transaction = Transaction(
               amount=data['amount'],
               merchant_id=data.get('merchant_id'),
               user_id=data.get('user_id'),
               timestamp=datetime.utcnow()
           )
           
           # TODO: Integrate with ML prediction
           # For now, set default values
           transaction.fraud_score = 0.0
           transaction.is_fraud = False
           
           db.session.add(transaction)
           db.session.commit()
           
           return jsonify({
               'transaction_id': transaction.id,
               'status': 'created'
           }), 201
       
       except Exception as e:
           return jsonify({'error': str(e)}), 400
   
   @transaction_bp.route('/transactions', methods=['GET'])
   def get_transactions():
       transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(100).all()
       return jsonify([{
           'id': t.id,
           'amount': t.amount,
           'merchant_id': t.merchant_id,
           'user_id': t.user_id,
           'is_fraud': t.is_fraud,
           'fraud_score': t.fraud_score,
           'timestamp': t.timestamp.isoformat()
       } for t in transactions])
   ```

#### **Deliverables:**
- [ ] ML prediction API endpoints
- [ ] Transaction management APIs
- [ ] API testing and validation

### **Day 14: Testing & Documentation**

#### **Tasks:**
1. **Unit Tests Setup**
   ```python
   # backend/tests/test_ml.py
   import unittest
   from app.ml.models import FraudDetectionModel
   from app.ml.feature_engineering import FeatureEngineer
   import numpy as np
   
   class TestMLModels(unittest.TestCase):
       def setUp(self):
           self.model = FraudDetectionModel()
           self.feature_engineer = FeatureEngineer()
       
       def test_model_prediction(self):
           # Test basic model functionality
           X_test = np.random.rand(10, 30)  # Sample features
           predictions = self.model.predict(X_test)
           self.assertEqual(len(predictions), 10)
       
       def test_feature_engineering(self):
           # Test feature engineering
           sample_data = {
               'Amount': [100, 200, 300],
               'Time': [3600, 7200, 10800]
           }
           features = self.feature_engineer.create_features(pd.DataFrame(sample_data))
           self.assertIn('amount_log', features.columns)
   
   if __name__ == '__main__':
       unittest.main()
   ```

2. **API Documentation**
   ```markdown
   # API Documentation
   
   ## Endpoints
   
   ### POST /api/predict
   Predict fraud probability for a transaction
   
   **Request Body:**
   ```json
   {
     "features": [1.0, 2.0, 3.0, ...]  // Array of numerical features
   }
   ```
   
   **Response:**
   ```json
   {
     "is_fraud": false,
     "fraud_probability": 0.15,
     "status": "success"
   }
   ```
   
   ### GET /api/transactions
   Get list of recent transactions
   
   **Response:**
   ```json
   [
     {
       "id": 1,
       "amount": 100.0,
       "is_fraud": false,
       "fraud_score": 0.15,
       "timestamp": "2025-08-22T10:00:00"
     }
   ]
   ```
   ```

3. **Phase 1 Completion Checklist**
   ```markdown
   # Phase 1 Completion Checklist
   
   ## Environment Setup ✅
   - [ ] Python virtual environment
   - [ ] Node.js and npm
   - [ ] Docker and Docker Compose
   - [ ] Git repository setup
   
   ## Backend Foundation ✅
   - [ ] Flask application structure
   - [ ] Database models
   - [ ] Basic API endpoints
   - [ ] ML model integration
   
   ## Frontend Foundation ✅
   - [ ] React application setup
   - [ ] Basic components
   - [ ] Routing configuration
   - [ ] API service integration
   
   ## Data & ML Pipeline ✅
   - [ ] Dataset acquisition
   - [ ] Feature engineering pipeline
   - [ ] Basic ML model implementation
   - [ ] Model training utilities
   
   ## Testing & Documentation ✅
   - [ ] Unit tests setup
   - [ ] API documentation
   - [ ] Development guidelines
   - [ ] Docker deployment ready
   ```

#### **Deliverables:**
- [ ] Complete test suite
- [ ] API documentation
- [ ] Phase 1 completion report
- [ ] Ready for Phase 2 development

---

## **PHASE 1 SUCCESS CRITERIA**

### **Technical Criteria:**
- ✅ Local development environment fully functional
- ✅ Docker containers running successfully
- ✅ Basic API endpoints responding correctly
- ✅ ML model can make predictions
- ✅ Frontend can display basic dashboard
- ✅ Database operations working

### **Business Criteria:**
- ✅ Can process a sample transaction
- ✅ Can generate fraud prediction
- ✅ Basic monitoring/logging in place
- ✅ Ready for data integration

---

## **NEXT STEPS (Phase 2 Preview)**
1. **Advanced Feature Engineering**
2. **Model Performance Optimization**
3. **Real-time Data Processing**
4. **Enhanced Frontend Dashboard**
5. **Authentication System**

---

## **SUPPORT & TROUBLESHOOTING**

### **Common Issues:**
1. **Docker Permission Issues (Windows)**
   - Ensure Docker Desktop is running
   - Check WSL2 configuration

2. **Python Package Conflicts**
   - Use virtual environment
   - Clear pip cache if needed

3. **Node.js Version Issues**
   - Use Node.js LTS version
   - Clear npm cache

### **Resources:**
- **Flask Documentation:** https://flask.palletsprojects.com/
- **React Documentation:** https://react.dev/
- **Scikit-learn Documentation:** https://scikit-learn.org/
- **Docker Documentation:** https://docs.docker.com/
