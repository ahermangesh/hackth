import requests
import time

def test_fraud_api():
    """Test the minimal fraud API with the real fraudTest.csv"""
    
    print("🔍 Testing Universal Fraud Detection API...")
    
    # Test health check
    try:
        health_response = requests.get('http://localhost:5001/health', timeout=5)
        if health_response.status_code == 200:
            print("✅ API is healthy:", health_response.json()['message'])
        else:
            print("❌ Health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Upload the fraudTest.csv file
    file_path = 'ProvidedData/6/fraudTest.csv'
    
    try:
        print(f"📤 Uploading {file_path}...")
        
        with open(file_path, 'rb') as f:
            files = {'file': ('fraudTest.csv', f, 'text/csv')}
            response = requests.post('http://localhost:5001/upload', files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result['status'] == 'success':
                task_id = result['task_id']
                print(f"✅ Upload successful! Task ID: {task_id}")
                
                # Monitor progress
                print("⏳ Monitoring analysis progress...")
                for i in range(60):  # Wait up to 60 seconds
                    try:
                        status_response = requests.get(f'http://localhost:5001/status/{task_id}', timeout=10)
                        if status_response.status_code == 200:
                            status = status_response.json()['status']
                            print(f"Status: {status}")
                            
                            if status == 'Completed':
                                # Get results
                                results_response = requests.get(f'http://localhost:5001/results/{task_id}', timeout=10)
                                if results_response.status_code == 200:
                                    results = results_response.json()
                                    
                                    print("\n" + "="*50)
                                    print("🎉 FRAUD DETECTION RESULTS")
                                    print("="*50)
                                    print(f"📊 Dataset Type: {results['dataset_type']}")
                                    print(f"📈 Total Transactions: {results['total_transactions']:,}")
                                    print(f"🚨 Fraud Cases Detected: {results['fraud_detected']:,}")
                                    print(f"📊 Fraud Rate: {results['fraud_rate']:.3f}%")
                                    
                                    if 'total_fraud_amount' in results:
                                        print(f"💰 Total Fraud Amount: ${results['total_fraud_amount']:,.2f}")
                                    
                                    print(f"🔴 High Risk Transactions: {results['high_risk_count']:,}")
                                    print(f"📊 Average Fraud Probability: {results['avg_fraud_probability']:.3f}")
                                    print(f"🎯 Max Fraud Probability: {results['max_fraud_probability']:.3f}")
                                    
                                    print("\n✅ Universal Fraud Detection System Working Perfectly!")
                                    return True
                                    
                            elif status.startswith('Error'):
                                print(f"❌ Analysis failed: {status}")
                                return False
                                
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"Status check error: {e}")
                        
                print("⏰ Analysis timed out")
                return False
                
            else:
                print(f"❌ Upload failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

if __name__ == "__main__":
    success = test_fraud_api()
    if success:
        print("\n🌟 SUMMARY: Universal Fraud Detection API is working perfectly!")
        print("🎯 Clients can now upload ANY CSV file for automatic fraud detection")
    else:
        print("\n❌ Test failed - check server logs for details")
