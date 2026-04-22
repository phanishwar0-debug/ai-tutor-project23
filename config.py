import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ai_tutor_db')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Admin credentials (for initial setup)
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@aitutor.com')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')