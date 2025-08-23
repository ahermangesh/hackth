#!/usr/bin/env python3
"""
Test real fraud data upload using the enterprise API
"""

import requests
import json
import time
import os

def test_real_csv_upload():
    """Test uploading the real fraudTest.csv file"""
    
    # Path to the real fraud data
    csv_file_path = r"C:\Users\KIIT0001\cursor projects\hackth\ProvidedData\6\fraudTest.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return
    
    file_size = os.path.getsize(csv_file_path) / (1024 * 1024)  # MB
    print(f"📁 File size: {file_size:.2f} MB")
    
    # Enterprise upload endpoint
    upload_url = "http://localhost:5000/api/enterprise-multi/upload"
    
    # Customer details for testing
    customer_data = {
        'customer_id': 'test_customer_001',
        'company_name': 'Real Data Test Corp',
        'email': 'test@realdata.com'
    }
    
    print("🚀 Testing real fraud data upload...")
    print(f"📂 Uploading: {csv_file_path}")
    
    try:
        # Upload the file
        with open(csv_file_path, 'rb') as f:
            files = {'file': ('fraudTest.csv', f, 'text/csv')}
            data = customer_data
            
            print("⏳ Uploading file...")
            response = requests.post(upload_url, files=files, data=data, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"📊 Processing job ID: {result.get('job_id')}")
            
            # Monitor progress
            job_id = result.get('job_id')
            if job_id:
                monitor_progress(job_id)
                
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during upload: {e}")

def monitor_progress(job_id):
    """Monitor the processing progress"""
    progress_url = f"http://localhost:5000/api/enterprise-multi/progress/{job_id}"
    
    print(f"\n⏳ Monitoring progress for job: {job_id}")
    
    while True:
        try:
            response = requests.get(progress_url)
            if response.status_code == 200:
                progress = response.json()
                status = progress.get('status')
                processed = progress.get('processed', 0)
                total = progress.get('total', 0)
                
                if total > 0:
                    percent = (processed / total) * 100
                    print(f"📈 Progress: {processed}/{total} ({percent:.1f}%) - Status: {status}")
                else:
                    print(f"📈 Status: {status}")
                
                if status == 'completed':
                    print("✅ Processing completed!")
                    get_results(job_id)
                    break
                elif status == 'failed':
                    print("❌ Processing failed!")
                    break
                    
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error monitoring progress: {e}")
            break

def get_results(job_id):
    """Get the fraud detection results"""
    results_url = f"http://localhost:5000/api/enterprise-multi/results/{job_id}"
    
    try:
        response = requests.get(results_url)
        if response.status_code == 200:
            results = response.json()
            
            print("\n🎯 FRAUD DETECTION RESULTS")
            print("=" * 50)
            
            # Summary statistics
            summary = results.get('summary', {})
            print(f"📊 Total transactions analyzed: {summary.get('total_transactions', 0)}")
            print(f"🚨 Fraud cases detected: {summary.get('fraud_count', 0)}")
            print(f"✅ Legitimate transactions: {summary.get('legitimate_count', 0)}")
            print(f"📈 Fraud rate: {summary.get('fraud_percentage', 0):.2f}%")
            
            # Risk breakdown
            risk_breakdown = summary.get('risk_breakdown', {})
            if risk_breakdown:
                print(f"\n🎯 Risk Level Breakdown:")
                for risk_level, count in risk_breakdown.items():
                    print(f"   {risk_level}: {count} transactions")
            
            # High-risk transactions
            fraud_transactions = results.get('fraud_transactions', [])
            if fraud_transactions:
                print(f"\n🚨 High-Risk Transactions (showing first 10):")
                for i, txn in enumerate(fraud_transactions[:10]):
                    print(f"   {i+1}. Amount: ${txn.get('amount', 'N/A')} | "
                          f"Risk: {txn.get('risk_score', 'N/A')} | "
                          f"Reasons: {', '.join(txn.get('fraud_reasons', []))}")
            
            # Dataset type detected
            dataset_type = results.get('dataset_type', 'Unknown')
            print(f"\n🔍 Dataset type detected: {dataset_type}")
            
            # Processing time
            processing_time = summary.get('processing_time_seconds', 0)
            print(f"⏱️ Processing time: {processing_time:.2f} seconds")
            
        else:
            print(f"❌ Failed to get results: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting results: {e}")

if __name__ == "__main__":
    print("🧪 Real Fraud Data Testing")
    print("=" * 40)
    test_real_csv_upload()
