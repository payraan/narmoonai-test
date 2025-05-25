import logging
from datetime import datetime

# تنظیم logger
def setup_logger():
    logger = logging.getLogger('narmoon_bot')
    logger.setLevel(logging.DEBUG)
    
    # Handler برای console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger

# ایجاد logger
logger = setup_logger()

# Wrapper برای debug کردن functions
def debug_wrapper(func_name):
    def decorator(func):
        async def wrapper(update, context):
            user_id = update.effective_user.id if update.effective_user else "Unknown"
            logger.info(f"🟢 {func_name} called by user {user_id}")
            
            try:
                # Log the update type
                if update.message:
                    logger.info(f"📨 Message update: {update.message.text}")
                elif update.callback_query:
                    logger.info(f"🔘 Callback query: {update.callback_query.data}")
                
                result = await func(update, context)
                logger.info(f"✅ {func_name} completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"❌ Error in {func_name}: {str(e)}")
                logger.exception("Full traceback:")
                
                # Send error to user
                if update.message:
                    await update.message.reply_text(
                        f"❌ خطا در اجرای دستور: {str(e)}\n"
                        f"لطفاً به پشتیبانی اطلاع دهید."
                    )
                raise
                
        return wrapper
    return decorator
