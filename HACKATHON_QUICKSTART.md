# 🚀 HACKATHON FRAUD DETECTION SYSTEM - QUICK START

## **⚡ IMMEDIATE SETUP (5 minutes)**

### **Step 1: Install Python Dependencies**
```bash
cd backend
python -m venv fraud_env
# Windows:
fraud_env\Scripts\activate
# Install dependencies:
pip install -r requirements.txt
```

### **Step 2: Start Backend Server**
```bash
# In backend directory:
python app/__init__.py
```
Backend will be available at: `http://localhost:5000`

### **Step 3: Frontend Setup** 
```bash
cd frontend
# If React app creation is complete:
npm install @mui/material @emotion/react @emotion/styled @mui/icons-material
npm install axios recharts react-router-dom
npm start
```
Frontend will be available at: `http://localhost:3000`

---

## **📊 UPLOAD KAGGLE DATA**

### **Step 4: Download Fraud Detection Dataset**
1. Go to: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
2. Download `creditcard.csv`
3. Place in: `data/raw/creditcard.csv`

### **Step 5: Train Model**
```bash
# Option 1: API Upload (Recommended)
# Use the frontend upload feature at http://localhost:3000

# Option 2: Direct API call
curl -X POST -F "file=@data/raw/creditcard.csv" http://localhost:5000/api/ml/train
```

---

## **🎯 HACKATHON DEMO FLOW**

### **1. Dashboard Overview**
- Visit: `http://localhost:3000`
- Shows real-time fraud statistics
- Transaction monitoring

### **2. Upload & Train Model**
- Upload your Kaggle CSV file
- Train ML model (2-3 minutes)
- Model automatically starts detecting fraud

### **3. Generate Sample Data**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"count": 50}' \
  http://localhost:5000/api/transactions/sample
```

### **4. Test Fraud Detection**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "user_id": "user_123",
    "merchant_id": "merchant_456",
    "transaction_type": "credit_card"
  }' \
  http://localhost:5000/api/transactions/
```

---

## **📱 API ENDPOINTS**

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/ml/status` | GET | Check model status |
| `/api/ml/predict` | POST | Predict single transaction |
| `/api/ml/train` | POST | Upload & train model |
| `/api/transactions/` | GET | List transactions |
| `/api/transactions/` | POST | Create transaction |
| `/api/transactions/sample` | POST | Generate sample data |
| `/api/dashboard/stats` | GET | Dashboard statistics |

---

## **🚨 TROUBLESHOOTING**

### **Backend Issues:**
```bash
# If port 5000 is busy:
netstat -ano | findstr :5000
# Kill process and restart

# If dependencies fail:
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### **Frontend Issues:**
```bash
# If npm install fails:
npm cache clean --force
npm install

# If port 3000 is busy:
# React will automatically suggest port 3001
```

### **Docker Issues:**
```bash
# If Docker is preferred:
docker-compose up --build

# Backend only:
docker-compose up backend

# Check logs:
docker-compose logs backend
```

---

## **🏆 HACKATHON SUCCESS CHECKLIST**

### **✅ Must Have (Core Demo):**
- [ ] Backend API running on port 5000
- [ ] Frontend dashboard on port 3000
- [ ] ML model trained with Kaggle data
- [ ] Sample transactions generated
- [ ] Fraud detection working

### **🌟 Nice to Have (Extra Points):**
- [ ] Real-time dashboard updates
- [ ] Multiple ML models comparison
- [ ] Transaction analytics charts
- [ ] Export fraud reports
- [ ] Mobile-responsive design

### **🎯 Demo Script (5 minutes):**
1. **Show Dashboard** - Real-time fraud statistics
2. **Upload Data** - Train model live
3. **Create Transaction** - Show fraud detection
4. **Explain ML** - Show confidence scores
5. **Show Analytics** - Charts and trends

---

## **⚡ SPEED OPTIMIZATION**

### **Fast Setup (Docker):**
```bash
# One-command setup:
docker-compose up --build
```

### **Skip Frontend Build:**
```bash
# Backend only for quick testing:
cd backend
python app/__init__.py
# Test with Postman/curl
```

### **Pre-trained Model:**
```bash
# If you have a pre-trained model:
# Place fraud_model.pkl in data/models/
# Backend will auto-load it
```

---

## **📊 SAMPLE DATA FORMAT**

### **Transaction JSON:**
```json
{
  "amount": 100.50,
  "user_id": "user_123",
  "merchant_id": "merchant_456", 
  "transaction_type": "credit_card",
  "location": "Mumbai",
  "device_id": "device_789"
}
```

### **ML Prediction Response:**
```json
{
  "is_fraud": false,
  "fraud_probability": 0.23,
  "risk_level": "low",
  "confidence": 0.54,
  "status": "success"
}
```

---

## **🎉 READY TO HACK!**

Your fraud detection system is ready for the hackathon! 

**Next Steps:**
1. Start backend server
2. Upload your Kaggle data
3. Generate sample transactions  
4. Build your demo presentation

**Good luck! 🚀**
