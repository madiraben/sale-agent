from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
import hashlib
import hmac
import json
from typing import Dict, Any, Optional
from config.settings import settings
from app.chatbot import ChatbotService

app = FastAPI(
    title="Messenger Chatbot API",
    description="A basic Facebook Messenger chatbot built with FastAPI",
    version="0.1.0"
)

# Initialize chatbot service
chatbot_service = ChatbotService()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Messenger Chatbot API is running!"}

@app.get("/webhook")
async def verify_webhook(
    request: Request,  # Add this
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token")
):
    """
    Webhook verification endpoint for Facebook Messenger
    This endpoint is called by Facebook to verify the webhook URL
    """
    # Debug logging
    print(f"=== WEBHOOK VERIFICATION DEBUG ===")
    print(f"Headers: {dict(request.headers)}")
    print(f"Query params: hub_mode={hub_mode}, hub_challenge={hub_challenge}, hub_verify_token={hub_verify_token}")
    print(f"Settings VERIFY_TOKEN: '{settings.VERIFY_TOKEN}'")
    print(f"Comparison: '{hub_verify_token}' == '{settings.VERIFY_TOKEN}' = {hub_verify_token == settings.VERIFY_TOKEN}")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        print("✅ Webhook verified successfully!")
        return PlainTextResponse(content=hub_challenge)
    else:
        print(f"❌ Webhook verification failed!")
        print(f"   Mode check: {hub_mode} == 'subscribe' = {hub_mode == 'subscribe'}")
        print(f"   Token check: {hub_verify_token} == {settings.VERIFY_TOKEN} = {hub_verify_token == settings.VERIFY_TOKEN}")
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Handle incoming messages from Facebook Messenger
    This endpoint receives all webhook events from Facebook
    """
    # Verify the request signature
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    if not verify_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse the request body
    try:
        data = json.loads(body.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Process the webhook data
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                await process_messaging_event(messaging_event)
    
    return {"status": "EVENT_RECEIVED"}

def verify_signature(payload: bytes, signature: str) -> bool:
    """
    Verify that the webhook request came from Facebook
    """
    if not settings.APP_SECRET:
        print("Warning: APP_SECRET not set, skipping signature verification")
        return True
    
    expected_signature = hmac.new(
        settings.APP_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Remove 'sha256=' prefix from signature
    signature_hash = signature.replace("sha256=", "")
    
    return hmac.compare_digest(expected_signature, signature_hash)

async def process_messaging_event(messaging_event: Dict[str, Any]):
    """
    Process individual messaging events
    """
    sender_id = messaging_event.get("sender", {}).get("id")
    recipient_id = messaging_event.get("recipient", {}).get("id")
    
    # Handle text messages
    if "message" in messaging_event:
        message = messaging_event["message"]
        
        # Skip if message has attachments only (no text)
        if "text" not in message:
            return
        
        message_text = message["text"]
        print(f"Received message from {sender_id}: {message_text}")
        
        # Generate response using chatbot service
        response_text = await chatbot_service.generate_response(message_text, sender_id)
        
        # Send response back to user
        await send_message(sender_id, response_text)
    
    # Handle postback events (button clicks, etc.)
    elif "postback" in messaging_event:
        postback = messaging_event["postback"]
        payload = postback.get("payload", "")
        print(f"Received postback from {sender_id}: {payload}")
        
        # Handle postback
        response_text = await chatbot_service.handle_postback(payload, sender_id)
        await send_message(sender_id, response_text)

async def send_message(recipient_id: str, message_text: str):
    """
    Send a text message to a Facebook Messenger user
    """
    await chatbot_service.send_text_message(recipient_id, message_text)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)