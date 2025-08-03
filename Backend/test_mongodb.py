#!/usr/bin/env python3
"""
Test script to verify MongoDB connection
"""
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

def test_mongodb_uri():
    """Test MongoDB URI parsing and encoding"""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    print(f"Original URI: {mongodb_uri}")
    
    # Handle URL encoding for username and password if they exist in the URI
    if "@" in mongodb_uri and "mongodb://" in mongodb_uri:
        try:
            # Split the URI to get the protocol and the rest
            protocol_part = mongodb_uri.split("://", 1)
            if len(protocol_part) == 2:
                protocol = protocol_part[0] + "://"
                rest = protocol_part[1]
                
                # Check if there are credentials
                if "@" in rest:
                    credentials_part = rest.split("@", 1)
                    if len(credentials_part) == 2:
                        credentials = credentials_part[0]
                        host_part = credentials_part[1]
                        
                        # Split credentials into username and password
                        if ":" in credentials:
                            username, password = credentials.split(":", 1)
                            # URL encode username and password
                            encoded_username = quote_plus(username)
                            encoded_password = quote_plus(password)
                            # Reconstruct the URI
                            encoded_uri = f"{protocol}{encoded_username}:{encoded_password}@{host_part}"
                            print(f"Encoded URI: {encoded_uri}")
                            return encoded_uri
        except Exception as e:
            print(f"Error encoding URI: {e}")
    
    print("No encoding needed or URI format not recognized")
    return mongodb_uri

if __name__ == "__main__":
    print("Testing MongoDB URI encoding...")
    test_mongodb_uri()
    
    print("\nTo fix the MongoDB connection issue:")
    print("1. Create a .env file in the Backend directory")
    print("2. Add your MongoDB URI with properly encoded credentials")
    print("3. Example: MONGODB_URI=mongodb://username%40domain.com:password%40here@localhost:27017/dbname")
    print("4. Or use local MongoDB without auth: MONGODB_URI=mongodb://localhost:27017") 