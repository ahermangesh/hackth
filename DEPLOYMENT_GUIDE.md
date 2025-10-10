# 🚀 FraudGuard Pro - Deployment Guide

## Quick Setup for Anyone

### 1. **Clone & Install**
```bash
git clone <your-repo-url>
cd hackth
pip install -r requirements.txt
```

### 2. **Run the Application**
```bash
python modern_fraud_dashboard.py
```

### 3. **Access Dashboard**
- Open: `http://localhost:5000`
- The system will show "API Configuration Required"

### 4. **Add Your Google AI API Key**
1. Click **"Configure Now"** or go to **Settings**
2. Enter your Google AI API key
3. Click **"Test API Key"** - system will find best model
4. Save settings

### 5. **Start Analyzing Fraud** 🎯
- Upload CSV files
- Get AI-powered fraud analysis
- View detailed risk assessments

---

## 🔑 Getting Google AI API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create new API key
3. Copy the key (starts with `AIza...`)
4. Add to FraudGuard Pro settings

---

## 📊 CSV Format Support

**UPI Transactions:**
```csv
transaction_id,user_id,amount,transaction_type,location,timestamp
```

**Credit Card:**
```csv
transaction_id,user_id,amount,merchant,category,timestamp
```

**Generic:**
```csv
transaction_id,amount,type,location,timestamp
```

---

## ✨ Features

- **🤖 AI-Powered Analysis** - Smart fraud detection with explanations
- **📊 Professional Dashboard** - Clean, modern interface
- **🌓 Dark/Light Theme** - User preference support
- **📱 Responsive Design** - Works on all devices
- **🔒 Secure** - No API keys stored in code
- **⚡ Fast Processing** - Real-time analysis

---

## 🛠️ No Setup Required

- ❌ No database setup needed
- ❌ No complex configuration
- ❌ No API keys in code
- ✅ Just run and add your API key!

---

## 🔧 Troubleshooting

**"API Configuration Required"**
- Add your Google AI API key in Settings
- Test the key to ensure it works
- System will auto-select best model

**CSV Upload Issues**
- Ensure CSV has required columns
- Check file format is valid CSV
- File size limit: 50MB

**AI Analysis Not Working**
- Verify API key is valid
- Check Google AI billing status
- Test key in Settings page

---

## 🌟 Ready to Deploy!

Your FraudGuard Pro system is now completely self-contained and ready for deployment. Users just need to:

1. **Run the application**
2. **Add their API key**
3. **Start detecting fraud!**

No complex setup, no hardcoded credentials - just professional fraud detection! 🚀
