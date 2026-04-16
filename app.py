import os
from io import BytesIO
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, send_file
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.secret_key = os.environ.get('SECRET_KEY', 'smartrentals-dev-secret-change-in-production')
csrf = CSRFProtect(app)

app.config['WTF_CSRF_ENABLED'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = False

# ── Firebase ──────────────────────────────────────────────────────────────────
try:
    if not firebase_admin._apps:
        cred_path = 'serviceAccountKey.json'
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized with serviceAccountKey.json")
        else:
            firebase_admin.initialize_app()
            print("Firebase initialized with default credentials")
    db = firestore.client()
except Exception as e:
    print(f"Warning: Firebase initialization failed. Error: {e}")
    db = None

# ── Admin credentials (in-memory; move to Firebase for production) ────────────
users = {
    "admin": {
        "password": generate_password_hash("admin123"),
        "email": "admin@example.com",
    }
}

# ── CSRF cookie ───────────────────────────────────────────────────────────────
@app.after_request
def add_csrf_token(response):
    response.set_cookie('csrf_token', generate_csrf())
    return response

# ─────────────────────────────────────────────────────────────────────────────
#  ADMIN AUTH
# ─────────────────────────────────────────────────────────────────────────────

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
        data = request.get_json() if request.is_json else request.form
        username, password = data.get('username'), data.get('password')
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
        username, email, password = data.get('username'), data.get('email'), data.get('password')
        if not username or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400
        if username in users:
            return jsonify({'error': 'Username already exists'}), 400
        users[username] = {'password': generate_password_hash(password), 'email': email}
        return jsonify({'success': True, 'message': 'Registration successful. Please login.',
                        'redirect': url_for('login')})
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

# ─────────────────────────────────────────────────────────────────────────────
#  PROPERTIES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/properties')
def properties():
    if 'username' not in session: return redirect(url_for('login'))
    properties_list = []
    if db is not None:
        try:
            for doc in db.collection('properties').stream():
                p = doc.to_dict(); p['id'] = doc.id
                properties_list.append(p)
        except Exception as e:
            print(f"Error fetching properties: {e}")
            flash('Failed to fetch properties.', 'error')
    return render_template('properties.html', properties=properties_list)

@app.route('/api/properties', methods=['POST'])
def add_property():
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    if db is None: return jsonify({'error': 'Database connection failed'}), 500
    try:
        data = request.json
        if not data: return jsonify({'error': 'No data provided'}), 400
        for f in ['address', 'flat_number', 'type', 'rent_amount', 'deposit_amount', 'status']:
            if f not in data: return jsonify({'error': f'Missing field: {f}'}), 400
        ref = db.collection('properties').document()
        ref.set({'address': data['address'], 'flat_number': data['flat_number'],
                 'type': data['type'], 'rent_amount': float(data['rent_amount']),
                 'deposit_amount': float(data['deposit_amount']), 'status': data['status'],
                 'created_at': datetime.now().isoformat(), 'owner': session['username']})
        return jsonify({'success': True, 'id': ref.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/properties/<property_id>', methods=['DELETE'])
def delete_property(property_id):
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    if db is None: return jsonify({'error': 'Database connection failed'}), 500
    try:
        db.collection('properties').document(property_id).delete()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
#  TENANTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/tenants')
def tenants():
    if 'username' not in session: return redirect(url_for('login'))
    tenants_list = []
    if db is not None:
        try:
            # Build tenant_id → active property label map
            property_map = {}
            for doc in db.collection('agreements').where('status', '==', 'Active').stream():
                a = doc.to_dict()
                property_map[a.get('tenant_id')] = a.get('property_label', '')

            for doc in db.collection('tenants').stream():
                t = doc.to_dict(); t['id'] = doc.id
                t['current_property'] = property_map.get(doc.id, '')
                tenants_list.append(t)
        except Exception as e:
            print(f"Error fetching tenants: {e}")
            flash('Failed to fetch tenants.', 'error')
    return render_template('tenants.html', tenants=tenants_list)

@app.route('/api/tenants', methods=['POST'])
def add_tenant():
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    if db is None: return jsonify({'error': 'Database connection failed'}), 500
    try:
        data = request.json
        if not data: return jsonify({'error': 'No data provided'}), 400
        for f in ['name', 'phone', 'email', 'id_proof']:
            if f not in data: return jsonify({'error': f'Missing field: {f}'}), 400

        portal_password = data.get('portal_password', '')
        ref = db.collection('tenants').document()
        ref.set({
            'name': data['name'], 'phone': data['phone'],
            'email': data['email'], 'id_proof': data['id_proof'],
            'occupation': data.get('occupation', ''),
            'family_members': int(data.get('family_members', 0)),
            'emergency_contact': data.get('emergency_contact', ''),
            'portal_password_hash': generate_password_hash(portal_password) if portal_password else '',
            'created_at': datetime.now().isoformat(), 'added_by': session['username']
        })
        return jsonify({'success': True, 'id': ref.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tenants/<tenant_id>', methods=['DELETE'])
def delete_tenant(tenant_id):
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    if db is None: return jsonify({'error': 'Database connection failed'}), 500
    try:
        db.collection('tenants').document(tenant_id).delete()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
#  AGREEMENTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/agreements')
def agreements():
    if 'username' not in session: return redirect(url_for('login'))
    agreements_list, properties_list, tenants_list = [], [], []
    today = datetime.now().date()
    if db is not None:
        try:
            for doc in db.collection('agreements').stream():
                a = doc.to_dict(); a['id'] = doc.id
                end_str = a.get('end_date', '')
                if end_str:
                    try:
                        a['days_remaining'] = (datetime.strptime(end_str, '%Y-%m-%d').date() - today).days
                    except Exception:
                        a['days_remaining'] = None
                else:
                    a['days_remaining'] = None
                agreements_list.append(a)
            for doc in db.collection('properties').where('status', '==', 'Vacant').stream():
                p = doc.to_dict()
                properties_list.append({'id': doc.id, 'label': f"{p.get('flat_number')} - {p.get('address')}"})
            for doc in db.collection('tenants').stream():
                t = doc.to_dict()
                tenants_list.append({'id': doc.id, 'name': t.get('name')})
        except Exception as e:
            print(f"Error fetching agreements: {e}")
    return render_template('agreements.html', agreements=agreements_list,
                           properties=properties_list, tenants=tenants_list)

@app.route('/api/agreements', methods=['POST'])
def add_agreement():
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    if db is None: return jsonify({'error': 'Database absent'}), 500
    try:
        data = request.json
        for f in ['tenant_id', 'tenant_name', 'property_id', 'property_label', 'start_date', 'end_date', 'rent_amount']:
            if f not in data: return jsonify({'error': f'Missing {f}'}), 400
        ref = db.collection('agreements').document()
        ref.set({
            'tenant_id': data['tenant_id'], 'tenant_name': data['tenant_name'],
            'property_id': data['property_id'], 'property_label': data['property_label'],
            'start_date': data['start_date'], 'end_date': data['end_date'],
            'rent_amount': float(data['rent_amount']),
            'due_day': int(data.get('due_day', 5)),
            'late_fee_amount': float(data.get('late_fee_amount', 0)),
            'status': 'Active', 'created_at': datetime.now().isoformat()
        })
        db.collection('properties').document(data['property_id']).update({'status': 'Occupied'})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agreements/<aid>', methods=['DELETE'])
def end_agreement(aid):
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    try:
        ag_ref = db.collection('agreements').document(aid)
        ag_doc = ag_ref.get()
        if ag_doc.exists:
            prop_id = ag_doc.to_dict().get('property_id')
            ag_ref.update({'status': 'Terminated'})
            db.collection('properties').document(prop_id).update({'status': 'Vacant'})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
#  PAYMENTS  (with late-fee calculation)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/payments')
def payments():
    if 'username' not in session: return redirect(url_for('login'))
    payments_list, agreements_list = [], []
    if db is not None:
        try:
            for doc in db.collection('payments').order_by('payment_date',
                        direction=firestore.Query.DESCENDING).stream():
                p = doc.to_dict(); p['id'] = doc.id
                payments_list.append(p)
            for doc in db.collection('agreements').where('status', '==', 'Active').stream():
                a = doc.to_dict()
                agreements_list.append({
                    'id': doc.id,
                    'label': f"{a.get('tenant_name')} ({a.get('property_label')})",
                    'rent': a.get('rent_amount'),
                    'due_day': a.get('due_day', 5),
                    'late_fee_amount': a.get('late_fee_amount', 0)
                })
        except Exception as e:
            print(f"Error fetching payments: {e}")
    return render_template('payments.html', payments=payments_list, agreements=agreements_list)

@app.route('/api/payments', methods=['POST'])
def add_payment():
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    if db is None: return jsonify({'error': 'Database not connected'}), 500
    try:
        data = request.json
        payment_date = datetime.now()

        # ── Late fee calculation ──────────────────────────────────────────────
        is_late = False
        late_fee = 0.0
        due_date_str = ''
        month_str = data.get('month', '')          # e.g. "2025-04"
        ag_id = data.get('agreement_id', '')
        if ag_id and month_str and db:
            try:
                ag_doc = db.collection('agreements').document(ag_id).get()
                if ag_doc.exists:
                    ag = ag_doc.to_dict()
                    due_day = int(ag.get('due_day', 5))
                    late_fee_cfg = float(ag.get('late_fee_amount', 0))
                    year, month = int(month_str[:4]), int(month_str[5:7])
                    due_date = datetime(year, month, min(due_day, 28)).date()
                    due_date_str = due_date.isoformat()
                    if payment_date.date() > due_date:
                        is_late = True
                        late_fee = late_fee_cfg
            except Exception as e:
                print(f"Late fee calc error: {e}")

        ref = db.collection('payments').document()
        ref.set({
            'agreement_id': data['agreement_id'],
            'agreement_label': data['agreement_label'],
            'amount': float(data['amount']),
            'month': data['month'],
            'payment_date': payment_date.isoformat(),
            'mode': data['mode'],
            'is_late': is_late,
            'late_fee': late_fee,
            'due_date': due_date_str,
            'recorded_by': session['username']
        })
        return jsonify({'success': True, 'is_late': is_late, 'late_fee': late_fee})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
#  RECEIPTS  (HTML + PDF)
# ─────────────────────────────────────────────────────────────────────────────

def _get_payment_or_404(payment_id):
    if db is None: return None
    doc = db.collection('payments').document(payment_id).get()
    if not doc.exists: return None
    p = doc.to_dict(); p['id'] = payment_id
    return p

@app.route('/api/payments/<payment_id>/receipt')
def payment_receipt(payment_id):
    if 'username' not in session and 'tenant_id' not in session:
        return redirect(url_for('login'))
    p = _get_payment_or_404(payment_id)
    if p is None: return "Payment not found", 404
    return render_template('receipt.html', payment=p)

@app.route('/api/payments/<payment_id>/receipt/pdf')
def payment_receipt_pdf(payment_id):
    if 'username' not in session and 'tenant_id' not in session:
        return redirect(url_for('login'))
    if not FPDF_AVAILABLE:
        return "PDF generation not available — install fpdf2.", 501
    p = _get_payment_or_404(payment_id)
    if p is None: return "Payment not found", 404
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(20, 20, 20)

        # Header
        pdf.set_fill_color(15, 12, 41)
        pdf.rect(0, 0, 210, 40, 'F')
        pdf.set_font('Helvetica', 'B', 22)
        pdf.set_text_color(255, 95, 56)
        pdf.set_xy(0, 10)
        pdf.cell(210, 10, 'SmartRentals', align='C')
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(200, 200, 200)
        pdf.set_xy(0, 22)
        pdf.cell(210, 8, 'Rent Payment Receipt', align='C')

        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(20, 50)

        # Receipt ID
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 7, f"Receipt ID: SR-{payment_id[:12].upper()}", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(3)

        # Amount highlight
        pdf.set_fill_color(243, 244, 255)
        pdf.set_draw_color(220, 220, 240)
        y = pdf.get_y()
        pdf.rect(20, y, 170, 28, 'FD')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 100, 120)
        pdf.set_xy(20, y + 4)
        pdf.cell(170, 8, 'AMOUNT PAID', align='C')
        pdf.set_font('Helvetica', 'B', 22)
        pdf.set_text_color(255, 95, 56)
        pdf.set_xy(20, y + 12)
        pdf.cell(170, 14, f"Rs. {int(p.get('amount', 0))}", align='C')
        pdf.ln(36)

        # Details table
        def row(label, value, bold_val=False):
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(110, 110, 130)
            pdf.cell(55, 9, label)
            if bold_val:
                pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(30, 30, 50)
            pdf.cell(0, 9, str(value), new_x='LMARGIN', new_y='NEXT')

        row('Tenant & Property', p.get('agreement_label', '—'))
        row('For Month', p.get('month', '—'))
        row('Payment Mode', p.get('mode', '—'))
        row('Payment Date', p.get('payment_date', '')[:10])
        if p.get('due_date'):
            row('Due Date', p.get('due_date', ''))
        if p.get('is_late'):
            row('Status', 'LATE PAYMENT', bold_val=True)
            pdf.set_text_color(220, 50, 50)
            row('Late Fee', f"Rs. {int(p.get('late_fee', 0))}", bold_val=True)
            pdf.set_text_color(30, 30, 50)
            row('Total Charged', f"Rs. {int(p.get('amount', 0) + p.get('late_fee', 0))}", bold_val=True)
        row('Recorded By', p.get('recorded_by', '—'))

        # Footer
        pdf.set_y(-25)
        pdf.set_draw_color(220, 220, 220)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_text_color(180, 180, 180)
        pdf.cell(0, 10, 'Computer-generated receipt — no signature required. SmartRentals.', align='C')

        buf = BytesIO()
        pdf.output(buf)
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf', as_attachment=True,
                         download_name=f'SmartRentals_Receipt_{payment_id[:8]}.pdf')
    except Exception as e:
        return f"PDF generation failed: {e}", 500

# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD STATS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/dashboard/stats')
def dashboard_stats():
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    stats = {'total_properties': 0, 'occupied': 0, 'vacant': 0, 'total_tenants': 0,
             'active_agreements': 0, 'expiring_soon': 0, 'total_income': 0, 'open_complaints': 0}
    if db is not None:
        try:
            for doc in db.collection('properties').stream():
                d = doc.to_dict(); stats['total_properties'] += 1
                if d.get('status') == 'Occupied': stats['occupied'] += 1
                else: stats['vacant'] += 1
            stats['total_tenants'] = len(list(db.collection('tenants').stream()))
            today = datetime.now().date()
            for doc in db.collection('agreements').where('status', '==', 'Active').stream():
                d = doc.to_dict(); stats['active_agreements'] += 1
                end_str = d.get('end_date', '')
                if end_str:
                    try:
                        days_left = (datetime.strptime(end_str, '%Y-%m-%d').date() - today).days
                        if 0 <= days_left <= 30: stats['expiring_soon'] += 1
                    except Exception: pass
            for doc in db.collection('payments').stream():
                stats['total_income'] += doc.to_dict().get('amount', 0)
            try:
                for doc in db.collection('complaints').where('status', '==', 'Open').stream():
                    stats['open_complaints'] += 1
            except Exception: pass
        except Exception as e:
            print(f"Stats error: {e}")
    return jsonify(stats)

# ─────────────────────────────────────────────────────────────────────────────
#  COMPLAINTS  (Admin — with staff assignment)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/complaints')
def complaints():
    if 'username' not in session: return redirect(url_for('login'))
    complaints_list, staff_list = [], []
    if db is not None:
        try:
            for doc in db.collection('complaints').order_by('created_at',
                        direction=firestore.Query.DESCENDING).stream():
                c = doc.to_dict(); c['id'] = doc.id
                complaints_list.append(c)
            for doc in db.collection('staff_users').stream():
                s = doc.to_dict()
                staff_list.append({'id': doc.id, 'name': s.get('name', '')})
        except Exception as e:
            print(f"Complaints fetch error: {e}")
    return render_template('complaints.html', complaints=complaints_list, staff_list=staff_list)

@app.route('/api/complaints', methods=['POST'])
def add_complaint():
    if 'username' not in session and 'tenant_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if db is None: return jsonify({'error': 'Database not connected'}), 500
    try:
        data = request.json
        if not data or 'description' not in data:
            return jsonify({'error': 'Description is required'}), 400
        logged_by = session.get('username') or session.get('tenant_name', 'Tenant')
        ref = db.collection('complaints').document()
        ref.set({
            'tenant_name': data.get('tenant_name', ''),
            'property_ref': data.get('property_ref', ''),
            'category': data.get('category', 'General'),
            'description': data['description'],
            'assigned_to': data.get('assigned_to', ''),
            'status': 'Open',
            'created_at': datetime.now().isoformat(),
            'logged_by': logged_by
        })
        return jsonify({'success': True, 'id': ref.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/complaints/<cid>', methods=['PATCH'])
def update_complaint_status(cid):
    is_admin = 'username' in session
    is_staff = 'staff_id' in session
    if not is_admin and not is_staff:
        return jsonify({'error': 'Unauthorized'}), 401
    if db is None: return jsonify({'error': 'Database not connected'}), 500
    try:
        data = request.json
        update_data = {}
        if 'status' in data: update_data['status'] = data['status']
        if 'assigned_to' in data and is_admin: update_data['assigned_to'] = data['assigned_to']
        if 'resolution_note' in data: update_data['resolution_note'] = data['resolution_note']
        db.collection('complaints').document(cid).update(update_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
#  ADMIN — STAFF MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/admin/staff')
def staff_management():
    if 'username' not in session: return redirect(url_for('login'))
    staff_list = []
    if db is not None:
        try:
            for doc in db.collection('staff_users').stream():
                s = doc.to_dict(); s['id'] = doc.id
                staff_list.append(s)
        except Exception as e:
            print(f"Staff fetch error: {e}")
    return render_template('staff_management.html', staff_list=staff_list)

@app.route('/api/admin/staff', methods=['POST'])
def add_staff():
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    if db is None: return jsonify({'error': 'Database not connected'}), 500
    try:
        data = request.json
        for f in ['name', 'username', 'password']:
            if not data.get(f): return jsonify({'error': f'Missing {f}'}), 400
        # Check username uniqueness
        existing = db.collection('staff_users').where('username', '==', data['username']).stream()
        if any(True for _ in existing):
            return jsonify({'error': 'Username already taken'}), 400
        ref = db.collection('staff_users').document()
        ref.set({'name': data['name'], 'username': data['username'],
                 'password_hash': generate_password_hash(data['password']),
                 'created_at': datetime.now().isoformat()})
        return jsonify({'success': True, 'id': ref.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/staff/<sid>', methods=['DELETE'])
def delete_staff(sid):
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    if db is None: return jsonify({'error': 'Database not connected'}), 500
    try:
        db.collection('staff_users').document(sid).delete()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────────────────────────────────────
#  TENANT PORTAL
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/tenant/login', methods=['GET', 'POST'])
def tenant_login():
    if 'tenant_id' in session: return redirect(url_for('tenant_dashboard'))
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        phone = data.get('phone', '').strip()
        password = data.get('password', '')
        if db is None:
            flash('Database unavailable', 'error')
            return redirect(url_for('tenant_login'))
        try:
            docs = list(db.collection('tenants').where('phone', '==', phone).stream())
            if docs:
                tenant = docs[0].to_dict()
                pwd_hash = tenant.get('portal_password_hash', '')
                if pwd_hash and check_password_hash(pwd_hash, password):
                    session['tenant_id'] = docs[0].id
                    session['tenant_name'] = tenant.get('name', 'Tenant')
                    return redirect(url_for('tenant_dashboard'))
            flash('Invalid phone number or password.', 'error')
        except Exception as e:
            flash(f'Login error: {e}', 'error')
    return render_template('tenant_login.html')

@app.route('/tenant/logout')
def tenant_logout():
    session.pop('tenant_id', None)
    session.pop('tenant_name', None)
    return redirect(url_for('tenant_login'))

@app.route('/tenant/dashboard')
def tenant_dashboard():
    if 'tenant_id' not in session: return redirect(url_for('tenant_login'))
    tenant_id = session['tenant_id']
    tenant_data, active_agreement, payments_list, complaints_list = {}, None, [], []
    if db is not None:
        try:
            tdoc = db.collection('tenants').document(tenant_id).get()
            if tdoc.exists: tenant_data = tdoc.to_dict()
            # Active agreement
            for doc in db.collection('agreements').where('tenant_id', '==', tenant_id)\
                         .where('status', '==', 'Active').stream():
                active_agreement = doc.to_dict(); active_agreement['id'] = doc.id
                break
            # Payment history
            for doc in db.collection('payments').where('agreement_id', '==',
                         active_agreement['id'] if active_agreement else '').stream():
                p = doc.to_dict(); p['id'] = doc.id
                payments_list.append(p)
            payments_list.sort(key=lambda x: x.get('payment_date', ''), reverse=True)
            # Tenant's own complaints
            for doc in db.collection('complaints').where('tenant_name', '==',
                         tenant_data.get('name', '')).stream():
                c = doc.to_dict(); c['id'] = doc.id
                complaints_list.append(c)
            complaints_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        except Exception as e:
            print(f"Tenant dashboard error: {e}")
    return render_template('tenant_dashboard.html', tenant=tenant_data,
                           agreement=active_agreement, payments=payments_list,
                           complaints=complaints_list,
                           tenant_name=session.get('tenant_name', ''))

# ─────────────────────────────────────────────────────────────────────────────
#  STAFF PORTAL
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if 'staff_id' in session: return redirect(url_for('staff_dashboard'))
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')
        if db is None:
            flash('Database unavailable', 'error')
            return redirect(url_for('staff_login'))
        try:
            docs = list(db.collection('staff_users').where('username', '==', username).stream())
            if docs:
                staff = docs[0].to_dict()
                if check_password_hash(staff.get('password_hash', ''), password):
                    session['staff_id'] = docs[0].id
                    session['staff_name'] = staff.get('name', 'Staff')
                    return redirect(url_for('staff_dashboard'))
            flash('Invalid username or password.', 'error')
        except Exception as e:
            flash(f'Login error: {e}', 'error')
    return render_template('staff_login.html')

@app.route('/staff/logout')
def staff_logout():
    session.pop('staff_id', None)
    session.pop('staff_name', None)
    return redirect(url_for('staff_login'))

@app.route('/staff/dashboard')
def staff_dashboard():
    if 'staff_id' not in session: return redirect(url_for('staff_login'))
    staff_name = session.get('staff_name', '')
    complaints_list = []
    if db is not None:
        try:
            for doc in db.collection('complaints').where('assigned_to', '==', staff_name).stream():
                c = doc.to_dict(); c['id'] = doc.id
                complaints_list.append(c)
            complaints_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        except Exception as e:
            print(f"Staff dashboard error: {e}")
    return render_template('staff_dashboard.html',
                           staff={'name': staff_name},
                           staff_name=staff_name,
                           complaints=complaints_list)


if __name__ == '__main__':
    print('Starting SmartRentals Management System Server...')
    app.run(debug=True, host='0.0.0.0', port=5000)
