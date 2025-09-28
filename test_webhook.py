#!/usr/bin/env python3
"""
Test script to verify the webhook endpoint works correctly
This bypasses ngrok's browser warning by including the proper headers
"""

import requests
import sys

def test_webhook_verification(ngrok_url, verify_token):
    """Test the webhook verification endpoint"""
    
    # Construct the webhook URL
    webhook_url = f"{ngrok_url}/webhook"
    
    # Parameters that Facebook sends for webhook verification
    params = {
        'hub.mode': 'subscribe',
        'hub.challenge': 'test_challenge_12345',
        'hub.verify_token': verify_token
    }
    
    # Headers to bypass ngrok browser warning
    headers = {
        'ngrok-skip-browser-warning': 'true',
        'User-Agent': 'FacebookBot/1.0'
    }
    
    try:
        print(f"Testing webhook verification at: {webhook_url}")
        print(f"Using verify token: {verify_token}")
        print("Headers:", headers)
        print("Parameters:", params)
        print("-" * 50)
        
        response = requests.get(webhook_url, params=params, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            if response.text == params['hub.challenge']:
                print("✅ Webhook verification SUCCESSFUL!")
                print("Your webhook is configured correctly.")
                return True
            else:
                print("❌ Webhook verification FAILED!")
                print(f"Expected: {params['hub.challenge']}")
                print(f"Got: {response.text}")
                return False
        else:
            print("❌ Webhook verification FAILED!")
            print(f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to webhook: {e}")
        return False

def test_webhook_post(ngrok_url):
    """Test the POST webhook endpoint"""
    
    webhook_url = f"{ngrok_url}/webhook"
    
    # Sample Facebook webhook payload
    test_payload = {
        "object": "page",
        "entry": [
            {
                "id": "123456789",
                "time": 1234567890,
                "messaging": [
                    {
                        "sender": {"id": "test_user_id"},
                        "recipient": {"id": "test_page_id"},
                        "timestamp": 1234567890,
                        "message": {
                            "mid": "test_message_id",
                            "text": "Hello, this is a test message!"
                        }
                    }
                ]
            }
        ]
    }
    
    headers = {
        'ngrok-skip-browser-warning': 'true',
        'Content-Type': 'application/json',
        'User-Agent': 'FacebookBot/1.0'
    }
    
    try:
        print(f"\nTesting POST webhook at: {webhook_url}")
        print("Payload:", test_payload)
        print("-" * 50)
        
        response = requests.post(webhook_url, json=test_payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ POST webhook test SUCCESSFUL!")
            return True
        else:
            print("❌ POST webhook test FAILED!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to POST webhook: {e}")
        return False

if __name__ == "__main__":
    # Configuration
    ngrok_url = "https://36870ad90b7c.ngrok-free.app"
    verify_token = "123"
    
    if len(sys.argv) > 1:
        ngrok_url = sys.argv[1]
    if len(sys.argv) > 2:
        verify_token = sys.argv[2]
    
    print("🚀 Testing Facebook Messenger Webhook")
    print(f"ngrok URL: {ngrok_url}")
    print(f"Verify Token: {verify_token}")
    print("=" * 60)
    
    # Test GET webhook verification
    success1 = test_webhook_verification(ngrok_url, verify_token)
    
    # Test POST webhook
    success2 = test_webhook_post(ngrok_url)
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your webhook is ready for Facebook Messenger integration.")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please check your server and configuration.")