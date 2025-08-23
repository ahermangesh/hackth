#!/usr/bin/env python3
"""
Test Gemini AI Integration for FraudGuard System
Tests the Google Gemini API with provided API key
"""

import os
import sys
from llm_integration import LLMFraudAnalyzer

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("💡 Install python-dotenv: pip install python-dotenv")

# Set your Gemini API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def test_gemini_integration():
    """Test Gemini AI integration"""
    print("🤖 Testing Gemini AI Integration")
    print("=" * 50)
    
    # Set environment variable
    os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
    
    try:
        # First install the required package
        print("📦 Installing Google Generative AI package...")
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pip", "install", "google-generativeai"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Package installed successfully!")
        else:
            print(f"❌ Package installation failed: {result.stderr}")
            return
        
        # Initialize Gemini analyzer
        print("\n🧠 Initializing Gemini AI analyzer...")
        analyzer = LLMFraudAnalyzer(api_provider="gemini", api_key=GEMINI_API_KEY)
        
        # Test transaction data
        test_transaction = {
            "transaction_id": "TXN_123456",
            "amount": 15000,
            "transaction_type": "P2P",
            "hour": 2,
            "day_of_week": 6,  # Sunday
            "is_weekend": 1,
            "payer_bank": "SBI",
            "payee_bank": "HDFC", 
            "device_type": "Android",
            "location": "Mumbai",
            "payer_vpa": "user123@paytm",
            "payee_vpa": "unknown_merchant@phonepe"
        }
        
        feature_importance = {
            "amount": 0.35,
            "hour": 0.25,
            "is_weekend": 0.15,
            "cross_bank": 0.15,
            "device_type": 0.10
        }
        
        print("📊 Test Transaction Details:")
        for key, value in test_transaction.items():
            print(f"   {key}: {value}")
        
        print(f"\n🚨 ML Prediction: FRAUD")
        print(f"🎯 Confidence: 89%")
        
        print("\n🤖 Generating Gemini AI explanation...")
        
        # Get AI explanation
        explanation = analyzer.explain_fraud_decision(
            test_transaction, 
            prediction=1,  # Fraud
            confidence=89.0,
            feature_importance=feature_importance
        )
        
        print("\n🧠 Gemini AI Analysis:")
        print("=" * 60)
        print(explanation)
        print("=" * 60)
        
        # Test natural language query
        print("\n💬 Testing Natural Language Query...")
        query_response = analyzer.answer_query(
            "What are the main risk factors in this transaction?",
            data=test_transaction
        )
        
        print(f"❓ Query: What are the main risk factors in this transaction?")
        print(f"🤖 Gemini Response:")
        print(query_response)
        
        print("\n✅ Gemini integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing Gemini integration: {str(e)}")
        print("Please check your API key and internet connection.")

def test_provider_comparison():
    """Compare different LLM providers"""
    print("\n🔄 Testing Multiple AI Providers")
    print("=" * 50)
    
    providers = ["gemini", "ollama"]  # Test available providers
    
    for provider in providers:
        print(f"\n🧠 Testing {provider.upper()}...")
        try:
            if provider == "gemini":
                analyzer = LLMFraudAnalyzer(api_provider=provider, api_key=GEMINI_API_KEY)
            else:
                analyzer = LLMFraudAnalyzer(api_provider=provider)
            
            # Simple test query
            response = analyzer._call_llm("What is fraud detection?", max_tokens=100)
            
            if "error" in response.lower() or "not provided" in response.lower():
                print(f"   ❌ {provider}: {response[:100]}...")
            else:
                print(f"   ✅ {provider}: Working")
                print(f"      Sample: {response[:80]}...")
        
        except Exception as e:
            print(f"   ❌ {provider}: Error - {str(e)}")

if __name__ == "__main__":
    print("🛡️ FraudGuard Gemini AI Integration Test")
    print("=" * 60)
    print("Testing Google Gemini AI for fraud detection enhancement\n")
    
    test_gemini_integration()
    test_provider_comparison()
    
    print("\n🚀 Next Steps:")
    print("1. Use 'gemini' as api_provider in your fraud detection system")
    print("2. Set GEMINI_API_KEY environment variable for production")
    print("3. Run: python ai_enhanced_fraud_ui.py")
    print("4. Experience AI-enhanced fraud detection with Gemini!")
