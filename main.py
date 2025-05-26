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

from handlers.crypto_handlers import (
    crypto_menu, dex_menu, coin_menu,
    handle_dex_option, handle_coin_option,
    handle_trending_options, handle_treasury_options,
    process_user_input
)

from admin.commands import admin_activate, admin_help, admin_user_info, admin_stats, admin_broadcast

# Simple wrapper functions that work with commands
async def cmd_start(update, context):
    """Command wrapper for /start"""
    await start(update, context)

async def cmd_analyze(update, context):
    """Command wrapper for /analyze"""
    # Send message directly without callback_query
    market_buttons = [
        [InlineKeyboardButton("🪙 رمزارزها", callback_data="market_crypto")],
        [
            InlineKeyboardButton("📈 فارکس", callback_data="market_forex"),
            InlineKeyboardButton("💹 سهام", callback_data="market_stocks")
        ],
        [
            InlineKeyboardButton("🏅 طلا", callback_data="market_gold"),
            InlineKeyboardButton("🛢️ نفت", callback_data="market_oil")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
    ]
    
    await update.message.reply_text(
        "📊 لطفاً بازار مورد نظر خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(market_buttons)
    )

async def cmd_crypto(update, context):
    """Command wrapper for /crypto"""
    keyboard = [
        [InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")],
        [InlineKeyboardButton("🪙 نارموون کوین", callback_data="narmoon_coin")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    
    await update.message.reply_text(
        "🪙 منوی کریپتو - انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cmd_dex(update, context):
    """Command wrapper for /dex"""
    keyboard = [
        [InlineKeyboardButton("📊 توکن ترندینگ", callback_data="dex_trending")],
        [InlineKeyboardButton("📈 توکن تاپ گینرز", callback_data="dex_top_gainers")],
        [InlineKeyboardButton("📉 توکن تاپ لوزرز", callback_data="dex_top_losers")],
        [InlineKeyboardButton("🔍 جستجوی توکن", callback_data="dex_search")],
        [InlineKeyboardButton("🔎 آدرس دکس", callback_data="dex_address")],
        [InlineKeyboardButton("📊 تحلیل هولدرها", callback_data="dex_holders")],
        [InlineKeyboardButton("📄 اطلاعات توکن", callback_data="dex_token_info")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="crypto")]
    ]
    
    await update.message.reply_text(
        "🔄 نارموون دکس - انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cmd_coin(update, context):
    """Command wrapper for /coin"""
    keyboard = [
        [InlineKeyboardButton("🔥 کوین های داغ", callback_data="coin_hot")],
        [InlineKeyboardButton("🚀 کوین های بازیگران", callback_data="coin_players")],
        [InlineKeyboardButton("💰 کوین های معاملاتی", callback_data="coin_trading")],
        [InlineKeyboardButton("💎 کوین های ذخیره ارزش", callback_data="coin_store_of_value")],
        [InlineKeyboardButton("🏛️ تحلیل ترژری", callback_data="coin_treasury")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="crypto")]
    ]
    
    await update.message.reply_text(
        "🪙 نارموون کوین - انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cmd_trending(update, context):
    """Command wrapper for /trending"""
    keyboard = [
        [InlineKeyboardButton("🌐 همه شبکه‌ها", callback_data="trending_all_networks")],
        [InlineKeyboardButton("🔷 اتریوم", callback_data="trending_ethereum")],
        [InlineKeyboardButton("🟡 بایننس", callback_data="trending_bsc")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="narmoon_dex")]
    ]
    
    await update.message.reply_text(
        "📊 توکن‌های ترندینگ - شبکه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cmd_hotcoins(update, context):
    """Command wrapper for /hotcoins"""
    await cmd_coin(update, context)

async def cmd_tokeninfo(update, context):
    """Command wrapper for /tokeninfo"""
    await update.message.reply_text(
        "🔍 برای دریافت اطلاعات توکن:\n\n"
        "1️⃣ به منوی دکس بروید\n"
        "2️⃣ گزینه 'اطلاعات توکن' را انتخاب کنید\n"
        "3️⃣ آدرس توکن را ارسال کنید",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")
        ]])
    )

async def cmd_holders(update, context):
    """Command wrapper for /holders"""
    await update.message.reply_text(
        "👥 برای بررسی هولدرها:\n\n"
        "1️⃣ به منوی دکس بروید\n"
        "2️⃣ گزینه 'تحلیل هولدرها' را انتخاب کنید\n"
        "3️⃣ آدرس توکن را ارسال کنید",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")
        ]])
    )

async def cmd_subscription(update, context):
    """Command wrapper for /subscription"""
    await subscription_plans(update, context)

async def cmd_terms(update, context):
    """Command wrapper for /terms"""
    terms_text = """
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

async def cmd_faq(update, context):
    """Command wrapper for /faq"""
    faq_text = """
❓ سوالات متداول

1️⃣ ربات چگونه کار می‌کند؟
پاسخ: ربات با استفاده از هوش مصنوعی تصاویر چارت را تحلیل می‌کند.

2️⃣ آیا نیاز به دانش تخصصی دارم؟
پاسخ: خیر، ربات به زبان ساده توضیح می‌دهد.

3️⃣ چگونه اشتراک تهیه کنم؟
پاسخ: از منوی اشتراک یا تماس با پشتیبانی.
"""
    
    await update.message.reply_text(
        faq_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
        ]])
    )

async def cmd_support(update, context):
    """Command wrapper for /support"""
    support_text = """
📞 ارتباط با پشتیبانی

🆔 آیدی پشتیبان: @mmpouya
⏰ ساعات پاسخگویی: 9 صبح تا 9 شب

شماره کاربری شما: {}
""".format(update.effective_user.id)
    
    await update.message.reply_text(
        support_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💬 پیام به پشتیبان", url="https://t.me/mmpouya"),
            InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")
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
    
    # Command handlers - before ConversationHandler
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("analyze", cmd_analyze))
    app.add_handler(CommandHandler("crypto", cmd_crypto))
    app.add_handler(CommandHandler("dex", cmd_dex))
    app.add_handler(CommandHandler("coin", cmd_coin))
    app.add_handler(CommandHandler("trending", cmd_trending))
    app.add_handler(CommandHandler("hotcoins", cmd_hotcoins))
    app.add_handler(CommandHandler("tokeninfo", cmd_tokeninfo))
    app.add_handler(CommandHandler("holders", cmd_holders))
    app.add_handler(CommandHandler("subscription", cmd_subscription))
    app.add_handler(CommandHandler("terms", cmd_terms))
    app.add_handler(CommandHandler("faq", cmd_faq))
    app.add_handler(CommandHandler("support", cmd_support))

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
