#!/usr/bin/env python3
"""
🤖 LLM Integration for FraudGuard System
Enhances fraud detection with AI-powered explanations and analysis
"""

import openai
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import requests
import os
from datetime import datetime

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class LLMFraudAnalyzer:
    """Integrates LLM capabilities for enhanced fraud analysis"""
    
    def __init__(self, api_provider="openai", api_key=None):
        """
        Initialize LLM integration
        
        Args:
            api_provider: "openai", "anthropic", "ollama", "gemini", or "huggingface"
            api_key: API key for the service (if required)
        """
        self.api_provider = api_provider
        self.api_key = api_key or os.getenv(f"{api_provider.upper()}_API_KEY")
        
        if api_provider == "openai" and self.api_key:
            openai.api_key = self.api_key
        elif api_provider == "gemini" and self.api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.api_key)
        
        self.setup_provider()
    
    def setup_provider(self):
        """Setup specific provider configurations"""
        if self.api_provider == "openai":
            self.model = "gpt-4o-mini"  # Cost-effective option
            self.endpoint = "https://api.openai.com/v1/chat/completions"
        elif self.api_provider == "anthropic":
            self.model = "claude-3-haiku-20240307"  # Fast and efficient
            self.endpoint = "https://api.anthropic.com/v1/messages"
        elif self.api_provider == "ollama":
            self.model = "llama3:8b"  # Local model
            self.endpoint = "http://localhost:11434/api/generate"
        elif self.api_provider == "gemini":
            self.model = "gemini-1.5-flash"  # Fast and cost-effective
            self.endpoint = None  # Uses SDK
        elif self.api_provider == "huggingface":
            self.model = "microsoft/DialoGPT-medium"
            self.endpoint = "https://api-inference.huggingface.co/models/"
    
    def explain_fraud_decision(self, transaction_data: Dict, prediction: int, 
                             confidence: float, feature_importance: Dict) -> str:
        """
        Generate intelligent explanation for fraud prediction
        
        Args:
            transaction_data: Transaction details
            prediction: 0 (legitimate) or 1 (fraud)
            confidence: Model confidence score
            feature_importance: Top features and their importance scores
        """
        
        # Prepare context for LLM
        context = self._prepare_fraud_context(transaction_data, prediction, 
                                            confidence, feature_importance)
        
        prompt = f"""
        You are an expert fraud analyst. Analyze this transaction and explain the fraud detection decision in simple, actionable terms.
        
        Transaction Details:
        {json.dumps(context, indent=2)}
        
        Provide:
        1. Clear verdict (FRAUD or LEGITIMATE)
        2. Main reasons for the decision (top 3 factors)
        3. Risk level (LOW/MEDIUM/HIGH)
        4. Recommended actions
        5. Confidence explanation
        
        Keep the explanation clear and professional for business users.
        """
        
        response = self._call_llm(prompt)
        return response
    
    def analyze_fraud_patterns(self, fraud_cases: pd.DataFrame) -> str:
        """
        Analyze patterns in fraud cases using LLM
        
        Args:
            fraud_cases: DataFrame containing fraud transactions
        """
        
        # Extract key patterns
        patterns = self._extract_fraud_patterns(fraud_cases)
        
        prompt = f"""
        You are a fraud intelligence analyst. Analyze these fraud patterns and provide strategic insights.
        
        Fraud Patterns Detected:
        {json.dumps(patterns, indent=2)}
        
        Provide:
        1. Key fraud trends and patterns
        2. Risk factors to monitor
        3. Prevention recommendations
        4. Emerging threats identified
        5. Business impact assessment
        
        Format as a professional fraud intelligence report.
        """
        
        response = self._call_llm(prompt)
        return response
    
    def natural_language_query(self, query: str, transaction_data: pd.DataFrame) -> str:
        """
        Answer natural language questions about fraud data
        
        Args:
            query: Natural language question
            transaction_data: DataFrame to analyze
        """
        
        # Prepare data summary
        data_summary = self._prepare_data_summary(transaction_data)
        
        prompt = f"""
        You are a fraud data analyst. Answer this question about our fraud detection data:
        
        Question: {query}
        
        Data Summary:
        {json.dumps(data_summary, indent=2)}
        
        Provide a clear, data-driven answer with specific insights and recommendations.
        """
        
        response = self._call_llm(prompt)
        return response
    
    def generate_fraud_report(self, analysis_results: Dict) -> str:
        """
        Generate comprehensive fraud analysis report
        
        Args:
            analysis_results: Results from fraud detection analysis
        """
        
        prompt = f"""
        You are a senior fraud analyst. Create a comprehensive fraud detection report.
        
        Analysis Results:
        {json.dumps(analysis_results, indent=2)}
        
        Generate a professional report with:
        1. Executive Summary
        2. Key Findings
        3. Fraud Statistics
        4. Risk Assessment
        5. Recommendations
        6. Action Items
        
        Format as a business-ready report with clear insights and actionable recommendations.
        """
        
        response = self._call_llm(prompt)
        return response
    
    def suggest_feature_engineering(self, transaction_type: str, 
                                  current_features: List[str]) -> str:
        """
        Suggest new features for fraud detection using domain expertise
        
        Args:
            transaction_type: "UPI" or "Credit Card"
            current_features: List of existing features
        """
        
        prompt = f"""
        You are a machine learning engineer specializing in fraud detection.
        
        Transaction Type: {transaction_type}
        Current Features: {current_features}
        
        Suggest 10 new features that could improve fraud detection for {transaction_type} transactions.
        
        For each feature, provide:
        1. Feature name
        2. Description
        3. How to calculate it
        4. Why it's useful for fraud detection
        5. Implementation complexity (LOW/MEDIUM/HIGH)
        
        Focus on features that capture fraud patterns specific to {transaction_type}.
        """
        
        response = self._call_llm(prompt)
        return response
    
    def answer_query(self, question: str, data: Any = None) -> str:
        """
        Answer natural language questions about fraud data
        
        Args:
            question: User's question in natural language
            data: Optional data context for the question
        """
        
        prompt = f"""
        You are an expert fraud analyst. Answer the following question about fraud detection:
        
        Question: {question}
        
        Context Data: {data if data else "General fraud detection knowledge"}
        
        Provide a clear, concise answer with specific insights and actionable information.
        Use emojis and formatting to make the response engaging and easy to read.
        """
        
        response = self._call_llm(prompt)
        return response
    
    def _prepare_fraud_context(self, transaction_data: Dict, prediction: int,
                             confidence: float, feature_importance: Dict) -> Dict:
        """Prepare context for fraud explanation"""
        return {
            "transaction": transaction_data,
            "verdict": "FRAUD" if prediction == 1 else "LEGITIMATE",
            "confidence_score": round(confidence, 3),
            "top_risk_factors": feature_importance,
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_fraud_patterns(self, fraud_cases: pd.DataFrame) -> Dict:
        """Extract key patterns from fraud cases"""
        patterns = {}
        
        if 'amount' in fraud_cases.columns or 'Amount' in fraud_cases.columns:
            amount_col = 'amount' if 'amount' in fraud_cases.columns else 'Amount'
            patterns['amount_patterns'] = {
                'avg_fraud_amount': fraud_cases[amount_col].mean(),
                'median_fraud_amount': fraud_cases[amount_col].median(),
                'amount_range': [fraud_cases[amount_col].min(), fraud_cases[amount_col].max()]
            }
        
        if 'hour' in fraud_cases.columns:
            patterns['time_patterns'] = {
                'peak_fraud_hours': fraud_cases['hour'].value_counts().head(5).to_dict(),
                'fraud_by_hour_distribution': fraud_cases['hour'].value_counts().sort_index().to_dict()
            }
        
        patterns['total_fraud_cases'] = len(fraud_cases)
        patterns['fraud_rate'] = len(fraud_cases) / len(fraud_cases) if len(fraud_cases) > 0 else 0
        
        return patterns
    
    def _prepare_data_summary(self, data: pd.DataFrame) -> Dict:
        """Prepare data summary for LLM analysis"""
        summary = {
            'total_transactions': len(data),
            'columns': list(data.columns),
            'date_range': {
                'start': data.index.min() if hasattr(data.index, 'min') else 'N/A',
                'end': data.index.max() if hasattr(data.index, 'max') else 'N/A'
            }
        }
        
        # Add fraud statistics if fraud column exists
        fraud_cols = [col for col in data.columns if 'fraud' in col.lower() or 'class' in col.lower()]
        if fraud_cols:
            fraud_col = fraud_cols[0]
            summary['fraud_statistics'] = {
                'total_fraud': int(data[fraud_col].sum()),
                'fraud_rate': float(data[fraud_col].mean()),
                'legitimate_transactions': int((data[fraud_col] == 0).sum())
            }
        
        return summary
    
    def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Make API call to LLM service
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum response length
        """
        try:
            if self.api_provider == "openai":
                return self._call_openai(prompt, max_tokens)
            elif self.api_provider == "anthropic":
                return self._call_anthropic(prompt, max_tokens)
            elif self.api_provider == "ollama":
                return self._call_ollama(prompt, max_tokens)
            elif self.api_provider == "gemini":
                return self._call_gemini(prompt, max_tokens)
            elif self.api_provider == "huggingface":
                return self._call_huggingface(prompt, max_tokens)
            else:
                return "LLM provider not configured. Please set up API credentials."
                
        except Exception as e:
            return f"LLM analysis unavailable: {str(e)}"
    
    def _call_openai(self, prompt: str, max_tokens: int) -> str:
        """Call OpenAI API"""
        if not self.api_key:
            return "OpenAI API key not provided. Set OPENAI_API_KEY environment variable."
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert fraud analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI API error: {str(e)}"
    
    def _call_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Call Anthropic Claude API"""
        if not self.api_key:
            return "Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable."
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = requests.post(self.endpoint, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["content"][0]["text"]
        except Exception as e:
            return f"Anthropic API error: {str(e)}"
    
    def _call_ollama(self, prompt: str, max_tokens: int) -> str:
        """Call local Ollama API"""
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens}
        }
        
        try:
            response = requests.post(self.endpoint, json=data, timeout=30)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            return f"Ollama API error: {str(e)}. Make sure Ollama is running locally."
    
    def _call_huggingface(self, prompt: str, max_tokens: int) -> str:
        """Call Hugging Face Inference API"""
        if not self.api_key:
            return "Hugging Face API key not provided. Set HUGGINGFACE_API_KEY environment variable."
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}}
        
        try:
            response = requests.post(self.endpoint + self.model, headers=headers, json=data)
            response.raise_for_status()
            return response.json()[0]["generated_text"]
        except Exception as e:
            return f"Hugging Face API error: {str(e)}"
    
    def _call_gemini(self, prompt: str, max_tokens: int) -> str:
        """Call Google Gemini API"""
        if not GEMINI_AVAILABLE:
            return "Gemini not available. Install: pip install google-generativeai"
        
        if not self.api_key:
            return "Gemini API key not provided. Set GEMINI_API_KEY environment variable."
        
        try:
            model = genai.GenerativeModel(self.model)
            
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.3,
            )
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        except Exception as e:
            return f"Gemini API error: {str(e)}"

class LLMEnhancedFraudUI:
    """Enhanced fraud detection UI with LLM capabilities"""
    
    def __init__(self, llm_analyzer: LLMFraudAnalyzer):
        self.llm = llm_analyzer
    
    def get_intelligent_explanation(self, transaction_data: Dict, 
                                  ml_prediction: int, confidence: float,
                                  feature_importance: Dict) -> Dict:
        """Get AI-powered fraud explanation"""
        
        # Get LLM explanation
        explanation = self.llm.explain_fraud_decision(
            transaction_data, ml_prediction, confidence, feature_importance
        )
        
        # Structure the response
        return {
            "ml_prediction": "FRAUD" if ml_prediction == 1 else "LEGITIMATE",
            "confidence": confidence,
            "ai_explanation": explanation,
            "top_features": feature_importance,
            "timestamp": datetime.now().isoformat()
        }
    
    def answer_user_question(self, question: str, data: pd.DataFrame) -> str:
        """Answer user questions about fraud data"""
        return self.llm.natural_language_query(question, data)
    
    def generate_insights_report(self, fraud_data: pd.DataFrame) -> str:
        """Generate intelligent insights report"""
        return self.llm.analyze_fraud_patterns(fraud_data)

# Example usage and integration patterns
def example_integration():
    """Example of how to integrate LLM into existing fraud detection"""
    
    # Initialize LLM (choose your provider)
    llm_analyzer = LLMFraudAnalyzer(
        api_provider="openai",  # or "anthropic", "ollama", "huggingface"
        api_key="your-api-key-here"  # or set environment variable
    )
    
    # Example transaction data
    transaction = {
        "amount": 5000.0,
        "transaction_type": "P2P",
        "hour": 2,  # 2 AM
        "is_weekend": 1,
        "high_amount": 1
    }
    
    # Example ML prediction
    ml_prediction = 1  # Fraud
    confidence = 0.95
    feature_importance = {
        "high_amount": 0.45,
        "hour": 0.30,
        "is_weekend": 0.15,
        "amount": 0.10
    }
    
    # Get intelligent explanation
    explanation = llm_analyzer.explain_fraud_decision(
        transaction, ml_prediction, confidence, feature_importance
    )
    
    print("🤖 AI-Powered Fraud Analysis:")
    print(explanation)
    
    return explanation

if __name__ == "__main__":
    print("🤖 LLM Integration for FraudGuard System")
    print("="*50)
    print("Available integrations:")
    print("1. OpenAI GPT-4 (API key required)")
    print("2. Anthropic Claude (API key required)")
    print("3. Ollama (local deployment)")
    print("4. Hugging Face (API key required)")
    print("\nRun example_integration() to see LLM fraud analysis in action!")
