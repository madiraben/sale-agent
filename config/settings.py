from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # Facebook App Configuration
    VERIFY_TOKEN: str = "your_verify_token_here"
    PAGE_ACCESS_TOKEN: Optional[str] = None
    APP_SECRET: Optional[str] = None
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    
    # Application Configuration  
    APP_NAME: str = "Messenger Chatbot"
    DEBUG: bool = False
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create a global settings instance
settings = Settings()