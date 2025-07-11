# auth_handler.py
from firebase_handler import auth_client, db # Import initialized auth_client and db
from datetime import datetime

class AuthHandler:
    def __init__(self):
        if not auth_client:
            raise ValueError("Firebase Auth client is not initialized. Check firebase_handler.py.")

    def login_user(self, email, password):
        """
        Authenticates a user using Firebase Email/Password.
        Note: The Firebase Admin SDK does not directly support password-based login
        for client authentication. It's for managing users or verifying ID tokens.
        For a Gradio app that doesn't use client-side JS SDK, a common workaround
        is to use Admin SDK to *verify user existence* and then manage sessions.
        A truly secure email/password login would involve Firebase Auth REST API or client SDK.
        For this demo, we'll verify user existence and mock a session.
        You MUST create users manually in Firebase Console -> Authentication -> Users
        for this login to work.
        """
        try:
            # Attempt to get user by email. If it fails, user doesn't exist or is disabled.
            user = auth_client.get_user_by_email(email)

            # In a real app, you'd securely compare the password hash or verify an ID token.
            # For this simple Gradio demo without client-side JS, we will
            # "assume" successful login if the user exists.
            # THIS IS A SIMPLIFICATION FOR DEMO PURPOSES.
            # A more secure approach for password verification would be needed for production.

            # Store/update user info in Firestore
            user_ref = db.collection('users').document(user.uid)
            if not user_ref.get().exists:
                user_ref.set({
                    'email': user.email,
                    'displayName': user.display_name or user.email.split('@')[0],
                    'createdAt': datetime.now()
                })
            user_ref.update({'lastLogin': datetime.now()})

            return user.uid, user.email, None # Return UID, email, and no error
        except Exception as e:
            return None, None, str(e) # Return no UID, no email, and the error

# Instantiate the AuthHandler
auth_manager = AuthHandler()
