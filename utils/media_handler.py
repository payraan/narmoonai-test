# utils/media_handler.py
import os
import tempfile
from telegram import Update, InlineKeyboardMarkup, InputMediaPhoto, InputMediaAnimation
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

class MediaHandler:
   def __init__(self):
       self.media_path = "resources/media/"
       self.gifs_path = os.path.join(self.media_path, "gifs/")
       self.images_path = os.path.join(self.media_path, "images/")
       self.ensure_media_directories()
   
   def ensure_media_directories(self):
       """اطمینان از وجود پوشه‌های رسانه"""
       directories = [self.media_path, self.gifs_path, self.images_path]
       for directory in directories:
           if not os.path.exists(directory):
               os.makedirs(directory)
               print(f"📁 Created directory: {directory}")
   
   def file_exists(self, file_path):
       """بررسی وجود فایل"""
       return os.path.exists(file_path) and os.path.getsize(file_path) > 0
   
   async def send_welcome_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              reply_markup: InlineKeyboardMarkup = None):
       """ارسال رسانه خوشامدگویی"""
       print(f"🔍 DEBUG: Looking for GIF at: {self.gifs_path}welcome.gif")
       welcome_gif = os.path.join(self.gifs_path, "welcome.gif")
       print(f"🔍 DEBUG: File exists: {self.file_exists(welcome_gif)}")
       
       if self.file_exists(welcome_gif):
           try:
               print(f"🔍 DEBUG: Attempting to send GIF...")
               with open(welcome_gif, 'rb') as gif:
                   user_name = update.effective_user.first_name or "کاربر"
                   caption = (
                       f"سلام {user_name} عزیز! 👋✨\n\n"
                       "🚀 به دستیار هوش مصنوعی نارموون خوش اومدی!\n\n"
                       "اینجا می‌تونی بازارها رو تحلیل کنی و سیگنال بگیری 📈"
                   )
                   
                   await context.bot.send_animation(
                       chat_id=update.effective_chat.id,
                       animation=gif,
                       caption=caption,
                       reply_markup=reply_markup,
                       parse_mode=ParseMode.MARKDOWN
                   )
                   print(f"✅ DEBUG: GIF sent successfully!")
                   return True
           except Exception as e:
               print(f"❌ Error sending welcome GIF: {e}")
       else:
           print(f"❌ DEBUG: GIF file not found or empty")
       
       return False
   
   async def send_crypto_menu_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  message_text: str, reply_markup: InlineKeyboardMarkup = None):
       """ارسال رسانه برای منوی کریپتو"""
       crypto_gif = os.path.join(self.gifs_path, "crypto_market.gif")
       
       if self.file_exists(crypto_gif):
           try:
               with open(crypto_gif, 'rb') as gif:
                   await context.bot.send_animation(
                       chat_id=update.effective_chat.id,
                       animation=gif,
                       caption=message_text,
                       reply_markup=reply_markup,
                       parse_mode=ParseMode.MARKDOWN
                   )
                   return True
           except Exception as e:
               print(f"❌ Error sending crypto GIF: {e}")
       
       return False

# نمونه global
media_handler = MediaHandler()


async def download_photo(file_id: str, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """
    عکس را در یک فایل موقت امن دانلود کرده و مسیر آن را برمی‌گرداند.
    فایل پس از استفاده باید به صورت دستی پاک شود.
    """
    try:
        bot_file = await context.bot.get_file(file_id)
        
        # استخراج پسوند اصلی فایل
        file_ext = os.path.splitext(bot_file.file_path)[1]
        
        # ساخت فایل موقت امن با پسوند صحیح
        # delete=False ضروری است تا فایل پس از خروج از with باقی بماند
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        
        await bot_file.download_to_drive(temp_file.name)
        print(f"✅ Photo downloaded to temporary file: {temp_file.name}")
        temp_file.close() # بستن فایل
        return temp_file.name
            
    except Exception as e:
        print(f"❌ Error downloading photo: {e}")
        return None
