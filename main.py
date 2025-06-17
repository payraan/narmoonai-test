# این بلوک کد را جایگزین import های فعلی در بالای فایل main.py کنید

import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.error import Conflict

from config.settings import TELEGRAM_TOKEN
from config.constants import (
    MAIN_MENU, SELECTING_MARKET, SELECTING_ANALYSIS_TYPE, SELECTING_TIMEFRAME,
    SELECTING_STRATEGY, WAITING_IMAGES,
    CRYPTO_MENU, DEX_MENU, DEX_SUBMENU, COIN_MENU,
    TRADE_COACH_AWAITING_INPUT  # <-- ثابت جدید اضافه شد
)

from database import init_db, db_manager
from database.repository import get_user_info, get_user_api_stats

# Import handlers (نسخه اصلاح و تمیز شده)
from handlers.handlers import (
    start, handle_main_menu, show_market_selection, handle_market_selection,
    show_timeframes, handle_timeframe_selection, show_strategy_selection,
    handle_strategy_selection, receive_images, cancel,
    show_narmoon_products, show_ai_features, show_faq, show_faq_page2, usage_guide,
    terms_and_conditions, terms_and_conditions_page2, terms_and_conditions_page3,
    subscription_plans, support_contact,
    handle_tnt_plan_selection, handle_analysis_type_selection,
    show_analysis_type_selection, show_referral_panel,
)

from handlers.crypto_handlers import (
    crypto_menu, dex_menu, coin_menu,
    handle_dex_option, handle_coin_option,
    handle_trending_options, handle_treasury_options,
    process_user_input, handle_tnt_analysis_request,
    handle_trending_coins_list,
    trade_coach_handler,           # <-- هندلر جدید اضافه شد
    trade_coach_prompt_handler     # <-- هندلر جدید اضافه شد
)

from admin.commands import admin_activate, admin_user_info, admin_stats, admin_broadcast, admin_referral_stats, admin_health_check

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update, context):
    """مدیریت خطاهای عمومی"""
    logger.error(f"Update {update} caused error {context.error}")
    
    # مدیریت خطای Conflict
    if isinstance(context.error, Conflict):
        logger.warning("Bot conflict detected - another instance may be running")
        # اینجا می‌توانید bot را restart کنید یا صبر کنید
        await asyncio.sleep(5)
        return
    
    # سایر خطاها
    if update and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ خطایی رخ داده است. لطفاً دوباره تلاش کنید یا /start را بزنید."
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

def safe_migration():
    """Migration ایمن که بر اساس محیط تصمیم می‌گیرد"""
    import os
    
    database_url = os.getenv("DATABASE_URL")
    
    if database_url and database_url.startswith("postgres"):
        # Production: PostgreSQL - فقط init_db کافیه
        print("🐘 PostgreSQL detected - using init_db only")
        return True
    else:
        # Development: SQLite - migration مفصل
        print("🗄️ SQLite detected - running full migration")
        try:
            from simple_migration import simple_migration
            return simple_migration()
        except Exception as e:
            print(f"⚠️ Migration warning: {e}")
            return True  # ادامه می‌دهیم حتی اگر migration مشکل داشته باشد

# Wrapper هوشمند برای تبدیل callback handlers به command handlers
def create_command_wrapper(callback_handler):
    """Wrapper برای تبدیل callback handlers به command handlers"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        class MockQuery:
            async def answer(self):
                pass
            async def edit_message_text(self, text, reply_markup=None, parse_mode=None, **kwargs):
                await update.message.reply_text(
                    text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                    **kwargs
                )
        mock_update = type('MockUpdate', (), {
            'callback_query': MockQuery(),
            'effective_user': update.effective_user
        })()
        return await callback_handler(mock_update, context)
    return wrapper

# تابع /status
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش وضعیت اشتراک کاربر"""
    user_id = update.effective_user.id
    try:
        user = get_user_info(user_id)
        api_stats = get_user_api_stats(user_id)
        if not user:
            await update.message.reply_text("❌ کاربر یافت نشد!")
            return
        
        plan_type = user.get('tnt_plan_type', 'رایگان')
        is_active = '✅ فعال' if user.get('is_tnt_plan_active', False) else '❌ غیرفعال'
        message = f"""📊 **وضعیت اشتراک شما**

🎯 **پلن TNT:** {plan_type}
📅 **وضعیت:** {is_active}
📈 **استفاده امروز:** {api_stats.get('today', 0)} درخواست
📊 **کل استفاده:** {api_stats.get('total', 0)} درخواست"""
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]]
        
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error in status_command: {e}")
        await update.message.reply_text("❌ خطا در دریافت اطلاعات.")

# تابع /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنمای کامل دستورات ربات"""
    help_text = """🤖 **راهنمای ربات نارموون**

🏠 **منوهای اصلی:**
/start - شروع ربات
/crypto - منوی رمزارزها
/analyze - تحلیل نمودار
/coach - مربی ترید

💰 **اشتراک و حساب:**
/subscription - خرید اشتراک
/status - وضعیت اشتراک من
/referral - پنل رفرال

ℹ️ **راهنمایی:**
/help - این راهنما
/support - پشتیبانی
/cancel - لغو عملیات

💡 **نکته:** برای شروع، دستور /start را بزنید!"""
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]]
    await update.message.reply_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def main():
    """تابع اصلی با مدیریت خطای بهبود یافته"""
    
    try:
        # ایجاد پایگاه داده
        print("🔧 Initializing database...")
        # auto_migrate_tnt_system()  # Disabled for SQLAlchemy
        print("✅ Database ready!")
        
        # اجرای Migration ایمن - Disabled for SQLAlchemy
        # print("🔄 Running safe migration...")
        # if safe_migration():
        #     print("✅ Migration completed!")
        # else:
        #     print("⚠️ Migration had issues but continuing...")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("🔧 Continuing without migration...")
        # ادامه می‌دهیم چون init_db کار کرده

    # ایجاد اپلیکیشن با تنظیمات بهبود یافته
    print("🤖 Building Telegram application...")
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # اضافه کردن error handler
    app.add_error_handler(error_handler)

    # تعریف conversation handler
    conv_handler = ConversationHandler( 
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("analyze", show_market_selection),
            CommandHandler("coach", trade_coach_handler),
        ],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(handle_tnt_plan_selection, pattern="^(tnt_mini|tnt_plus|tnt_max)$"),  # اول این
                CallbackQueryHandler(terms_and_conditions_page2, pattern="^terms_page2$"),
                CallbackQueryHandler(terms_and_conditions_page3, pattern="^terms_page3$"),
                CallbackQueryHandler(show_faq_page2, pattern="^faq_page2$"),
                # CallbackQueryHandler(debug_callback_handler),  # ← کامنت شده
                CallbackQueryHandler(trade_coach_handler, pattern='^trade_coach$'),
                CallbackQueryHandler(crypto_menu, pattern="^crypto$"),
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(subscription_plans, pattern="^subscription$"),
                CallbackQueryHandler(handle_main_menu),  # handlers عمومی بعد از specific ones
            ],
            CRYPTO_MENU: [
                CallbackQueryHandler(dex_menu, pattern="^narmoon_dex$"),
                CallbackQueryHandler(coin_menu, pattern="^narmoon_coin$"),
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(crypto_menu, pattern="^crypto$")
            ],
            DEX_MENU: [
                CallbackQueryHandler(handle_dex_option, pattern="^dex_"),
                CallbackQueryHandler(handle_trending_options, pattern="^trending_"),
                CallbackQueryHandler(handle_tnt_analysis_request, pattern="^tnt_analysis_crypto$"),
                CallbackQueryHandler(dex_menu, pattern="^narmoon_dex$"),
                CallbackQueryHandler(crypto_menu, pattern="^crypto$"),
                CallbackQueryHandler(start, pattern="^main_menu$")
            ],
            DEX_SUBMENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_user_input),
                CallbackQueryHandler(dex_menu, pattern="^narmoon_dex$"),
                CallbackQueryHandler(crypto_menu, pattern="^crypto$"),
                CallbackQueryHandler(start, pattern="^main_menu$")
            ],
            COIN_MENU: [
                CallbackQueryHandler(handle_coin_option, pattern="^coin_"),
                CallbackQueryHandler(handle_trending_coins_list, pattern="^trending_coins_list$"),
                CallbackQueryHandler(handle_treasury_options, pattern="^treasury_"),
                CallbackQueryHandler(coin_menu, pattern="^narmoon_coin$"),
                CallbackQueryHandler(crypto_menu, pattern="^crypto$"),
                CallbackQueryHandler(start, pattern="^main_menu$")
            ],
            SELECTING_MARKET: [
                CallbackQueryHandler(handle_market_selection, pattern='^market_'),
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(show_market_selection, pattern="^analyze_charts$")
            ],
            SELECTING_ANALYSIS_TYPE: [
                CallbackQueryHandler(handle_analysis_type_selection, pattern='^analysis_'),
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(show_market_selection, pattern="^analyze_charts$")
            ],
            SELECTING_TIMEFRAME: [
                CallbackQueryHandler(handle_timeframe_selection, pattern='^tf_'),
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(show_market_selection, pattern="^analyze_charts$")
            ],
            SELECTING_STRATEGY: [
                CallbackQueryHandler(handle_strategy_selection),
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(show_market_selection, pattern="^analyze_charts$"),
                CallbackQueryHandler(show_timeframes, pattern="^back_to_timeframes$")
            ],
            WAITING_IMAGES: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_images),
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(show_market_selection, pattern="^analyze_charts$")
            ],
            TRADE_COACH_AWAITING_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, trade_coach_prompt_handler),
                MessageHandler(filters.PHOTO, trade_coach_prompt_handler),
                CallbackQueryHandler(trade_coach_handler, pattern="^continue_coach$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(start, pattern="^main_menu$")
        ],
        allow_reentry=True,
        per_message=False
    )
    
    # افزودن handlers
    app.add_handler(conv_handler)

    # Command handlers برای menu shortcuts با استفاده از Wrapper
    app.add_handler(CommandHandler("subscription", create_command_wrapper(subscription_plans)))
    app.add_handler(CommandHandler("referral", create_command_wrapper(show_referral_panel)))
    app.add_handler(CommandHandler("support", create_command_wrapper(support_contact)))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("crypto", crypto_menu))

    # Command handlers برای menu shortcuts
    app.add_handler(CommandHandler("analyze", show_market_selection))
    app.add_handler(CommandHandler("crypto", crypto_menu))
    app.add_handler(CommandHandler("subscription", subscription_plans))
    app.add_handler(CommandHandler("terms", terms_and_conditions))
    app.add_handler(CommandHandler("faq", show_faq))
    app.add_handler(CommandHandler("support", support_contact))

    # Command handlers wrapper functions
    async def trending_wrapper(update, context):
        update.callback_query = type('obj', (object,), {
            'data': 'trending_all_networks',
            'answer': lambda: None,
            'edit_message_text': update.message.reply_text
        })()
        await handle_trending_options(update, context)

    async def dex_wrapper(update, context):
        await dex_menu(update, context)

    async def coin_wrapper(update, context):
        await coin_menu(update, context)

    async def tokeninfo_wrapper(update, context):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        await update.message.reply_text(
            "🔍 برای اطلاعات توکن، ابتدا به منوی دکس بروید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")
            ]])
        )

    async def holders_wrapper(update, context):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        await update.message.reply_text(
            "👥 برای بررسی هولدرها، ابتدا به منوی دکس بروید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")
            ]])
        )

    # اضافه کردن command handlers
    app.add_handler(CommandHandler("dex", dex_wrapper))
    app.add_handler(CommandHandler("coin", coin_wrapper))
    app.add_handler(CommandHandler("trending", trending_wrapper))
    app.add_handler(CommandHandler("hotcoins", coin_wrapper))
    app.add_handler(CommandHandler("tokeninfo", tokeninfo_wrapper))
    app.add_handler(CommandHandler("holders", holders_wrapper))

    # دستورات مدیریتی
    app.add_handler(CommandHandler("activate", admin_activate))
    # app.add_handler(CommandHandler("adminhelp", admin_help))  # موقتاً غیرفعال
    app.add_handler(CommandHandler("userinfo", admin_user_info))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CommandHandler("referralstats", admin_referral_stats))
    # دستورات مدیریتی TNT
    from admin.commands import admin_activate_tnt, admin_tnt_stats, admin_user_tnt_info, admin_clean_database, admin_db_stats, admin_reset_db
    app.add_handler(CommandHandler("activatetnt", admin_activate_tnt))
    app.add_handler(CommandHandler("tntstats", admin_tnt_stats))
    app.add_handler(CommandHandler("usertnt", admin_user_tnt_info))
    app.add_handler(CommandHandler("cleandb", admin_clean_database))
    app.add_handler(CommandHandler("dbstats", admin_db_stats))
    app.add_handler(CommandHandler("resetdb", admin_reset_db))
    app.add_handler(CommandHandler("health", admin_health_check))

    print("🤖 ربات نارموون آماده است!")
    print(f"✅ توکن: {TELEGRAM_TOKEN[:10]}...")
    print("📊 برای توقف: Ctrl+C")
    
    # اجرای bot با مدیریت خطای بهبود یافته
    try:
        print("🚀 Starting bot polling...")
        app.run_polling()

    except Conflict:
        print("❌ Bot conflict detected!")
        print("🔧 Another bot instance is running. Please:")
        print("   1. Stop all other Railway services")
        print("   2. Run: python bot_conflict_resolver.py")
        print("   3. Wait 10 seconds and restart")
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
        print("🔧 Check logs for more details")

if __name__ == "__main__":
    print("🌟 Narmoon Trading Bot")
    print("=" * 30)
    main()
    print("=" * 30)
    print("👋 Goodbye!")


