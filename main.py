# main.py - بهبود یافته با مدیریت خطا و پشتیبانی کامل از سیستم رفرال

import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram.error import Conflict

from config.settings import TELEGRAM_TOKEN
from config.constants import (
    MAIN_MENU, SELECTING_MARKET, SELECTING_ANALYSIS_TYPE, SELECTING_TIMEFRAME,
    SELECTING_STRATEGY, WAITING_IMAGES,
    CRYPTO_MENU, DEX_MENU, DEX_SUBMENU, COIN_MENU
)

from database import init_db, db_manager
from database.migration import run_migration

# Import handlers
from handlers.handlers import (
    start, handle_main_menu, show_market_selection, handle_market_selection,
    show_timeframes, handle_timeframe_selection, show_strategy_selection,
    handle_strategy_selection, receive_images, cancel,
    show_narmoon_products, show_ai_features, show_faq, show_faq_page2, usage_guide,
    terms_and_conditions, terms_and_conditions_page2, terms_and_conditions_page3, subscription_plans, support_contact,
    show_referral_panel, handle_referral_copy_link, handle_referral_details,
    handle_tnt_plan_selection,
    debug_callback_handler
)

from handlers.crypto_handlers import (
    crypto_menu, dex_menu, coin_menu,
    handle_dex_option, handle_coin_option,
    handle_trending_options, handle_treasury_options,
    process_user_input, handle_tnt_analysis_request,
    handle_trending_coins_list
)

from admin.commands import admin_activate, admin_user_info, admin_stats, admin_broadcast, admin_referral_stats

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

def main():
    """تابع اصلی با مدیریت خطای بهبود یافته"""
    
    try:
        # ایجاد پایگاه داده
        print("🔧 Initializing database...")
        init_db()
        run_migration()  # اجرای migration
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
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(handle_tnt_plan_selection, pattern="^(tnt_mini|tnt_plus|tnt_max)$"),  # اول این
                CallbackQueryHandler(handle_referral_copy_link, pattern="^copy_link_.*"),
                CallbackQueryHandler(handle_referral_details, pattern="^referral_details$"),
                CallbackQueryHandler(terms_and_conditions_page2, pattern="^terms_page2$"),
                CallbackQueryHandler(terms_and_conditions_page3, pattern="^terms_page3$"),
                CallbackQueryHandler(show_faq_page2, pattern="^faq_page2$"),
                CallbackQueryHandler(show_referral_panel, pattern="^referral_panel$"),
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


