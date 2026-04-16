import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.secret_key = os.urandom(24)
csrf = CSRFProtect(app)

# Configuration
app.config['WTF_CSRF_ENABLED'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = False

# Initialize Firebase
try:
    if not firebase_admin._apps:
        cred_path = 'serviceAccountKey.json'
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized with serviceAccountKey.json")
        else:
            # Fallback for production/GCP environments
            firebase_admin.initialize_app()
            print("Firebase initialized with default credentials")
    db = firestore.client()
except Exception as e:
    print(f"Warning: Firebase initialization failed. Error: {e}")
    db = None

# Mock user database for admin login (to be moved to Firebase later)
users = {
    "admin": {
        "password": generate_password_hash("admin123"),
        "email": "admin@example.com",
    }
}

@app.after_request
def add_csrf_token(response):
    csrf_token = generate_csrf()
    response.set_cookie('csrf_token', csrf_token)
    return response

# --- Authentication Routes ---

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
         # Handle JSON or Form Data
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')

        user = users.get(username)

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session.permanent = True
            
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'redirect': url_for('dashboard')})

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Invalid username or password'}), 401

        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400

        if username in users:
            return jsonify({'error': 'Username already exists'}), 400

        users[username] = {
            'password': generate_password_hash(password),
            'email': email
        }

        return jsonify({
            'success': True,
            'message': 'Registration successful. Please login.',
            'redirect': url_for('login')
        })

    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

# --- Rental/Tenant System Routes ---

@app.route('/properties')
def properties():
    if 'username' not in session: return redirect(url_for('login'))
    
    properties_list = []
    if db is not None:
        try:
            docs = db.collection('properties').stream()
            for doc in docs:
                p_data = doc.to_dict()
                p_data['id'] = doc.id
                properties_list.append(p_data)
        except Exception as e:
            print(f"Error fetching properties: {e}")
            flash('Failed to fetch properties from database.', 'error')

    return render_template('properties.html', properties=properties_list)

@app.route('/api/properties', methods=['POST'])
def add_property():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['address', 'flat_number', 'type', 'rent_amount', 'deposit_amount', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        doc_ref = db.collection('properties').document()
        doc_ref.set({
            'address': data['address'],
            'flat_number': data['flat_number'],
            'type': data['type'],
            'rent_amount': float(data['rent_amount']),
            'deposit_amount': float(data['deposit_amount']),
            'status': data['status'],
            'created_at': datetime.now().isoformat(),
            'owner': session['username']
        })

        return jsonify({'success': True, 'message': 'Property added successfully!', 'id': doc_ref.id})
    except Exception as e:
        print(f"Error adding property: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/properties/<property_id>', methods=['DELETE'])
def delete_property(property_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        db.collection('properties').document(property_id).delete()
        return jsonify({'success': True, 'message': 'Property deleted successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tenants')
def tenants():
    if 'username' not in session: return redirect(url_for('login'))
    
    tenants_list = []
    if db is not None:
        try:
            docs = db.collection('tenants').stream()
            for doc in docs:
                t_data = doc.to_dict()
                t_data['id'] = doc.id
                tenants_list.append(t_data)
        except Exception as e:
            print(f"Error fetching tenants: {e}")
            flash('Failed to fetch tenants from database.', 'error')

    return render_template('tenants.html', tenants=tenants_list)

@app.route('/api/tenants', methods=['POST'])
def add_tenant():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['name', 'phone', 'email', 'id_proof']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        doc_ref = db.collection('tenants').document()
        doc_ref.set({
            'name': data['name'],
            'phone': data['phone'],
            'email': data['email'],
            'id_proof': data['id_proof'],
            'occupation': data.get('occupation', ''),
            'family_members': data.get('family_members', 0),
            'emergency_contact': data.get('emergency_contact', ''),
            'created_at': datetime.now().isoformat(),
            'added_by': session['username']
        })

        return jsonify({'success': True, 'message': 'Tenant added successfully!', 'id': doc_ref.id})
    except Exception as e:
        print(f"Error adding tenant: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tenants/<tenant_id>', methods=['DELETE'])
def delete_tenant(tenant_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        db.collection('tenants').document(tenant_id).delete()
        return jsonify({'success': True, 'message': 'Tenant deleted successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/agreements')
def agreements():
    if 'username' not in session: return redirect(url_for('login'))

    agreements_list = []
    properties_list = []
    tenants_list = []
    today = datetime.now().date()

    if db is not None:
        try:
            # Fetch agreements with days_remaining calculated
            for doc in db.collection('agreements').stream():
                a_data = doc.to_dict()
                a_data['id'] = doc.id
                end_str = a_data.get('end_date', '')
                if end_str:
                    try:
                        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
                        a_data['days_remaining'] = (end_date - today).days
                    except Exception:
                        a_data['days_remaining'] = None
                else:
                    a_data['days_remaining'] = None
                agreements_list.append(a_data)
            # Fetch properties for dropdown
            for doc in db.collection('properties').where('status', '==', 'Vacant').stream():
                p_data = doc.to_dict()
                properties_list.append({'id': doc.id, 'label': f"{p_data.get('flat_number')} - {p_data.get('address')}"})
            # Fetch tenants for dropdown
            for doc in db.collection('tenants').stream():
                t_data = doc.to_dict()
                tenants_list.append({'id': doc.id, 'name': t_data.get('name')})
        except Exception as e:
            print(f"Error fetching data for agreements: {e}")

    return render_template('agreements.html', agreements=agreements_list, properties=properties_list, tenants=tenants_list)

@app.route('/api/agreements', methods=['POST'])
def add_agreement():
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    if db is None: return jsonify({'error': 'Database absent'}), 500

    try:
        data = request.json
        required = ['tenant_id', 'tenant_name', 'property_id', 'property_label', 'start_date', 'end_date', 'rent_amount']
        for field in required:
            if field not in data: return jsonify({'error': f"Missing {field}"}), 400

        doc_ref = db.collection('agreements').document()
        doc_ref.set({
            'tenant_id': data['tenant_id'],
            'tenant_name': data['tenant_name'],
            'property_id': data['property_id'],
            'property_label': data['property_label'],
            'start_date': data['start_date'],
            'end_date': data['end_date'],
            'rent_amount': float(data['rent_amount']),
            'status': 'Active',
            'created_at': datetime.now().isoformat()
        })
        
        # Mark property as occupied
        db.collection('properties').document(data['property_id']).update({'status': 'Occupied'})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agreements/<aid>', methods=['DELETE'])
def end_agreement(aid):
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    try:
        # Mark as inactive and optionally free up property
        ag_ref = db.collection('agreements').document(aid)
        ag_doc = ag_ref.get()
        if ag_doc.exists:
            prop_id = ag_doc.to_dict().get('property_id')
            ag_ref.update({'status': 'Terminated'})
            db.collection('properties').document(prop_id).update({'status': 'Vacant'})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/payments')
def payments():
    if 'username' not in session: return redirect(url_for('login'))
    
    payments_list = []
    agreements_list = []
    if db is not None:
        try:
            for doc in db.collection('payments').order_by('payment_date', direction=firestore.Query.DESCENDING).stream():
                p_data = doc.to_dict()
                p_data['id'] = doc.id
                payments_list.append(p_data)
                
            for doc in db.collection('agreements').where('status', '==', 'Active').stream():
                a_data = doc.to_dict()
                agreements_list.append({
                    'id': doc.id, 
                    'label': f"{a_data.get('tenant_name')} ({a_data.get('property_label')})",
                    'rent': a_data.get('rent_amount')
                })
        except Exception as e:
            print(f"Error fetching payments: {e}")

    return render_template('payments.html', payments=payments_list, agreements=agreements_list)

@app.route('/api/payments', methods=['POST'])
def add_payment():
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    try:
        data = request.json
        doc_ref = db.collection('payments').document()
        doc_ref.set({
            'agreement_id': data['agreement_id'],
            'agreement_label': data['agreement_label'],
            'amount': float(data['amount']),
            'month': data['month'],
            'payment_date': datetime.now().isoformat(),
            'mode': data['mode'],
            'recorded_by': session['username']
        })
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- Dashboard Stats ---

@app.route('/api/dashboard/stats')
def dashboard_stats():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    stats = {
        'total_properties': 0, 'occupied': 0, 'vacant': 0,
        'total_tenants': 0, 'active_agreements': 0,
        'expiring_soon': 0, 'total_income': 0, 'open_complaints': 0
    }

    if db is not None:
        try:
            for doc in db.collection('properties').stream():
                d = doc.to_dict()
                stats['total_properties'] += 1
                if d.get('status') == 'Occupied':
                    stats['occupied'] += 1
                else:
                    stats['vacant'] += 1

            stats['total_tenants'] = len(list(db.collection('tenants').stream()))

            today = datetime.now().date()
            for doc in db.collection('agreements').where('status', '==', 'Active').stream():
                d = doc.to_dict()
                stats['active_agreements'] += 1
                end_str = d.get('end_date', '')
                if end_str:
                    try:
                        days_left = (datetime.strptime(end_str, '%Y-%m-%d').date() - today).days
                        if 0 <= days_left <= 30:
                            stats['expiring_soon'] += 1
                    except Exception:
                        pass

            for doc in db.collection('payments').stream():
                stats['total_income'] += doc.to_dict().get('amount', 0)

            try:
                for doc in db.collection('complaints').where('status', '==', 'Open').stream():
                    stats['open_complaints'] += 1
            except Exception:
                pass
        except Exception as e:
            print(f"Stats error: {e}")

    return jsonify(stats)

# --- Payment Receipt ---

@app.route('/api/payments/<payment_id>/receipt')
def payment_receipt(payment_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    if db is None:
        return "Database unavailable", 500
    try:
        doc = db.collection('payments').document(payment_id).get()
        if not doc.exists:
            return "Payment not found", 404
        payment = doc.to_dict()
        payment['id'] = payment_id
        return render_template('receipt.html', payment=payment)
    except Exception as e:
        return f"Error: {e}", 500

# --- Complaints Module ---

@app.route('/complaints')
def complaints():
    if 'username' not in session:
        return redirect(url_for('login'))
    complaints_list = []
    if db is not None:
        try:
            for doc in db.collection('complaints').order_by('created_at', direction=firestore.Query.DESCENDING).stream():
                c_data = doc.to_dict()
                c_data['id'] = doc.id
                complaints_list.append(c_data)
        except Exception as e:
            print(f"Complaints fetch error: {e}")
    return render_template('complaints.html', complaints=complaints_list)

@app.route('/api/complaints', methods=['POST'])
def add_complaint():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500
    try:
        data = request.json
        if not data or 'description' not in data:
            return jsonify({'error': 'Description is required'}), 400
        doc_ref = db.collection('complaints').document()
        doc_ref.set({
            'tenant_name': data.get('tenant_name', ''),
            'property_ref': data.get('property_ref', ''),
            'category': data.get('category', 'General'),
            'description': data['description'],
            'status': 'Open',
            'created_at': datetime.now().isoformat(),
            'logged_by': session['username']
        })
        return jsonify({'success': True, 'id': doc_ref.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/complaints/<cid>', methods=['PATCH'])
def update_complaint_status(cid):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500
    try:
        data = request.json
        db.collection('complaints').document(cid).update({'status': data.get('status', 'Open')})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print('Starting SmartRentals Management System Server...')
    app.run(debug=True, host='0.0.0.0', port=5000)