from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

from config.settings import TELEGRAM_TOKEN
from debug_logger import logger, debug_wrapper
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

from admin.commands import admin_activate, admin_help, admin_user_info, admin_stats, admin_broadcast

from command_handlers import (
    handle_start_command, handle_analyze_command, handle_crypto_command,
    handle_dex_command, handle_coin_command, handle_trending_command,
    handle_hotcoins_command, handle_tokeninfo_command, handle_holders_command,
    handle_subscription_command, handle_terms_command, handle_faq_command,
    handle_support_command
)

# Wrapper functions for commands
@debug_wrapper("dex_wrapper")
async def dex_wrapper(update, context):
    """Wrapper for /dex command"""
    from handlers.crypto_handlers import get_dex_menu_keyboard
    from database.operations import get_subscription_status
    
    user_id = update.effective_user.id
    subscription_status = get_subscription_status(user_id)
    
    if subscription_status == "inactive":
        await update.message.reply_text(
            "❌ شما اشتراک فعالی ندارید.\n"
            "برای استفاده از این بخش، لطفاً اشتراک تهیه کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💳 خرید اشتراک", callback_data="subscription_plans")
            ]])
        )
        return
    
    text = "🔄 نارموون دکس - انتخاب کنید:"
    keyboard = get_dex_menu_keyboard() if hasattr(crypto_handlers, 'get_dex_menu_keyboard') else [
        [InlineKeyboardButton("📊 توکن ترندینگ", callback_data="dex_trending")],
        [InlineKeyboardButton("📈 توکن تاپ گینرز", callback_data="dex_top_gainers")],
        [InlineKeyboardButton("📉 توکن تاپ لوزرز", callback_data="dex_top_losers")],
        [InlineKeyboardButton("🔍 جستجوی توکن", callback_data="dex_search")],
        [InlineKeyboardButton("🔎 آدرس دکس", callback_data="dex_address")],
        [InlineKeyboardButton("📊 تحلیل هولدرها", callback_data="dex_holders")],
        [InlineKeyboardButton("📄 اطلاعات توکن", callback_data="dex_token_info")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="crypto")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

@debug_wrapper("coin_wrapper")
async def coin_wrapper(update, context):
    """Wrapper for /coin command"""
    from handlers.crypto_handlers import get_coin_menu_keyboard
    from database.operations import get_subscription_status
    
    user_id = update.effective_user.id
    subscription_status = get_subscription_status(user_id)
    
    if subscription_status == "inactive":
        await update.message.reply_text(
            "❌ شما اشتراک فعالی ندارید.\n"
            "برای استفاده از این بخش، لطفاً اشتراک تهیه کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💳 خرید اشتراک", callback_data="subscription_plans")
            ]])
        )
        return
    
    text = "🪙 نارموون کوین - انتخاب کنید:"
    keyboard = get_coin_menu_keyboard() if hasattr(crypto_handlers, 'get_coin_menu_keyboard') else [
        [InlineKeyboardButton("🔥 کوین های داغ", callback_data="coin_hot")],
        [InlineKeyboardButton("🚀 کوین های بازیگران", callback_data="coin_players")],
        [InlineKeyboardButton("💰 کوین های معاملاتی", callback_data="coin_trading")],
        [InlineKeyboardButton("💎 کوین های ذخیره ارزش", callback_data="coin_store_of_value")],
        [InlineKeyboardButton("🏛️ تحلیل ترژری", callback_data="coin_treasury")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="crypto")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

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

@debug_wrapper("analyze_wrapper")
async def analyze_wrapper(update, context):
    """Wrapper for /analyze command"""
    await show_market_selection(update, context)

@debug_wrapper("faq_wrapper")
async def faq_wrapper(update, context):
    """Wrapper for /faq command"""
    # مستقیم پیام رو می‌فرستیم بدون callback_query
    from config.texts import STATIC_TEXTS
    faq_text = STATIC_TEXTS["faq_content"] if 'STATIC_TEXTS' in dir() else """
❓ سوالات متداول

1️⃣ ربات چگونه کار می‌کند؟
2️⃣ چگونه اشتراک تهیه کنم؟
3️⃣ آیا نیاز به دانش تخصصی دارم؟

برای اطلاعات بیشتر با پشتیبانی تماس بگیرید.
"""
    
    await update.message.reply_text(
        faq_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
        ]])
    )

@debug_wrapper("terms_wrapper")
async def terms_wrapper(update, context):
    """Wrapper for /terms command"""
    # مستقیم پیام رو می‌فرستیم بدون callback_query
    from config.texts import STATIC_TEXTS
    terms_text = STATIC_TEXTS["terms_and_conditions"] if 'STATIC_TEXTS' in dir() else """
📋 قوانین و مقررات استفاده از ربات

با استفاده از این ربات، شما با قوانین زیر موافقت می‌کنید:
• استفاده مسئولانه از خدمات
• عدم اشتراک‌گذاری اکانت
• رعایت قوانین معاملات

نسخه: 1.0
"""
    
    await update.message.reply_text(
        terms_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
        ]])
    )

@debug_wrapper("support_wrapper")
async def support_wrapper(update, context):
    """Wrapper for /support command"""
    support_text = """
👨‍💻 پشتیبانی ربات تحلیل چارت
برای ارتباط با پشتیبان و ارسال TXID پرداخت، لطفاً با آیدی زیر در تلگرام تماس بگیرید:

📱 @mmpouya

ساعات پاسخگویی: 9 صبح تا 9 شب
    """
    
    await update.message.reply_text(
        support_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
        ]])
    )

async def holders_wrapper(update, context):
    """Wrapper for /holders command"""
    await update.message.reply_text(
        "👥 برای بررسی هولدرها، ابتدا به منوی دکس بروید:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")
        ]])
    )

def main():
    logger.info("🤖 Starting Narmoon Bot...")
    
    # ایجاد پایگاه داده
    logger.info("Initializing database...")
    init_db()
    
    # ایجاد اپلیکیشن
    logger.info("Creating application...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    logger.info("Adding command handlers...")

    # Command handlers برای menu shortcuts - قبل از ConversationHandler
    app.add_handler(CommandHandler("analyze", handle_analyze_command))
    app.add_handler(CommandHandler("crypto", handle_crypto_command))
    app.add_handler(CommandHandler("dex", handle_dex_command))
    app.add_handler(CommandHandler("coin", handle_coin_command))
    app.add_handler(CommandHandler("trending", handle_trending_command))
    app.add_handler(CommandHandler("hotcoins", handle_hotcoins_command))
    app.add_handler(CommandHandler("tokeninfo", handle_tokeninfo_command))
    app.add_handler(CommandHandler("holders", handle_holders_command))
    app.add_handler(CommandHandler("subscription", handle_subscription_command))
    app.add_handler(CommandHandler("terms", handle_terms_command))
    app.add_handler(CommandHandler("faq", handle_faq_command))
    app.add_handler(CommandHandler("support", handle_support_command))

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
