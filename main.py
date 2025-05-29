# main.py - بهبود یافته با مدیریت خطا و پشتیبانی کامل از سیستم رفرال

import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram.error import Conflict

from config.settings import TELEGRAM_TOKEN
from config.constants import (
    MAIN_MENU, SELECTING_MARKET, SELECTING_TIMEFRAME,
    SELECTING_STRATEGY, WAITING_IMAGES,
    CRYPTO_MENU, DEX_MENU, DEX_SUBMENU, COIN_MENU
)

from database.operations import init_db
from simple_migration import simple_migration
from fix_referral_migration import fix_referral_migration

# Import handlers
from handlers.handlers import (
    start, handle_main_menu, show_market_selection, handle_market_selection,
    show_timeframes, handle_timeframe_selection, show_strategy_selection,
    handle_strategy_selection, receive_images, cancel,
    show_narmoon_products, show_ai_features, show_faq, usage_guide,
    terms_and_conditions, subscription_plans, support_contact,
    show_referral_panel, handle_referral_copy_link, handle_referral_details,
    debug_callback_handler
)

from handlers.crypto_handlers import (
    crypto_menu, dex_menu, coin_menu,
    handle_dex_option, handle_coin_option,
    handle_trending_options, handle_treasury_options,
    process_user_input
)

from admin.commands import admin_activate, admin_user_info, admin_stats, admin_broadcast

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

def main():
    """تابع اصلی با مدیریت خطای بهبود یافته"""
    
    try:
        # ایجاد پایگاه داده
        print("🔧 Initializing database...")
        init_db()
        print("✅ Database ready!")
        
        # اجرای Migration
        print("🔄 Running migration...")
        if simple_migration():
            print("✅ Migration completed!")
        else:
            print("⚠️ Migration had issues but continuing...")
        
        # اجرای Referral Migration
        print("🔧 Fixing referral tables...")
        if fix_referral_migration():
            print("✅ Referral fix completed!")
        else:
            print("⚠️ Referral fix had issues but continuing...")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("🔧 Try running the migration script first")
        return

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
                CallbackQueryHandler(handle_main_menu),
                CallbackQueryHandler(crypto_menu, pattern="^crypto$"),
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(show_referral_panel, pattern="^referral_panel$"),
                CallbackQueryHandler(handle_referral_copy_link, pattern="^copy_link_"),
                CallbackQueryHandler(handle_referral_details, pattern="^referral_details$"),
                CallbackQueryHandler(debug_callback_handler),  # این خط را اضافه کنید
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
            SELECTING_TIMEFRAME: [
                CallbackQueryHandler(handle_timeframe_selection, pattern='^tf_'),
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(show_market_selection, pattern="^analyze_charts$")
            ],
            SELECTING_STRATEGY: [
                CallbackQueryHandler(handle_strategy_selection, pattern=r'^(strategy_.*|ignore)$'),
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
