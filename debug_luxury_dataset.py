#!/usr/bin/env python3
"""
Debug script to analyze the luxury dataset structure
"""

import pandas as pd
import os

def analyze_luxury_dataset():
    # Look for the luxury dataset file
    possible_paths = [
        "luxury_cosmetics_analysis_2025.csv",
        "temp_uploads/luxury_cosmetics_analysis_2025.csv"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found file: {path}")
            try:
                df = pd.read_csv(path)
                print(f"\n📊 Dataset Analysis:")
                print(f"Rows: {len(df)}")
                print(f"Columns: {len(df.columns)}")
                print(f"\n📋 Column Names:")
                for i, col in enumerate(df.columns):
                    print(f"{i+1:2d}. {col}")
                
                print(f"\n🔢 Numeric Columns:")
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                for col in numeric_cols:
                    print(f"  - {col}")
                
                print(f"\n📝 Text Columns:")
                text_cols = df.select_dtypes(include=['object']).columns.tolist()
                for col in text_cols:
                    print(f"  - {col}")
                
                print(f"\n📋 Sample Data (first 3 rows):")
                print(df.head(3).to_string())
                
                print(f"\n🎯 Auto-Detection Test:")
                # Test known format detection
                columns = set(df.columns)
                
                # UPI format detection
                upi_indicators = {'amount (INR)', 'transaction_type', 'payer_vpa'}
                upi_match = len(upi_indicators.intersection(columns))
                print(f"UPI indicators found: {upi_match}/3 - {upi_indicators.intersection(columns)}")
                
                # Credit card detailed format
                cc_detailed_indicators = {'amt', 'merchant', 'category', 'city'}
                cc_detailed_match = len(cc_detailed_indicators.intersection(columns))
                print(f"Credit Card detailed indicators found: {cc_detailed_match}/4 - {cc_detailed_indicators.intersection(columns)}")
                
                # Credit card PCA format
                v_columns = [col for col in df.columns if col.startswith('V') and col[1:].isdigit()]
                pca_indicators = len(v_columns) > 15 and 'Amount' in columns and 'Time' in columns
                print(f"Credit Card PCA indicators: V columns={len(v_columns)}, Amount={'Amount' in columns}, Time={'Time' in columns}")
                
                # FraudTest format
                fraudtest_indicators = {'amt', 'zip', 'lat', 'long', 'city_pop', 'unix_time', 'merch_lat', 'merch_long'}
                fraudtest_match = len(fraudtest_indicators.intersection(columns))
                print(f"FraudTest indicators found: {fraudtest_match}/8 - {fraudtest_indicators.intersection(columns)}")
                
                print(f"\n🎯 Conclusion: This should trigger mapping interface!")
                
                return True
                
            except Exception as e:
                print(f"Error reading file: {e}")
                return False
    
    # Check temp_uploads directory
    temp_dir = "temp_uploads"
    if os.path.exists(temp_dir):
        print(f"\n📁 Files in {temp_dir}:")
        for file in os.listdir(temp_dir):
            print(f"  - {file}")
    
    print("❌ Luxury dataset file not found in expected locations")
    return False

if __name__ == "__main__":
    analyze_luxury_dataset()
