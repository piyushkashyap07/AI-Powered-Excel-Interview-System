#!/usr/bin/env python3
"""
Test MongoDB connection with the new configuration
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test the MongoDB connection"""
    try:
        # Get the MongoDB URI and database name
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB_NAME", "propensity_score_db")
        
        print(f"MongoDB URI: {mongodb_uri}")
        print(f"Database Name: {db_name}")
        
        # Create a client
        client = MongoClient(mongodb_uri, tlsAllowInvalidCertificates=True)
        
        # Test the connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Get the database
        db = client.get_database(db_name)
        print(f"✅ Connected to database: {db.name}")
        
        # List collections
        collections = db.list_collection_names()
        print(f"Collections in database: {collections}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing MongoDB connection...")
    success = test_mongodb_connection()
    
    if success:
        print("\n🎉 MongoDB connection test passed!")
        print("You can now run the main application.")
    else:
        print("\n❌ MongoDB connection test failed!")
        print("Please check your MongoDB URI and credentials.") 