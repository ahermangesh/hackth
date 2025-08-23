#!/usr/bin/env python3
"""
Customer Management and Pricing System
For B2B fraud detection service
"""

from flask import Blueprint, request, jsonify, render_template_string
import uuid
import json
import os
from datetime import datetime, timedelta
import hashlib

customer_bp = Blueprint('customer', __name__)

# Customer database (in production, use proper database)
CUSTOMERS_FILE = 'customers.json'
API_KEYS_FILE = 'api_keys.json'

def load_customers():
    """Load customer data"""
    if os.path.exists(CUSTOMERS_FILE):
        with open(CUSTOMERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_customers(customers):
    """Save customer data"""
    with open(CUSTOMERS_FILE, 'w') as f:
        json.dump(customers, f, indent=2, default=str)

def load_api_keys():
    """Load API keys"""
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_api_keys(api_keys):
    """Save API keys"""
    with open(API_KEYS_FILE, 'w') as f:
        json.dump(api_keys, f, indent=2)

def generate_api_key():
    """Generate secure API key"""
    return f"fg_{uuid.uuid4().hex[:24]}"

def get_plan_limits(plan_type):
    """Get plan limits and pricing"""
    plans = {
        'free': {
            'name': 'Free Trial',
            'monthly_transactions': 1000,
            'price': 0,
            'features': ['Basic fraud detection', 'Email reports', 'Standard support']
        },
        'startup': {
            'name': 'Startup Plan',
            'monthly_transactions': 50000,
            'price': 99,
            'features': ['Advanced ML models', 'API access', 'Priority support', 'Custom rules']
        },
        'business': {
            'name': 'Business Plan', 
            'monthly_transactions': 500000,
            'price': 499,
            'features': ['All features', 'White-label reports', 'Dedicated support', 'SLA guarantee']
        },
        'enterprise': {
            'name': 'Enterprise Plan',
            'monthly_transactions': 10000000,
            'price': 1999,
            'features': ['Custom deployment', 'On-premise option', 'Custom integrations', '24/7 support']
        }
    }
    return plans.get(plan_type, plans['free'])

@customer_bp.route('/signup', methods=['POST'])
def signup():
    """Customer signup endpoint"""
    try:
        data = request.get_json()
        
        required_fields = ['company_name', 'email', 'plan_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        customers = load_customers()
        
        # Check if email already exists
        if data['email'] in customers:
            return jsonify({'error': 'Email already registered'}), 400
        
        # Validate plan type
        plan_info = get_plan_limits(data['plan_type'])
        if not plan_info:
            return jsonify({'error': 'Invalid plan type'}), 400
        
        # Generate customer ID and API key
        customer_id = str(uuid.uuid4())
        api_key = generate_api_key()
        
        # Create customer record
        customer = {
            'customer_id': customer_id,
            'company_name': data['company_name'],
            'email': data['email'],
            'contact_person': data.get('contact_person', ''),
            'phone': data.get('phone', ''),
            'plan_type': data['plan_type'],
            'plan_info': plan_info,
            'api_key': api_key,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'usage': {
                'current_month_transactions': 0,
                'total_transactions': 0,
                'last_reset': datetime.now().isoformat()
            }
        }
        
        # Save customer
        customers[data['email']] = customer
        save_customers(customers)
        
        # Save API key mapping
        api_keys = load_api_keys()
        api_keys[api_key] = {
            'customer_id': customer_id,
            'email': data['email'],
            'created_at': datetime.now().isoformat()
        }
        save_api_keys(api_keys)
        
        return jsonify({
            'success': True,
            'customer_id': customer_id,
            'api_key': api_key,
            'plan_info': plan_info,
            'message': 'Account created successfully!'
        })
        
    except Exception as e:
        return jsonify({'error': f'Signup failed: {str(e)}'}), 500

@customer_bp.route('/validate-key', methods=['POST'])
def validate_api_key():
    """Validate API key and return customer info"""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 400
        
        api_keys = load_api_keys()
        
        if api_key not in api_keys:
            return jsonify({'error': 'Invalid API key'}), 401
        
        key_info = api_keys[api_key]
        customers = load_customers()
        customer = customers.get(key_info['email'])
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        return jsonify({
            'valid': True,
            'customer': {
                'customer_id': customer['customer_id'],
                'company_name': customer['company_name'],
                'plan_type': customer['plan_type'],
                'plan_info': customer['plan_info'],
                'usage': customer['usage']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@customer_bp.route('/usage/<customer_id>', methods=['GET'])
def get_usage(customer_id):
    """Get customer usage statistics"""
    try:
        customers = load_customers()
        
        # Find customer by ID
        customer = None
        for email, cust in customers.items():
            if cust['customer_id'] == customer_id:
                customer = cust
                break
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Check if we need to reset monthly usage
        last_reset = datetime.fromisoformat(customer['usage']['last_reset'])
        now = datetime.now()
        
        if now.month != last_reset.month or now.year != last_reset.year:
            customer['usage']['current_month_transactions'] = 0
            customer['usage']['last_reset'] = now.isoformat()
            save_customers(customers)
        
        return jsonify({
            'customer_id': customer_id,
            'plan_info': customer['plan_info'],
            'usage': customer['usage'],
            'remaining_transactions': max(0, 
                customer['plan_info']['monthly_transactions'] - 
                customer['usage']['current_month_transactions']
            )
        })
        
    except Exception as e:
        return jsonify({'error': f'Usage check failed: {str(e)}'}), 500

@customer_bp.route('/increment-usage', methods=['POST'])
def increment_usage():
    """Increment customer usage (called after processing)"""
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        transaction_count = data.get('transaction_count', 1)
        
        customers = load_customers()
        
        # Find customer by ID
        customer_email = None
        for email, cust in customers.items():
            if cust['customer_id'] == customer_id:
                customer_email = email
                break
        
        if not customer_email:
            return jsonify({'error': 'Customer not found'}), 404
        
        customer = customers[customer_email]
        
        # Update usage
        customer['usage']['current_month_transactions'] += transaction_count
        customer['usage']['total_transactions'] += transaction_count
        
        save_customers(customers)
        
        return jsonify({
            'success': True,
            'new_usage': customer['usage']
        })
        
    except Exception as e:
        return jsonify({'error': f'Usage update failed: {str(e)}'}), 500

@customer_bp.route('/pricing', methods=['GET'])
def pricing_page():
    """Pricing page for customers"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FraudGuard - Pricing</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
            
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 0; text-align: center; }
            .header h1 { font-size: 3em; margin-bottom: 20px; }
            .header p { font-size: 1.2em; opacity: 0.9; }
            
            .pricing-section { padding: 80px 0; background: #f8f9fa; }
            .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; margin-top: 50px; }
            
            .pricing-card { background: white; border-radius: 15px; padding: 40px 30px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.1); transition: transform 0.3s; }
            .pricing-card:hover { transform: translateY(-10px); }
            .pricing-card.featured { border: 3px solid #667eea; position: relative; }
            .pricing-card.featured::before { content: 'MOST POPULAR'; position: absolute; top: -15px; left: 50%; transform: translateX(-50%); background: #667eea; color: white; padding: 8px 20px; border-radius: 25px; font-size: 0.8em; font-weight: bold; }
            
            .plan-name { font-size: 1.5em; font-weight: bold; color: #667eea; margin-bottom: 10px; }
            .plan-price { font-size: 3em; font-weight: bold; color: #333; margin-bottom: 10px; }
            .plan-price span { font-size: 0.4em; color: #666; }
            .plan-desc { color: #666; margin-bottom: 30px; }
            
            .features { list-style: none; margin-bottom: 30px; }
            .features li { padding: 8px 0; }
            .features li::before { content: '✓'; color: #28a745; font-weight: bold; margin-right: 10px; }
            
            .cta-button { background: #667eea; color: white; padding: 15px 30px; border: none; border-radius: 25px; font-size: 1.1em; cursor: pointer; transition: background 0.3s; width: 100%; }
            .cta-button:hover { background: #5a67d8; }
            
            .signup-section { padding: 60px 0; }
            .signup-form { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
            .form-group input, .form-group select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 1em; }
            
            .demo-section { background: #667eea; color: white; padding: 60px 0; text-align: center; }
            .demo-button { background: white; color: #667eea; padding: 15px 30px; border: none; border-radius: 25px; font-size: 1.1em; cursor: pointer; margin: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>🛡️ FraudGuard</h1>
                <p>AI-Powered Fraud Detection for Banks & Fintech Startups</p>
            </div>
        </div>
        
        <div class="pricing-section">
            <div class="container">
                <h2 style="text-align: center; font-size: 2.5em; margin-bottom: 20px;">Choose Your Plan</h2>
                <p style="text-align: center; font-size: 1.2em; color: #666;">Transparent pricing that scales with your business</p>
                
                <div class="pricing-grid">
                    <div class="pricing-card">
                        <div class="plan-name">Free Trial</div>
                        <div class="plan-price">₹0<span>/month</span></div>
                        <div class="plan-desc">Perfect for testing our service</div>
                        <ul class="features">
                            <li>1,000 transactions/month</li>
                            <li>Basic fraud detection</li>
                            <li>Email reports</li>
                            <li>Standard support</li>
                        </ul>
                        <button class="cta-button" onclick="selectPlan('free')">Start Free Trial</button>
                    </div>
                    
                    <div class="pricing-card featured">
                        <div class="plan-name">Startup Plan</div>
                        <div class="plan-price">₹99<span>/month</span></div>
                        <div class="plan-desc">Ideal for growing fintech startups</div>
                        <ul class="features">
                            <li>50,000 transactions/month</li>
                            <li>Advanced ML models</li>
                            <li>API access</li>
                            <li>Custom fraud rules</li>
                            <li>Priority support</li>
                        </ul>
                        <button class="cta-button" onclick="selectPlan('startup')">Choose Startup</button>
                    </div>
                    
                    <div class="pricing-card">
                        <div class="plan-name">Business Plan</div>
                        <div class="plan-price">₹499<span>/month</span></div>
                        <div class="plan-desc">For established businesses</div>
                        <ul class="features">
                            <li>500,000 transactions/month</li>
                            <li>All ML features</li>
                            <li>White-label reports</li>
                            <li>Dedicated support</li>
                            <li>SLA guarantee</li>
                        </ul>
                        <button class="cta-button" onclick="selectPlan('business')">Choose Business</button>
                    </div>
                    
                    <div class="pricing-card">
                        <div class="plan-name">Enterprise</div>
                        <div class="plan-price">₹1,999<span>/month</span></div>
                        <div class="plan-desc">For banks and large institutions</div>
                        <ul class="features">
                            <li>10M+ transactions/month</li>
                            <li>Custom deployment</li>
                            <li>On-premise option</li>
                            <li>Custom integrations</li>
                            <li>24/7 support</li>
                        </ul>
                        <button class="cta-button" onclick="selectPlan('enterprise')">Contact Sales</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="signup-section" id="signup" style="display: none;">
            <div class="container">
                <div class="signup-form">
                    <h2 style="text-align: center; margin-bottom: 30px;">Create Your Account</h2>
                    <form id="signupForm">
                        <div class="form-group">
                            <label>Company Name *</label>
                            <input type="text" id="companyName" required>
                        </div>
                        <div class="form-group">
                            <label>Email Address *</label>
                            <input type="email" id="email" required>
                        </div>
                        <div class="form-group">
                            <label>Contact Person</label>
                            <input type="text" id="contactPerson">
                        </div>
                        <div class="form-group">
                            <label>Phone Number</label>
                            <input type="tel" id="phone">
                        </div>
                        <div class="form-group">
                            <label>Selected Plan</label>
                            <select id="planType" disabled>
                                <option value="free">Free Trial</option>
                                <option value="startup">Startup Plan</option>
                                <option value="business">Business Plan</option>
                                <option value="enterprise">Enterprise Plan</option>
                            </select>
                        </div>
                        <button type="submit" class="cta-button">Create Account</button>
                    </form>
                </div>
            </div>
        </div>
        
        <div class="demo-section">
            <div class="container">
                <h2 style="margin-bottom: 20px;">Ready to See It in Action?</h2>
                <p style="margin-bottom: 30px;">Try our fraud detection system with your own data</p>
                <button class="demo-button" onclick="window.open('/api/enterprise/demo-upload', '_blank')">Try Demo Upload</button>
                <button class="demo-button" onclick="window.open('/api/docs', '_blank')">View API Docs</button>
            </div>
        </div>
        
        <script>
            let selectedPlan = '';
            
            function selectPlan(plan) {
                selectedPlan = plan;
                document.getElementById('planType').value = plan;
                document.getElementById('signup').style.display = 'block';
                document.getElementById('signup').scrollIntoView({behavior: 'smooth'});
            }
            
            document.getElementById('signupForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = {
                    company_name: document.getElementById('companyName').value,
                    email: document.getElementById('email').value,
                    contact_person: document.getElementById('contactPerson').value,
                    phone: document.getElementById('phone').value,
                    plan_type: selectedPlan
                };
                
                fetch('/api/customer/signup', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(`Account created successfully!\\n\\nYour API Key: ${data.api_key}\\n\\nPlease save this key securely. You'll need it to access our API.`);
                        location.reload();
                    } else {
                        alert('Signup failed: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Signup error: ' + error);
                });
            });
        </script>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(customer_bp, url_prefix='/api/customer')
    app.run(debug=True, port=5002)
