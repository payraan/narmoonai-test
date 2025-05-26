from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

from config.settings import TELEGRAM_TOKEN
from config.constants import (
    MAIN_MENU, SELECTING_MARKET, SELECTING_TIMEFRAME,
    SELECTING_STRATEGY, WAITING_IMAGES,
    CRYPTO_MENU, DEX_MENU, DEX_SUBMENU, COIN_MENU
)

from database.operations import init_db

from handlers.handlers import (
    start, handle_main_menu, show_market_selection, handle_market_selection,
    show_timeframes, handle_timeframe_selection, show_strategy_selection,
    handle_strategy_selection, receive_images, cancel,
    show_narmoon_products, show_ai_features, show_faq, usage_guide,
    terms_and_conditions, subscription_plans, support_contact
)

from handlers.crypto_handlers import (
    crypto_menu, dex_menu, coin_menu,
    handle_dex_option, handle_coin_option,
    handle_trending_options, handle_treasury_options,
    process_user_input
)

from admin.commands import admin_activate, admin_help, admin_user_info, admin_stats, admin_broadcast

# Wrapper functions for commands
async def dex_wrapper(update, context):
    """Wrapper for /dex command"""
    # ایجاد mock callback_query برای سازگاری با تابع اصلی
    class MockCallbackQuery:
        def __init__(self, message):
            self.message = message
            self.data = "narmoon_dex"
        
        async def answer(self):
            pass
        
        async def edit_message_text(self, *args, **kwargs):
            await self.message.reply_text(*args, **kwargs)
    
    update.callback_query = MockCallbackQuery(update.message)
    await dex_menu(update, context)

async def coin_wrapper(update, context):
    """Wrapper for /coin command"""
    # ایجاد mock callback_query برای سازگاری با تابع اصلی
    class MockCallbackQuery:
        def __init__(self, message):
            self.message = message
            self.data = "narmoon_coin"
        
        async def answer(self):
            pass
        
        async def edit_message_text(self, *args, **kwargs):
            await self.message.reply_text(*args, **kwargs)
    
    update.callback_query = MockCallbackQuery(update.message)
    await coin_menu(update, context)

async def trending_wrapper(update, context):
    """Wrapper for /trending command"""
    # شبیه‌سازی callback query برای trending
    class MockCallbackQuery:
        def __init__(self, message):
            self.data = 'trending_all_networks'
            self.message = message
        
        async def answer(self):
            pass
        
        async def edit_message_text(self, *args, **kwargs):
            await self.message.reply_text(*args, **kwargs)
    
    update.callback_query = MockCallbackQuery(update.message)
    await handle_trending_options(update, context)

async def hotcoins_wrapper(update, context):
    """Wrapper for /hotcoins command"""
    await coin_menu(update, context)

async def tokeninfo_wrapper(update, context):
    """Wrapper for /tokeninfo command"""
    await update.message.reply_text(
        "🔍 برای اطلاعات توکن، ابتدا به منوی دکس بروید:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")
        ]])
    )

async def analyze_wrapper(update, context):
    """Wrapper for /analyze command"""
    await show_market_selection(update, context)

async def faq_wrapper(update, context):
    """Wrapper for /faq command"""
    await show_faq(update, context)

async def terms_wrapper(update, context):
    """Wrapper for /terms command"""
    await terms_and_conditions(update, context)

async def support_wrapper(update, context):
    """Wrapper for /support command"""
    await support_contact(update, context)

async def holders_wrapper(update, context):
    """Wrapper for /holders command"""
    await update.message.reply_text(
        "👥 برای بررسی هولدرها، ابتدا به منوی دکس بروید:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")
        ]])
    )

def main():
    # ایجاد پایگاه داده
    init_db()

    # ایجاد اپلیکیشن
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Command handlers برای menu shortcuts - قبل از ConversationHandler
    app.add_handler(CommandHandler("analyze", analyze_wrapper))
    app.add_handler(CommandHandler("crypto", crypto_menu))
    app.add_handler(CommandHandler("dex", dex_wrapper))
    app.add_handler(CommandHandler("coin", coin_wrapper))
    app.add_handler(CommandHandler("trending", trending_wrapper))
    app.add_handler(CommandHandler("hotcoins", hotcoins_wrapper))
    app.add_handler(CommandHandler("tokeninfo", tokeninfo_wrapper))
    app.add_handler(CommandHandler("holders", holders_wrapper))
    app.add_handler(CommandHandler("subscription", subscription_plans))
    app.add_handler(CommandHandler("terms", terms_wrapper))
    app.add_handler(CommandHandler("faq", faq_wrapper))
    app.add_handler(CommandHandler("support", support_wrapper))

    # تعریف conversation handler اصلی
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(handle_main_menu),
                CallbackQueryHandler(crypto_menu, pattern="^crypto$"),
                CallbackQueryHandler(start, pattern="^main_menu$")
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
        allow_reentry=True
    )

    # افزودن conversation handler
    app.add_handler(conv_handler)

    # دستورات مدیریتی
    app.add_handler(CommandHandler("activate", admin_activate))
    app.add_handler(CommandHandler("adminhelp", admin_help))
    app.add_handler(CommandHandler("userinfo", admin_user_info))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))

    print("🤖 ربات نارموون آماده است! اجرا شد.")
    print(f"✅ توکن: {TELEGRAM_TOKEN[:10]}...")
    print("📊 برای توقف: Ctrl+C")

    app.run_polling()

if __name__ == "__main__":
    main()
