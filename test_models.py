import google.generativeai as genai
import os

# Configure with API key from config
import json
try:
    with open('fraudguard_config.json', 'r') as f:
        config = json.load(f)
        api_key = config.get('google_api_key')
        print(f"API key found: {bool(api_key)}")
        
        if api_key:
            genai.configure(api_key=api_key)
            
            # List available models
            print("\n=== Available Models ===")
            try:
                models = genai.list_models()
                for model in models:
                    if 'generateContent' in model.supported_generation_methods:
                        print(f"✓ {model.name}")
            except Exception as e:
                print(f"Error listing models: {e}")
                
            # Test specific models
            test_models = [
                'gemini-1.5-flash-latest',
                'gemini-1.5-flash',
                'gemini-1.5-pro-latest', 
                'gemini-1.5-pro',
                'gemini-pro'
            ]
            
            print("\n=== Testing Models ===")
            for model_name in test_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content("Test: What is 2+2?")
                    if response and response.text:
                        print(f"✓ {model_name} - WORKING")
                    else:
                        print(f"✗ {model_name} - No response")
                except Exception as e:
                    print(f"✗ {model_name} - Error: {e}")
        else:
            print("No API key found in config!")
            
except Exception as e:
    print(f"Error: {e}")
