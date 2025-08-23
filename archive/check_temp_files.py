#!/usr/bin/env python3
"""
Debug script to check temp uploaded files
"""

import pandas as pd
import os

def check_temp_files():
    temp_dir = "temp_uploads"
    if not os.path.exists(temp_dir):
        print("No temp_uploads directory found")
        return
    
    files = os.listdir(temp_dir)
    if not files:
        print("No files in temp_uploads")
        return
    
    # Check the most recent file
    latest_file = max(files)
    file_path = os.path.join(temp_dir, latest_file)
    
    print(f"🔍 Analyzing latest file: {latest_file}")
    
    try:
        df = pd.read_csv(file_path)
        print(f"\n📊 Dataset Analysis:")
        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        print(f"\n📋 Column Names:")
        for i, col in enumerate(df.columns):
            print(f"{i+1:2d}. {col}")
        
        print(f"\n📋 Sample Data (first 2 rows):")
        print(df.head(2).to_string())
        
        print(f"\n🎯 Format Detection Test:")
        columns = set(df.columns)
        
        # Test all known formats
        upi_indicators = {'amount (INR)', 'transaction_type', 'payer_vpa'}
        upi_match = len(upi_indicators.intersection(columns))
        print(f"UPI match: {upi_match}/3")
        
        cc_detailed_indicators = {'amt', 'merchant', 'category', 'city'}
        cc_detailed_match = len(cc_detailed_indicators.intersection(columns))
        print(f"Credit Card detailed match: {cc_detailed_match}/4")
        
        v_columns = [col for col in df.columns if col.startswith('V') and col[1:].isdigit()]
        has_amount_time = 'Amount' in columns and 'Time' in columns
        print(f"Credit Card PCA: V columns={len(v_columns)}, Amount+Time={has_amount_time}")
        
        fraudtest_indicators = {'amt', 'zip', 'lat', 'long', 'city_pop', 'unix_time', 'merch_lat', 'merch_long'}
        fraudtest_match = len(fraudtest_indicators.intersection(columns))
        print(f"FraudTest match: {fraudtest_match}/8")
        
        # Check if any format is detected
        format_detected = (
            upi_match >= 2 or 
            cc_detailed_match >= 3 or 
            (len(v_columns) > 15 and has_amount_time) or 
            fraudtest_match >= 6
        )
        
        print(f"\n🎯 Should trigger mapping interface: {not format_detected}")
        
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    check_temp_files()
