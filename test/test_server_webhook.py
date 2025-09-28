#!/usr/bin/env python3
"""
Test script to be run ON THE SERVER to test webhook locally
This bypasses SSL issues and tests the actual webhook processing
"""
import requests
import json
import hashlib
import hmac

def test_webhook_localhost():
    # Test on localhost (bypass SSL)
    url = "http://localhost:8000/webhook"
    
    # Test message payload
    payload = {
        "object": "page",
        "entry": [{
            "id": "61558633094614",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "test_user_12345"},
                "recipient": {"id": "61558633094614"},
                "timestamp": 1234567890,
                "message": {
                    "mid": "test_message_id",
                    "text": "Hello! I want to know about your products!"
                }
            }]
        }]
    }
    
    # Convert to JSON
    payload_json = json.dumps(payload)
    
    # Create proper signature
    app_secret = "857b677a97ebcfbcf290e960c2dd5e48"  # From your .env
    signature = hmac.new(
        app_secret.encode('utf-8'),
        payload_json.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={signature}"
    }
    
    print("Testing webhook on localhost...")
    print(f"Payload: {payload_json}")
    print(f"Signature: sha256={signature}")
    
    try:
        response = requests.post(url, headers=headers, data=payload_json, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook test successful!")
            print("🎉 Check the logs with: sudo journalctl -u messenger-bot -f --no-pager -l")
        else:
            print(f"❌ Webhook test failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

def test_health_check():
    """Test the basic health check endpoint"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"Health check - Status: {response.status_code}")
        print(f"Health check - Response: {response.text}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    print("=== TESTING WEBHOOK ON SERVER ===")
    test_health_check()
    print()
    test_webhook_localhost()