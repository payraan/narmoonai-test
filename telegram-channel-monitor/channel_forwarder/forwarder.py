from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
import asyncio
import re
import logging
from config import *

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forwarder.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChannelForwarder:
    def __init__(self):
        self.client = TelegramClient('forwarder_session', API_ID, API_HASH)
        
    def clean_message_text(self, text):
        """پاک‌سازی متن از برندینگ کانال اصلی"""
        if not text:
            return ""
        
        cleaned_text = text
        
        # حذف کلمات مزاحم
        for word in WORDS_TO_REMOVE:
            cleaned_text = cleaned_text.replace(word, "")
        
        # حذف لینک‌های اضافی
        cleaned_text = re.sub(r'http[s]?://\S+', '', cleaned_text)
        
        # حذف @ mentions اضافی
        cleaned_text = re.sub(r'@\w+', '', cleaned_text)
        
        # پاک‌سازی فاصله‌های اضافی
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text.strip())
        
        return cleaned_text

    def add_persian_content(self, original_text):
        """اضافه کردن محتوای فارسی"""
        if not original_text.strip():
            return PERSIAN_TEMPLATE.strip()
        return f"{original_text}{PERSIAN_TEMPLATE}"

    async def send_to_target(self, text, media=None):
        """ارسال پیام به کانال مقصد"""
        try:
            if not text.strip() and not media:
                logger.warning("⚠️ پیام خالی - ارسال نشد")
                return
                
            await self.client.send_message(
                TARGET_CHANNEL,
                text,
                file=media,
                parse_mode='markdown'
            )
            logger.info("✅ پیام با موفقیت ارسال شد")
            
        except FloodWaitError as e:
            logger.warning(f"⏰ محدودیت ارسال: {e.seconds} ثانیه صبر")
            await asyncio.sleep(e.seconds)
            await self.send_to_target(text, media)
            
        except Exception as e:
            logger.error(f"❌ خطا در ارسال: {e}")

    async def process_new_message(self, event):
        """پردازش پیام جدید"""
        try:
            message = event.message
            
            # چک کردن اینکه پیام از خود ما نیست
            if message.out:
                return
                
            # استخراج متن
            original_text = message.text or ""
            
            # پاک‌سازی
            cleaned_text = self.clean_message_text(original_text)
            
            # اضافه کردن محتوای فارسی  
            final_text = self.add_persian_content(cleaned_text)
            
            # استخراج مدیا
            media = message.media if message.media else None
            
            # ارسال به کانال مقصد
            await self.send_to_target(final_text, media)
            
            # لاگ
            source_chat = await event.get_chat()
            logger.info(f"📨 پیام از {source_chat.username or source_chat.title} پردازش شد")
            
        except Exception as e:
            logger.error(f"❌ خطا در پردازش: {e}")

    async def start_monitoring(self):
        """شروع مانیتورینگ"""
        logger.info("🚀 شروع مانیتورینگ کانال‌ها...")
        
        try:
            # اتصال به تلگرام
            await self.client.start(phone=PHONE_NUMBER)
            logger.info("✅ اتصال به تلگرام برقرار شد")
            
            # بررسی دسترسی به کانال‌ها
            for channel in SOURCE_CHANNELS:
                try:
                    entity = await self.client.get_entity(channel)
                    logger.info(f"✅ دسترسی به کانال مبدا: {entity.title}")
                except Exception as e:
                    logger.error(f"❌ خطا در دسترسی به {channel}: {e}")
            
            try:
                target_entity = await self.client.get_entity(TARGET_CHANNEL)
                logger.info(f"✅ دسترسی به کانال مقصد: {target_entity.title}")
            except Exception as e:
                logger.error(f"❌ خطا در دسترسی به کانال مقصد: {e}")
                return
            
            # ثبت event handler
            @self.client.on(events.NewMessage(chats=SOURCE_CHANNELS))
            async def handle_new_message(event):
                await self.process_new_message(event)
            
            logger.info(f"👀 مانیتورینگ {len(SOURCE_CHANNELS)} کانال شروع شد")
            logger.info(f"🎯 کانال مقصد: {TARGET_CHANNEL}")
            logger.info("⭐ برای توقف: Ctrl+C")
            
            # اجرای دائمی
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ خطای کلی: {e}")

async def main():
    forwarder = ChannelForwarder()
    try:
        await forwarder.start_monitoring()
    except KeyboardInterrupt:
        logger.info("🛑 متوقف شد توسط کاربر")
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره: {e}")

if __name__ == "__main__":
    print("🔥 Auto Channel Forwarder v1.0")
    print("🎯 کانال مبدا: KlondikeAI")
    print("🎯 کانال مقصد: NarmoonAI_VIP")
    print("=" * 40)
    asyncio.run(main())
