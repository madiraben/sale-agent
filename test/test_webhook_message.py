#!/usr/bin/env python3
"""
Test script to send a properly formatted webhook request
This will help us test if the message processing is working
"""
import requests
import json
import hashlib
import hmac

def test_webhook():
    # Your webhook URL
    url = "https://social-sale-agent-webhook.click/webhook"
    
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
                    "text": "Hello! This is a test message from the debug script."
                }
            }]
        }]
    }
    
    # Convert to JSON
    payload_json = json.dumps(payload)
    
    # Create proper signature (you'll need your APP_SECRET)
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
    
    print("Testing webhook with proper signature...")
    print(f"Payload: {payload_json}")
    print(f"Signature: sha256={signature}")
    
    try:
        response = requests.post(url, headers=headers, data=payload_json, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook test successful!")
        else:
            print(f"❌ Webhook test failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

if __name__ == "__main__":
    test_webhook()