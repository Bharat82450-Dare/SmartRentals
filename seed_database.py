import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from werkzeug.security import generate_password_hash
import os

def seed():
    cred_path = 'serviceAccountKey.json'
    if not os.path.exists(cred_path):
        print(f"Error: {cred_path} not found.")
        return

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        db = firestore.client()

        print("INFO: Seeding properties...")
        properties = [
            {
                'address': 'Seaside Apartments, Block A',
                'flat_number': '101',
                'type': '2BHK',
                'rent_amount': 25000.0,
                'deposit_amount': 75000.0,
                'status': 'Vacant',
                'created_at': datetime.now().isoformat(),
                'owner': 'admin'
            },
            {
                'address': 'Seaside Apartments, Block B',
                'flat_number': '205',
                'type': '1BHK',
                'rent_amount': 15000.0,
                'deposit_amount': 45000.0,
                'status': 'Vacant',
                'created_at': datetime.now().isoformat(),
                'owner': 'admin'
            },
            {
                'address': 'Urban Heights, South Wing',
                'flat_number': '402',
                'type': '3BHK',
                'rent_amount': 45000.0,
                'deposit_amount': 135000.0,
                'status': 'Vacant',
                'created_at': datetime.now().isoformat(),
                'owner': 'admin'
            }
        ]

        for p in properties:
            db.collection('properties').add(p)
            print(f"INFO: Added property {p['flat_number']} - {p['address']}")

        print("INFO: Seeding initial staff...")
        staff = [
            {
                'name': 'John Plumber',
                'username': 'john_p',
                'password_hash': generate_password_hash('staff123'), # password is 'staff123'
                'created_at': datetime.now().isoformat()
            }
        ]
        
        for s in staff:
            db.collection('staff_users').add(s)
            print(f"INFO: Added staff {s['name']} (username: {s['username']}, pass: staff123)")

        print("INFO: Seeding complete.")

    except Exception as e:
        print(f"ERROR: Seeding failed: {e}")

if __name__ == "__main__":
    seed()
