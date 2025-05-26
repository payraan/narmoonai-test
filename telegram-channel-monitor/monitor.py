from telethon import TelegramClient, events
from datetime import datetime, timedelta
import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal
from models import TelegramPost
from config import API_ID, API_HASH, PHONE_NUMBER, SESSION_NAME, CHANNEL_USERNAME
import logging
import re
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- تابع پاکسازی پیام و حذف هر ردی از کانال ---
def clean_message_text(text: str) -> str:
    text = re.sub(r'@[A-Za-z0-9_]+', '', text)
    text = re.sub(r'https?://t\\.me/[^\\s]+', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return f"🤖 پیام از دستیار هوش مصنوعی نارموون:\n{text}"

class ChannelMonitor:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        # اطمینان از وجود پوشه مدیا
        os.makedirs('media', exist_ok=True)

    async def start(self):
        await self.client.start(phone=PHONE_NUMBER)
        logger.info("Client started successfully")
        await self.fetch_recent_posts(hours=24)
        await self.setup_handlers()

    async def fetch_recent_posts(self, hours=24):
        try:
            channel = await self.client.get_entity(CHANNEL_USERNAME)
            after_date = datetime.now() - timedelta(hours=hours)
            messages = []
            async for message in self.client.iter_messages(
                channel,
                offset_date=datetime.now(),
                reverse=False
            ):
                if message.date.replace(tzinfo=None) < after_date:
                    break
                messages.append(message)
            logger.info(f"Found {len(messages)} messages from last {hours} hours")
            async with AsyncSessionLocal() as db:
                for msg in messages:
                    await self.save_message(db, msg, CHANNEL_USERNAME)
                await db.commit()
        except Exception as e:
            logger.error(f"Error fetching recent posts: {e}")

    async def save_message(self, db, message, channel_username):
        try:
            stmt = select(TelegramPost).where(
                TelegramPost.message_id == message.id,
                TelegramPost.channel_username == channel_username
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            # --- تعیین media_path (نام عکس) فقط اگر عکس وجود دارد ---
            media_path = None
            if message.media:
                # فعلاً: نام عکس message_id.jpg در پوشه media
                media_path = f"media/{message.id}.jpg"
                if not os.path.exists(media_path):
                    await self.client.download_media(message, media_path)

            if existing:
                existing.views = getattr(message, 'views', 0) or 0
                existing.forwards = getattr(message, 'forwards', 0) or 0
            else:
                post = TelegramPost(
                    message_id=message.id,
                    channel_username=channel_username, # فیلد در دیتابیس هست ولی در API خروجی نده!
                    content=clean_message_text(message.text or message.message),
                    date=message.date.replace(tzinfo=None),
                    views=getattr(message, 'views', 0) or 0,
                    forwards=getattr(message, 'forwards', 0) or 0,
                    has_media=bool(message.media),
                    media_type=type(message.media).__name__ if message.media else None,
                    media_path=media_path,
                    created_at=datetime.utcnow(),
                )
                db.add(post)
        except Exception as e:
            logger.error(f"Error saving message: {e}")

    async def setup_handlers(self):
        @self.client.on(events.NewMessage(chats=CHANNEL_USERNAME))
        async def new_message_handler(event):
            logger.info(f"New message: {event.message.id}")
            async with AsyncSessionLocal() as db:
                await self.save_message(db, event.message, CHANNEL_USERNAME)
                await db.commit()
        logger.info(f"Monitoring channel: {CHANNEL_USERNAME}")

    async def run_forever(self):
        await self.start()
        logger.info("Bot is running... Press Ctrl+C to stop")
        await self.client.run_until_disconnected()

