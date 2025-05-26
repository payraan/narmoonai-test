from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import re

Base = declarative_base()

def clean_content(text):
    """پاک‌سازی نام کانال، امضا، و جایگزینی لینک‌ها"""
    if not text:
        return ""
    # لیست عبارت‌هایی که باید حذف شوند
    patterns = [
        r'@klondikeai',  # آی‌دی کانال
        r'Crypto AI by Klondike',
        r'Klondike Crypto AI',
        r'CryptoAI by Klondike',
        r'CryptoAI',       # اگر فقط همین هم مزاحمه اضافه کن
        r'Klondike',      # اگر کل متن کلوندایک رو می‌خواهی حذف کن، فعال کن (ممکنه اسم کوین باشه)
        r'https?://t\.me/[^\s]+',        # تمام لینک‌های تلگرام
        r'@KlondikeAI_Subscription_bot', # ربات اشتراک
        r'https?://www\.binance\.com/[^\s)]+', # لینک بایننس
        r'https?://binance\.com/[^\s)]+',
        r'\b(?:channel|کانال)\b[^\n]*', # اگر جایی اسم channel یا کانال اومده
    ]
    text = re.sub('|'.join(patterns), '', text, flags=re.IGNORECASE)
    # جایگزینی لینک‌های باقی‌مانده با لینک دلخواه (مثلاً دامنه خودت)
    text = re.sub(r'https?://[^\s)]+', 'https://narmoon.ir', text)
    # حذف فاصله‌های اضافه
    text = re.sub(r'\s+', ' ', text).strip()
    return text

class TelegramPost(Base):
    __tablename__ = 'telegram_posts'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, unique=True, nullable=False)
    channel_username = Column(String(100), nullable=False)
    content = Column(Text)
    date = Column(DateTime, nullable=False)
    views = Column(Integer, default=0)
    forwards = Column(Integer, default=0)
    has_media = Column(Boolean, default=False)
    media_type = Column(String(50))
    media_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        # پاک‌سازی متن و عدم نمایش channel_username
        return {
            'message_id': self.message_id,
            'content': clean_content(self.content),
            'date': self.date.isoformat(),
            'views': self.views,
            'forwards': self.forwards,
            'has_media': self.has_media,
            'media_type': self.media_type,
            'media_url': f'/media/{self.media_path.split("/")[-1]}' if self.has_media and self.media_path else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

