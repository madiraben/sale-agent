import requests
import json
import re
from typing import Dict, Any, Optional
from openai import OpenAI
from config.settings import settings

class ChatbotService:
    """
    Main chatbot service for processing messages and generating responses using OpenAI
    """
    
    def __init__(self):
        self.page_access_token = settings.PAGE_ACCESS_TOKEN
        self.send_api_url = f"https://graph.facebook.com/v18.0/me/messages?access_token={self.page_access_token}"
        
        # Initialize OpenAI client
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            print("Warning: OPENAI_API_KEY not set, OpenAI features will not work")
            self.openai_client = None
        
        # Simple conversation state storage (in production, use a database)
        self.user_contexts = {}
        
        # System prompt for the chatbot
        self.system_prompt = """You are a helpful and friendly sales assistant chatbot. Your role is to:
        
1. Greet customers warmly and professionally
2. Answer questions about products and services
3. Provide helpful information and support
4. Guide customers through their purchase journey
5. Handle customer inquiries with empathy and understanding
6. Keep responses conversational but professional
7. If you don't know something specific, offer to connect them with human support

Keep your responses concise (under 160 characters when possible for messaging) but informative. 
Be personable and use the customer's name when you know it.
Focus on being helpful and building trust with potential customers."""
    
    async def generate_response(self, message_text: str, sender_id: str) -> str:
        """
        Generate a response to the user's message using OpenAI
        """
        if not self.openai_client:
            return "I'm sorry, but I'm currently unable to process your message. Please try again later or contact our support team."
        
        # Get or create user context
        user_context = self.user_contexts.get(sender_id, {"conversation_history": [], "name": None})
        
        # Add user message to conversation history
        user_context["conversation_history"].append({"role": "user", "content": message_text})
        
        # Keep conversation history manageable (last 10 messages)
        if len(user_context["conversation_history"]) > 10:
            user_context["conversation_history"] = user_context["conversation_history"][-10:]
        
        try:
            # Prepare messages for OpenAI
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add user context if we have a name
            if user_context.get("name"):
                context_message = f"The customer's name is {user_context['name']}. Use their name in your responses when appropriate."
                messages.append({"role": "system", "content": context_message})
            
            # Add conversation history
            messages.extend(user_context["conversation_history"])
            
            # Generate response using OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            bot_response = response.choices[0].message.content.strip()
            
            # Extract name if this seems like an introduction
            if not user_context.get("name") and any(word in message_text.lower() for word in ["my name is", "i'm", "i am", "call me"]):
                extracted_name = self._extract_name(message_text)
                if extracted_name:
                    user_context["name"] = extracted_name
            
            # Add bot response to conversation history
            user_context["conversation_history"].append({"role": "assistant", "content": bot_response})
            
            # Update user context
            self.user_contexts[sender_id] = user_context
            
            return bot_response
            
        except Exception as e:
            print(f"Error generating OpenAI response: {str(e)}")
            # Fallback to a generic helpful response
            return "I'm having trouble processing your message right now. Could you please try again? If the issue persists, I can connect you with our support team."
    
    async def handle_postback(self, payload: str, sender_id: str) -> str:
        """
        Handle postback events (button clicks, quick replies, etc.)
        """
        # Use OpenAI to handle postbacks as well for more natural responses
        if self.openai_client:
            try:
                postback_context = f"The user clicked a button with payload: {payload}. Respond appropriately."
                
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "system", "content": postback_context},
                    {"role": "user", "content": f"Button clicked: {payload}"}
                ]
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=100,
                    temperature=0.5
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"Error generating postback response: {str(e)}")
        
        # Fallback responses for specific payloads
        if payload == "GET_STARTED":
            return "Welcome! I'm here to help you. What can I do for you today?"
        elif payload == "HELP":
            return "I'm here to help! You can ask me about our products, services, pricing, or anything else you'd like to know."
        elif payload == "CONTACT_SUPPORT":
            return "You can contact our support team at support@example.com or call +1-234-567-8900"
        else:
            return "Thanks for clicking that button! How can I help you?"
    
    async def send_text_message(self, recipient_id: str, message_text: str):
        """
        Send a text message to Facebook Messenger user
        """
        if not self.page_access_token:
            print("Warning: PAGE_ACCESS_TOKEN not set, cannot send messages")
            return
        
        message_data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        try:
            response = requests.post(
                self.send_api_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(message_data)
            )
            
            if response.status_code == 200:
                print(f"Message sent successfully to {recipient_id}")
            else:
                print(f"Failed to send message: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error sending message: {str(e)}")
    
    def _extract_name(self, text: str) -> Optional[str]:
        """
        Extract a name from the user's message
        """
        # Simple name extraction - look for capitalized words
        words = text.split()
        for word in words:
            # Skip common non-name words
            if word.lower() in ["i'm", "my", "name", "is", "call", "me", "i", "am"]:
                continue
            # Look for capitalized words (potential names)
            if word and word[0].isupper() and len(word) > 1:
                # Clean the word (remove punctuation)
                clean_word = re.sub(r'[^\w]', '', word)
                if clean_word and len(clean_word) > 1:
                    return clean_word
        return None