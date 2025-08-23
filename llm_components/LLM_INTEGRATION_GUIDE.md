# 🤖 LLM Integration Guide for FraudGuard

## 🎯 Overview
This guide shows you how to integrate different LLM providers into the FraudGuard fraud detection system for intelligent analysis and explanations.

## 🔧 Available LLM Providers

### 1. 🦙 Ollama (Local - Recommended for Development)
**Pros**: Free, private, no API keys needed
**Cons**: Requires local installation

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download a model (choose one)
ollama pull llama3:8b          # Good balance of speed/quality
ollama pull llama3:70b         # Best quality (requires more RAM)
ollama pull codellama:7b       # Good for technical analysis

# Start Ollama service
ollama serve
```

**Usage in code:**
```python
llm_analyzer = LLMFraudAnalyzer(api_provider="ollama")
```

### 2. 🤖 OpenAI (Most Capable)
**Pros**: Highest quality responses, best reasoning
**Cons**: Costs money, requires internet

**Setup:**
```bash
# Get API key from https://platform.openai.com/
export OPENAI_API_KEY="your-api-key-here"

# Or create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

**Usage in code:**
```python
llm_analyzer = LLMFraudAnalyzer(
    api_provider="openai",
    api_key="your-api-key"  # or None to use env variable
)
```

**Cost Estimates (GPT-4o-mini):**
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- ~$0.01 per fraud analysis

### 3. 🧠 Anthropic Claude (High Quality)
**Pros**: Excellent reasoning, good for analysis
**Cons**: Costs money, requires internet

**Setup:**
```bash
# Get API key from https://console.anthropic.com/
export ANTHROPIC_API_KEY="your-api-key-here"
```

**Usage in code:**
```python
llm_analyzer = LLMFraudAnalyzer(api_provider="anthropic")
```

### 4. 🤗 Hugging Face (Free Tier Available)
**Pros**: Many free models, good for experimentation
**Cons**: Rate limits, variable quality

**Setup:**
```bash
# Get API key from https://huggingface.co/settings/tokens
export HUGGINGFACE_API_KEY="your-api-key-here"
```

**Usage in code:**
```python
llm_analyzer = LLMFraudAnalyzer(api_provider="huggingface")
```

## 🚀 Quick Start Integration

### Step 1: Choose Your Provider
```python
# Option 1: Local Ollama (Free)
llm_analyzer = LLMFraudAnalyzer(api_provider="ollama")

# Option 2: OpenAI (Best Quality)
llm_analyzer = LLMFraudAnalyzer(api_provider="openai", api_key="your-key")

# Option 3: Auto-detect (tries providers in order)
llm_analyzer = LLMFraudAnalyzer()  # Will try ollama -> openai -> anthropic
```

### Step 2: Enhanced Fraud Analysis
```python
from llm_integration import LLMFraudAnalyzer, LLMEnhancedFraudUI

# Initialize
llm_analyzer = LLMFraudAnalyzer(api_provider="ollama")
llm_ui = LLMEnhancedFraudUI(llm_analyzer)

# Example fraud transaction
transaction = {
    "amount": 5000.0,
    "transaction_type": "P2P",
    "hour": 2,  # 2 AM
    "is_weekend": 1,
    "device_type": "Android"
}

# ML prediction (from your existing model)
ml_prediction = 1  # Fraud detected
confidence = 0.95
feature_importance = {
    "high_amount": 0.45,
    "hour": 0.30,
    "is_weekend": 0.15
}

# Get AI explanation
explanation = llm_analyzer.explain_fraud_decision(
    transaction, ml_prediction, confidence, feature_importance
)

print("🤖 AI Analysis:")
print(explanation)
```

### Step 3: Natural Language Queries
```python
import pandas as pd

# Load your fraud data
fraud_data = pd.read_csv('test_upi_transactions.csv')

# Ask questions in natural language
questions = [
    "What are the main patterns in fraud transactions?",
    "At what times of day do most frauds occur?",
    "What amount ranges are most suspicious?",
    "How can we improve our fraud detection?"
]

for question in questions:
    answer = llm_analyzer.natural_language_query(question, fraud_data)
    print(f"Q: {question}")
    print(f"A: {answer}\n")
```

## 🎨 UI Integration Examples

### Basic Integration
```python
# In your Flask app
from llm_integration import LLMFraudAnalyzer

app = Flask(__name__)

# Initialize LLM
try:
    llm_analyzer = LLMFraudAnalyzer(api_provider="ollama")
    llm_enabled = True
except:
    llm_enabled = False

@app.route('/analyze', methods=['POST'])
def analyze_with_ai():
    # Your existing fraud detection
    ml_result = your_fraud_detection_function(data)
    
    # Add AI explanation
    if llm_enabled:
        ai_explanation = llm_analyzer.explain_fraud_decision(
            transaction_data, ml_result['prediction'], 
            ml_result['confidence'], ml_result['features']
        )
        ml_result['ai_explanation'] = ai_explanation
    
    return jsonify(ml_result)
```

### Advanced Chat Interface
```python
@app.route('/chat', methods=['POST'])
def chat_with_ai():
    user_message = request.json['message']
    context_data = get_user_context()  # Your data context
    
    if llm_enabled:
        response = llm_analyzer.natural_language_query(user_message, context_data)
    else:
        response = "AI chat is currently disabled"
    
    return jsonify({'response': response})
```

## 💡 Use Cases & Examples

### 1. Fraud Explanation
```python
# When fraud is detected, explain why
explanation = llm_analyzer.explain_fraud_decision(
    transaction_data={
        "amount": 10000,
        "hour": 3,
        "transaction_type": "P2P",
        "location": "foreign"
    },
    prediction=1,  # Fraud
    confidence=0.92,
    feature_importance={"amount": 0.4, "hour": 0.3, "location": 0.3}
)
# Returns: "This transaction is flagged as fraud due to the high amount ($10,000) 
#          occurring at 3 AM, which is outside normal business hours..."
```

### 2. Pattern Analysis
```python
# Analyze fraud patterns in your dataset
fraud_cases = df[df['is_fraud'] == 1]
pattern_report = llm_analyzer.analyze_fraud_patterns(fraud_cases)
# Returns comprehensive analysis of fraud trends, risk factors, recommendations
```

### 3. Feature Engineering Suggestions
```python
# Get AI suggestions for new features
suggestions = llm_analyzer.suggest_feature_engineering(
    transaction_type="UPI",
    current_features=["amount", "hour", "device_type"]
)
# Returns suggestions for new features to improve detection
```

### 4. Business Reporting
```python
# Generate executive reports
analysis_results = {
    "total_transactions": 10000,
    "fraud_detected": 150,
    "accuracy": 0.987,
    "top_risk_factors": {...}
}

report = llm_analyzer.generate_fraud_report(analysis_results)
# Returns professional business report with insights and recommendations
```

## 🔧 Configuration Options

### Environment Variables
```bash
# API Keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export HUGGINGFACE_API_KEY="your-hf-key"

# Model Selection
export LLM_PROVIDER="ollama"          # Default provider
export OLLAMA_MODEL="llama3:8b"       # Ollama model
export OPENAI_MODEL="gpt-4o-mini"     # OpenAI model
```

### Custom Configuration
```python
# Custom provider settings
llm_analyzer = LLMFraudAnalyzer(
    api_provider="openai",
    api_key="your-key",
    model="gpt-4",  # Override default model
    max_tokens=1500,  # Longer responses
    temperature=0.2   # More consistent responses
)
```

## 🚀 Running the AI-Enhanced System

### Start the Enhanced UI
```bash
# Run the AI-enhanced fraud detection system
python ai_enhanced_fraud_ui.py

# Open in browser
http://localhost:5000
```

### Features Available:
- 🤖 **AI Chat Assistant**: Ask questions about fraud patterns
- 🧠 **Intelligent Explanations**: Get detailed reasons for fraud decisions
- 📊 **Natural Language Queries**: "Show me fraud patterns by time of day"
- 📈 **Smart Reporting**: Generate business-ready fraud reports
- 🎯 **Real-time Analysis**: Upload data and get AI insights instantly

## 💰 Cost Considerations

### Free Options:
1. **Ollama (Local)**: Completely free, runs on your hardware
2. **Hugging Face**: Free tier available with rate limits

### Paid Options:
1. **OpenAI**: ~$0.01 per fraud analysis (GPT-4o-mini)
2. **Anthropic**: Similar pricing to OpenAI

### Recommendations:
- **Development**: Use Ollama (free, private)
- **Production (Budget)**: OpenAI GPT-4o-mini
- **Production (Premium)**: OpenAI GPT-4 or Claude-3

## 🔒 Security & Privacy

### Local Processing (Ollama):
- ✅ Data never leaves your server
- ✅ No API keys required
- ✅ Complete privacy control

### Cloud APIs:
- ⚠️ Data sent to third-party services
- ⚠️ Consider data sensitivity
- ✅ Use for non-sensitive analysis only

## 🐛 Troubleshooting

### Common Issues:

1. **"LLM provider not configured"**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Or check API keys
   echo $OPENAI_API_KEY
   ```

2. **"Model not found"**
   ```bash
   # Download Ollama model
   ollama pull llama3:8b
   ```

3. **"API rate limit exceeded"**
   - Reduce request frequency
   - Upgrade API plan
   - Switch to local Ollama

### Debug Mode:
```python
# Enable detailed error logging
import logging
logging.basicConfig(level=logging.DEBUG)

llm_analyzer = LLMFraudAnalyzer(api_provider="ollama", debug=True)
```

## 🎯 Next Steps

1. **Choose your LLM provider** based on your needs
2. **Set up API keys** or install Ollama
3. **Run the enhanced UI**: `python ai_enhanced_fraud_ui.py`
4. **Upload test data** and see AI explanations in action
5. **Customize prompts** for your specific use case

The AI-enhanced fraud detection system is now ready to provide intelligent analysis and explanations for your fraud detection decisions! 🚀
