#!/usr/bin/env python3
"""
🤖 LLM Integration Demo for FraudGuard
Test different LLM providers and showcase AI-enhanced fraud analysis
"""

import pandas as pd
import time
from llm_integration import LLMFraudAnalyzer, LLMEnhancedFraudUI

def test_llm_providers():
    """Test different LLM providers"""
    print("🤖 Testing LLM Providers")
    print("="*50)
    
    providers = ["ollama", "openai", "anthropic"]
    working_providers = []
    
    for provider in providers:
        print(f"\n🔍 Testing {provider}...")
        try:
            llm = LLMFraudAnalyzer(api_provider=provider)
            
            # Simple test
            test_prompt = "Hello, can you help with fraud detection?"
            response = llm._call_llm(test_prompt, max_tokens=100)
            
            if "error" not in response.lower() and len(response) > 10:
                print(f"   ✅ {provider}: Working")
                working_providers.append(provider)
            else:
                print(f"   ❌ {provider}: {response}")
                
        except Exception as e:
            print(f"   ❌ {provider}: {str(e)}")
    
    return working_providers

def demo_fraud_explanation():
    """Demo AI-powered fraud explanation"""
    print("\n🧠 AI-Powered Fraud Explanation Demo")
    print("="*50)
    
    # Try to get working LLM
    working_providers = test_llm_providers()
    
    if not working_providers:
        print("❌ No LLM providers available. Please set up:")
        print("   - Ollama (local): ollama pull llama3:8b")
        print("   - OpenAI: export OPENAI_API_KEY=your-key")
        print("   - Anthropic: export ANTHROPIC_API_KEY=your-key")
        return
    
    # Use first working provider
    provider = working_providers[0]
    print(f"🤖 Using {provider} for demo...")
    
    try:
        llm_analyzer = LLMFraudAnalyzer(api_provider=provider)
        
        # Example suspicious transaction
        suspicious_transaction = {
            "transaction_id": "TXN_123456",
            "amount": 5000.0,
            "transaction_type": "P2P",
            "hour": 2,  # 2 AM
            "is_weekend": 1,
            "device_type": "Android",
            "location": "Mumbai",
            "payer_vpa": "user123456@paytm",
            "payee_vpa": "merchant@phonepe"
        }
        
        # Simulate ML prediction
        ml_prediction = 1  # Fraud detected
        confidence = 0.95
        feature_importance = {
            "high_amount": 0.45,
            "suspicious_hour": 0.30,
            "weekend_transaction": 0.15,
            "cross_bank_transfer": 0.10
        }
        
        print("\n📊 Transaction Details:")
        for key, value in suspicious_transaction.items():
            print(f"   {key}: {value}")
        
        print(f"\n🎯 ML Prediction: {'FRAUD' if ml_prediction else 'LEGITIMATE'}")
        print(f"🎯 Confidence: {confidence:.1%}")
        
        print("\n🤖 Generating AI explanation...")
        start_time = time.time()
        
        explanation = llm_analyzer.explain_fraud_decision(
            suspicious_transaction, ml_prediction, confidence, feature_importance
        )
        
        end_time = time.time()
        
        print(f"\n🧠 AI Analysis (took {end_time - start_time:.1f}s):")
        print("="*60)
        print(explanation)
        print("="*60)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def demo_natural_language_queries():
    """Demo natural language queries about fraud data"""
    print("\n💬 Natural Language Query Demo")
    print("="*50)
    
    # Check if test data exists
    if not pd.io.common.file_exists('test_upi_transactions.csv'):
        print("❌ Test data not found. Run generate_test_data.py first")
        return
    
    # Load test data
    df = pd.read_csv('test_upi_transactions.csv')
    print(f"📊 Loaded {len(df)} transactions")
    
    # Try to get working LLM
    working_providers = test_llm_providers()
    if not working_providers:
        print("❌ No LLM providers available")
        return
    
    provider = working_providers[0]
    llm_analyzer = LLMFraudAnalyzer(api_provider=provider)
    
    # Example questions
    questions = [
        "What percentage of transactions are fraudulent?",
        "What are the peak hours for fraud?",
        "What's the average amount of fraudulent transactions?",
        "What patterns do you see in the fraud data?"
    ]
    
    for question in questions:
        print(f"\n❓ Question: {question}")
        print("🤖 AI Answer:", end=" ")
        
        try:
            answer = llm_analyzer.natural_language_query(question, df)
            print(answer)
        except Exception as e:
            print(f"Error: {e}")

def demo_pattern_analysis():
    """Demo fraud pattern analysis"""
    print("\n📈 Fraud Pattern Analysis Demo")
    print("="*50)
    
    # Check if test data exists
    if not pd.io.common.file_exists('test_upi_transactions.csv'):
        print("❌ Test data not found. Run generate_test_data.py first")
        return
    
    # Load and filter fraud cases
    df = pd.read_csv('test_upi_transactions.csv')
    fraud_cases = df[df['is_fraud'] == 1]
    
    print(f"📊 Analyzing {len(fraud_cases)} fraud cases from {len(df)} total transactions")
    
    # Try to get working LLM
    working_providers = test_llm_providers()
    if not working_providers:
        print("❌ No LLM providers available")
        return
    
    provider = working_providers[0]
    llm_analyzer = LLMFraudAnalyzer(api_provider=provider)
    
    print("\n🤖 Generating fraud pattern analysis...")
    
    try:
        pattern_analysis = llm_analyzer.analyze_fraud_patterns(fraud_cases)
        
        print("\n📋 Fraud Intelligence Report:")
        print("="*60)
        print(pattern_analysis)
        print("="*60)
        
    except Exception as e:
        print(f"❌ Pattern analysis failed: {e}")

def demo_feature_suggestions():
    """Demo AI feature engineering suggestions"""
    print("\n🔧 AI Feature Engineering Demo")
    print("="*50)
    
    # Try to get working LLM
    working_providers = test_llm_providers()
    if not working_providers:
        print("❌ No LLM providers available")
        return
    
    provider = working_providers[0]
    llm_analyzer = LLMFraudAnalyzer(api_provider=provider)
    
    # Current features for UPI
    current_upi_features = [
        "amount", "transaction_type", "hour", "day_of_week",
        "payer_bank", "payee_bank", "device_type", "location"
    ]
    
    print(f"🏦 Current UPI Features: {', '.join(current_upi_features)}")
    print("\n🤖 Asking AI for feature engineering suggestions...")
    
    try:
        suggestions = llm_analyzer.suggest_feature_engineering(
            transaction_type="UPI",
            current_features=current_upi_features
        )
        
        print("\n💡 AI Feature Suggestions:")
        print("="*60)
        print(suggestions)
        print("="*60)
        
    except Exception as e:
        print(f"❌ Feature suggestion failed: {e}")

def main():
    """Run all LLM integration demos"""
    print("🤖 FraudGuard LLM Integration Demo")
    print("="*60)
    print("Testing AI-enhanced fraud detection capabilities")
    print()
    
    # Test basic LLM functionality
    demo_fraud_explanation()
    
    # Test natural language queries
    demo_natural_language_queries()
    
    # Test pattern analysis
    demo_pattern_analysis()
    
    # Test feature suggestions
    demo_feature_suggestions()
    
    print("\n🎯 Demo Complete!")
    print("\nTo start the AI-enhanced UI:")
    print("   python ai_enhanced_fraud_ui.py")
    print("   Open: http://localhost:5000")
    
    print("\nTo configure LLM providers:")
    print("   See LLM_INTEGRATION_GUIDE.md for detailed setup instructions")

if __name__ == "__main__":
    main()
