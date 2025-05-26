import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
SESSION_NAME = os.getenv('SESSION_NAME')
DATABASE_URL = os.getenv('DATABASE_URL')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

print(f"✅ Config loaded successfully!")
print(f"📱 Phone: {PHONE_NUMBER}")
print(f"📢 Channel: {CHANNEL_USERNAME}")
