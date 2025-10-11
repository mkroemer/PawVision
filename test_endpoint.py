#!/usr/bin/env python3
"""Simple test script to check the current-video endpoint."""

import requests
import json

def test_endpoint():
    """Test the /api/current-video endpoint."""
    try:
        print("Testing /api/current-video endpoint...")
        response = requests.get("http://localhost:5001/api/current-video", timeout=5)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Endpoint is working!")
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                print(f"Response text: {response.text}")
        else:
            print(f"❌ Endpoint returned status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on localhost:5001?")
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_endpoint()
