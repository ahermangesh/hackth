#!/usr/bin/env python3
"""
Quick test to verify Gemini AI is working with environment variables
"""

import os

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("💡 Install python-dotenv for better environment variable support")

from llm_integration import LLMFraudAnalyzer

def test_gemini():
    print("🧪 Testing Gemini AI Integration...")
    
    try:
        # Initialize using environment variable
        analyzer = LLMFraudAnalyzer(api_provider="gemini")  # Will use GEMINI_API_KEY from .env
        print("✅ Gemini analyzer initialized")
        
        # Test with a simple fraud case
        test_transaction = {
            "amount": 5000,
            "hour": 2,
            "transaction_type": "P2P",
            "location": "Mumbai"
        }
        
        feature_importance = {
            "amount": 0.35,
            "hour": 0.25,
            "location": 0.20
        }
        
        print("🤖 Testing fraud explanation...")
        explanation = analyzer.explain_fraud_decision(
            transaction_data=test_transaction,
            prediction=1,
            confidence=85.0,
            feature_importance=feature_importance
        )
        
        print("🎯 Gemini Response:")
        print("-" * 50)
        print(explanation)
        print("-" * 50)
        print("✅ Gemini AI is working perfectly!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_gemini()
