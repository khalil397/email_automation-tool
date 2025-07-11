# firebase_handler.py
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import json # To parse JSON string from environment variable if used

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK.
    It attempts to load credentials from:
    1. GOOGLE_APPLICATION_CREDENTIALS environment variable (standard GCP way).
    2. FIREBASE_SERVICE_ACCOUNT_KEY environment variable (for custom deployments).
    3. serviceAccountKey.json file (for local development/testing).
    """
    try:
        if not firebase_admin._apps: # Check if Firebase app is already initialized
            cred = None
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                # Standard way to load credentials in Google Cloud environments
                cred = credentials.ApplicationDefault()
            elif os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY'):
                # For custom deployment environments where key is passed as a string
                key_json = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY'))
                cred = credentials.Certificate(key_json)
            else:
                # For local development: expects serviceAccountKey.json in the root
                # REMEMBER: Add serviceAccountKey.json to .gitignore!
                if os.path.exists("serviceAccountKey.json"):
                    cred = credentials.Certificate("serviceAccountKey.json")
                else:
                    raise FileNotFoundError("serviceAccountKey.json not found and no Firebase credentials in environment.")

            firebase_admin.initialize_app(cred, {
                'projectId': os.getenv('FIREBASE_PROJECT_ID') # Get project ID from env
            })
            print("Firebase Admin SDK initialized successfully.")
        return True
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
        return False

# Initialize Firebase when this module is imported
if initialize_firebase():
    db = firestore.client()
    auth_client = auth
else:
    db = None
    auth_client = None
    print("Firestore and Auth clients not available due to Firebase initialization error.")
