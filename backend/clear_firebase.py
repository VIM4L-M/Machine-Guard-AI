"""
Script to clear all sensor data from Firebase Realtime Database.
Use this to refresh/reset your Firebase data.
"""

import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db

# Load environment variables
load_dotenv()

def clear_firebase_data():
    """Delete all sensor readings from Firebase."""
    
    # Get Firebase config from environment
    credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-key.json")
    database_url = os.getenv("FIREBASE_DATABASE_URL")
    
    if not database_url:
        print("❌ Error: FIREBASE_DATABASE_URL not set in .env file")
        return False
    
    if not os.path.exists(credentials_path):
        print(f"❌ Error: Firebase credentials file not found: {credentials_path}")
        return False
    
    try:
        # Initialize Firebase
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
        
        print(f"✓ Connected to Firebase: {database_url}")
        
        # Get reference to sensor_readings node
        ref = db.reference('sensor_readings')
        
        # Check if data exists
        data = ref.get()
        if data:
            print(f"📊 Found data in Firebase. Deleting...")
            # Delete all data under sensor_readings
            ref.delete()
            print("✓ All sensor readings deleted successfully!")
        else:
            print("ℹ️  No data found in Firebase (already empty)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        # Clean up
        try:
            firebase_admin.delete_app(firebase_admin.get_app())
        except:
            pass

if __name__ == "__main__":
    print("=" * 50)
    print("Firebase Data Cleanup Script")
    print("=" * 50)
    
    # Confirm with user
    response = input("\n⚠️  This will DELETE ALL sensor data from Firebase.\nAre you sure? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        print("\n🔄 Clearing Firebase data...")
        if clear_firebase_data():
            print("\n✅ Done! Firebase is now empty and ready for fresh data.")
        else:
            print("\n❌ Failed to clear Firebase data. Check the error above.")
    else:
        print("\n❌ Cancelled. No data was deleted.")
