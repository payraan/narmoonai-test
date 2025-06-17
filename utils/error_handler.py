# utils/error_handler.py (فایل جدید)
from handlers.ui_helpers import main_menu_only, STANDARD_MESSAGES

async def handle_api_error(update, context, error_type="general"):
    """مدیریت استاندارد خطاها"""
    error_messages = {
        "api_limit": "⚠️ محدودیت روزانه درخواست‌ها به پایان رسیده است.",
        "network": "🌐 خطا در اتصال به شبکه. لطفاً دوباره تلاش کنید.",
        "general": STANDARD_MESSAGES["ERROR"]
    }
    
    await update.message.reply_text(
        error_messages.get(error_type, error_messages["general"]),
        reply_markup=main_menu_only()
    )

async def handle_callback_error(query, error_type="general"):
    """مدیریت خطاهای callback query"""
    error_messages = {
        "api_limit": "⚠️ محدودیت روزانه درخواست‌ها به پایان رسیده است.",
        "network": "🌐 خطا در اتصال به شبکه. لطفاً دوباره تلاش کنید.",
        "general": STANDARD_MESSAGES["ERROR"]
    }
    
    await query.edit_message_text(
        error_messages.get(error_type, error_messages["general"]),
        reply_markup=main_menu_only()
    )
