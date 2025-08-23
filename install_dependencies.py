#!/usr/bin/env python3
"""
Quick installer for FraudGuard dependencies
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        print(f"📦 Installing {package}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {package} installed successfully")
        else:
            print(f"❌ Failed to install {package}: {result.stderr}")
    except Exception as e:
        print(f"❌ Error installing {package}: {e}")

def main():
    packages = [
        "flask",
        "pandas", 
        "numpy",
        "scikit-learn",
        "python-dotenv",
        "google-generativeai"
    ]
    
    print("🚀 Installing FraudGuard dependencies...")
    print("=" * 50)
    
    for package in packages:
        install_package(package)
    
    print("\n🎉 Installation complete!")
    print("Run: python original_fraud_ui.py")

if __name__ == "__main__":
    main()
