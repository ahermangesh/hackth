# 🗂️ FraudGuard Project Organization

## 📁 **Main Directory - Core Working Files**

### 🏆 **Primary Systems:**
- **`working_fraud_api.py`** - Your beautiful UI with pricing, UPI & Credit Card detection (Pre-LLM)
- **`original_fraud_ui.py`** - Original beautiful UI with LLM integration
- **`upi_fraud_detector.py`** - Focused UPI fraud detection
- **`standalone_fraud_detector.py`** - Self-contained rule-based detector

### 🔧 **Utilities:**
- **`status_check.py`** - System status checking utility

## 📁 **llm_components/ - AI Enhancement Components**

### 🧠 **LLM Integration:**
- **`llm_integration.py`** - Core LLM framework (OpenAI, Anthropic, Gemini, Ollama)
- **`ai_enhanced_fraud_ui.py`** - AI-powered web interface
- **`demo_llm_integration.py`** - LLM testing framework
- **`test_gemini_integration.py`** - Gemini AI testing
- **`quick_ai_demo.py`** - Quick AI demonstration
- **`LLM_INTEGRATION_GUIDE.md`** - Complete setup documentation

## 📁 **archive/ - Experimental & Old Versions**

### 🧪 **Test Files:**
- All `test_*.py` files
- All experimental detectors
- Old UI versions
- Development utilities

## 🎯 **Usage Guide:**

### **For Clean Fraud Detection (No AI):**
```bash
python working_fraud_api.py
# Access: http://localhost:5000
```

### **For AI-Enhanced Fraud Detection:**
```bash
python original_fraud_ui.py
# Access: http://localhost:5000
```

### **For Standalone Analysis:**
```bash
python standalone_fraud_detector.py
```

## 🚀 **Development Workflow:**

1. **Primary Development:** Use `working_fraud_api.py` or `original_fraud_ui.py`
2. **AI Features:** Access components in `llm_components/`
3. **Reference:** Check `archive/` for older implementations
4. **Clean Workspace:** Only essential files in main directory

## 📊 **Project Status:**
- ✅ **Core Systems:** Working and organized
- ✅ **LLM Integration:** Separated and modular
- ✅ **Workspace:** Clean and maintainable
- ✅ **Documentation:** Up to date

Your workspace is now organized for efficient development! 🛡️✨
