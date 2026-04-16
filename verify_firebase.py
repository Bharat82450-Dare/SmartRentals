import firebase_admin
from firebase_admin import credentials, firestore
import os

def verify():
    cred_path = 'serviceAccountKey.json'
    if not os.path.exists(cred_path):
        print(f"Error: {cred_path} not found.")
        return

    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        # Get project info
        project_id = cred.project_id
        print(f"INFO: Firebase initialized successfully.")
        print(f"INFO: Project ID: {project_id}")
        
        # Test read
        collections = db.collections()
        col_names = [c.id for c in collections]
        print(f"INFO: Available collections: {col_names if col_names else 'None (New Project)'}")
        
    except Exception as e:
        print(f"ERROR: Verification failed: {e}")

if __name__ == "__main__":
    verify()
