#!/bin/bash

echo "🧪 Testing Fraud Detection System..."
echo "================================="

# Test 1: API Health Check
echo "1. Testing API Health..."
curl -s http://localhost:5000/health
echo -e "\n"

# Test 2: Generate Sample Data
echo "2. Generating Sample Transactions..."
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"count": 5}' \
  http://localhost:5000/api/transactions/sample
echo -e "\n"

# Test 3: Create Suspicious Transaction
echo "3. Creating Suspicious Transaction..."
curl -s -X POST -H "Content-Type: application/json" \
  -d '{
    "amount": 9999,
    "user_id": "test_user_suspicious",
    "merchant_id": "test_merchant_123",
    "transaction_type": "credit_card"
  }' \
  http://localhost:5000/api/transactions/
echo -e "\n"

# Test 4: Create Normal Transaction
echo "4. Creating Normal Transaction..."
curl -s -X POST -H "Content-Type: application/json" \
  -d '{
    "amount": 25.50,
    "user_id": "test_user_normal",
    "merchant_id": "test_merchant_456",
    "transaction_type": "upi"
  }' \
  http://localhost:5000/api/transactions/
echo -e "\n"

# Test 5: View Dashboard Stats
echo "5. Dashboard Statistics..."
curl -s http://localhost:5000/api/dashboard/stats
echo -e "\n"

# Test 6: ML Model Status
echo "6. ML Model Status..."
curl -s http://localhost:5000/api/ml/status
echo -e "\n"

# Test 7: Direct ML Prediction
echo "7. Testing ML Prediction..."
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"amount": 5000, "user_id": "test_user"}' \
  http://localhost:5000/api/ml/predict
echo -e "\n"

echo "✅ All tests completed!"
echo "🚀 Your fraud detection system is ready for demo!"
