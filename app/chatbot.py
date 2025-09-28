import requests
import json
import re
from typing import Dict, Any, Optional
from config.settings import settings

class ChatbotService:
    """
    Main chatbot service for processing messages and generating responses
    """
    
    def __init__(self):
        self.page_access_token = settings.PAGE_ACCESS_TOKEN
        self.send_api_url = f"https://graph.facebook.com/v18.0/me/messages?access_token={self.page_access_token}"
        
        # Simple conversation state storage (in production, use a database)
        self.user_contexts = {}
    
    async def generate_response(self, message_text: str, sender_id: str) -> str:
        """
        Generate a response to the user's message using basic NLP and rules
        """
        message_lower = message_text.lower().strip()
        
        # Get or create user context
        user_context = self.user_contexts.get(sender_id, {"state": "default", "name": None})
        
        # Handle greetings
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            if user_context.get("name"):
                response = f"Hello again, {user_context['name']}! How can I help you today?"
            else:
                response = "Hello! Welcome to our chatbot. What's your name?"
                user_context["state"] = "waiting_for_name"
        
        # Handle name collection
        elif user_context.get("state") == "waiting_for_name":
            # Extract potential name from message
            name = self._extract_name(message_text)
            if name:
                user_context["name"] = name
                user_context["state"] = "default"
                response = f"Nice to meet you, {name}! How can I assist you today?"
            else:
                response = "I'd love to know your name! Could you tell me what I should call you?"
        
        # Handle help requests
        elif any(keyword in message_lower for keyword in ["help", "support", "assistance"]):
            response = self._get_help_message()
        
        # Handle product/service inquiries
        elif any(keyword in message_lower for keyword in ["product", "service", "price", "cost", "buy", "purchase"]):
            response = self._handle_product_inquiry(message_lower)
        
        # Handle thanks
        elif any(keyword in message_lower for keyword in ["thank", "thanks", "appreciate"]):
            response = "You're very welcome! Is there anything else I can help you with?"
        
        # Handle goodbye
        elif any(keyword in message_lower for keyword in ["bye", "goodbye", "see you", "farewell"]):
            name = user_context.get("name", "")
            response = f"Goodbye{', ' + name if name else ''}! Feel free to message me anytime. Have a great day!"
        
        # Handle questions
        elif message_text.strip().endswith("?"):
            response = self._handle_question(message_lower)
        
        # Default response
        else:
            response = self._get_default_response(message_lower)
        
        # Update user context
        self.user_contexts[sender_id] = user_context
        
        return response
    
    async def handle_postback(self, payload: str, sender_id: str) -> str:
        """
        Handle postback events (button clicks, quick replies, etc.)
        """
        if payload == "GET_STARTED":
            return "Welcome! I'm here to help you. What can I do for you today?"
        elif payload == "HELP":
            return self._get_help_message()
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
                if clean_word:
                    return clean_word
        return None
    
    def _get_help_message(self) -> str:
        """
        Get the help message with available commands
        """
        return """
I can help you with:
• General questions and information
• Product and service inquiries
• Support and assistance
• Just having a conversation!

Feel free to ask me anything or just say hello! 😊
        """.strip()
    
    def _handle_product_inquiry(self, message_lower: str) -> str:
        """
        Handle product or service related inquiries
        """
        if "price" in message_lower or "cost" in message_lower:
            return "For pricing information, please visit our website or contact our sales team. I can connect you with them if you'd like!"
        elif "product" in message_lower:
            return "We offer various products and services. What specific type of product are you interested in?"
        else:
            return "I'd be happy to help you learn about our products and services! What specifically are you looking for?"
    
    def _handle_question(self, message_lower: str) -> str:
        """
        Handle questions from users
        """
        if any(keyword in message_lower for keyword in ["how", "what", "when", "where", "why", "who"]):
            return "That's a great question! While I try my best to help, for detailed information I'd recommend contacting our support team or checking our website. Is there something specific I can help you with right now?"
        else:
            return "I'd love to help answer your question! Could you provide a bit more detail so I can give you the best response?"
    
    def _get_default_response(self, message_lower: str) -> str:
        """
        Generate a default response for unrecognized messages
        """
        responses = [
            "I understand! Tell me more about what you're looking for.",
            "Interesting! How can I help you with that?",
            "I'm here to help! Could you tell me more about what you need?",
            "Thanks for reaching out! What can I do for you today?",
            "I'd love to assist you! Can you provide a bit more detail?"
        ]
        
        # Simple hash-based selection for consistency per user input
        response_index = len(message_lower) % len(responses)
        return responses[response_index]