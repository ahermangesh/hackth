import requests
import pandas as pd
import time

# Create a small test CSV file
test_data = {
    'trans_date_trans_time': ['2024-01-01 10:00:00', '2024-01-01 11:00:00', '2024-01-01 12:00:00'],
    'cc_num': [1234567890123456, 1234567890123457, 1234567890123458],
    'merchant': ['merchant_A', 'fraud_merchant_B', 'merchant_C'],
    'category': ['grocery', 'misc_pos', 'gas_transport'],
    'amt': [25.50, 999.99, 45.00],
    'first': ['John', 'Jane', 'Bob'],
    'last': ['Doe', 'Smith', 'Johnson'],
    'gender': ['M', 'F', 'M'],
    'street': ['123 Main St', '456 Oak Ave', '789 Pine Rd'],
    'city': ['New York', 'Los Angeles', 'Chicago'],
    'state': ['NY', 'CA', 'IL'],
    'zip': [10001, 90210, 60601],
    'lat': [40.7128, 34.0522, 41.8781],
    'long': [-74.0060, -118.2437, -87.6298],
    'city_pop': [8000000, 4000000, 2700000],
    'job': ['Engineer', 'Doctor', 'Teacher'],
    'dob': ['1990-01-01', '1985-05-15', '1975-12-25'],
    'trans_num': ['txn001', 'txn002', 'txn003'],
    'unix_time': [1704110400, 1704114000, 1704117600],
    'merch_lat': [40.7500, 34.0500, 41.8800],
    'merch_long': [-74.0000, -118.2500, -87.6300],
    'is_fraud': [0, 1, 0]  # Jane's transaction is fraud
}

df = pd.DataFrame(test_data)
df.to_csv('test_upload_sample.csv', index=False)
print("✅ Created test CSV file: test_upload_sample.csv")

# Test the upload API
print("🔄 Testing upload API...")

try:
    # Upload the file
    with open('test_upload_sample.csv', 'rb') as f:
        files = {'file': f}
        response = requests.post('http://localhost:5000/upload', files=files)
    
    if response.status_code == 200:
        result = response.json()
        if result['status'] == 'success':
            task_id = result['task_id']
            print(f"✅ Upload successful! Task ID: {task_id}")
            
            # Check status
            for i in range(30):  # Wait up to 30 seconds
                status_response = requests.get(f'http://localhost:5000/status/{task_id}')
                if status_response.status_code == 200:
                    status = status_response.json()['status']
                    print(f"Status: {status}")
                    
                    if status == 'Completed':
                        # Get results
                        results_response = requests.get(f'http://localhost:5000/results/{task_id}')
                        if results_response.status_code == 200:
                            results = results_response.json()
                            print("\n🎉 FRAUD DETECTION RESULTS:")
                            print(f"Dataset Type: {results['dataset_type']}")
                            print(f"Total Transactions: {results['total_transactions']}")
                            print(f"Fraud Detected: {results['fraud_detected']}")
                            print(f"Fraud Rate: {results['fraud_rate']:.2f}%")
                            if 'total_fraud_amount' in results:
                                print(f"Total Fraud Amount: ${results['total_fraud_amount']:.2f}")
                            break
                    elif status.startswith('Error'):
                        print(f"❌ Error: {status}")
                        break
                        
                    time.sleep(1)
        else:
            print(f"❌ Upload failed: {result['message']}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Connection error: {e}")
    print("Make sure the server is running at http://localhost:5000")
