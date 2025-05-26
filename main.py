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

def main():
    # ایجاد پایگاه داده
    init_db()

    # ایجاد اپلیکیشن
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # تعریف conversation handler اصلی با navigation fixes
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                # Handle all main menu callbacks
                CallbackQueryHandler(handle_main_menu),
                CallbackQueryHandler(crypto_menu, pattern="^crypto$"),
                # Fix: Handle navigation from analysis section back to main menu
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
                # Fix: Handle back to main menu
                CallbackQueryHandler(start, pattern="^main_menu$")
            ],
            DEX_SUBMENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_user_input),
                CallbackQueryHandler(dex_menu, pattern="^narmoon_dex$"),
                CallbackQueryHandler(crypto_menu, pattern="^crypto$"),
                # Fix: Handle back to main menu
                CallbackQueryHandler(start, pattern="^main_menu$")
            ],
            COIN_MENU: [
                CallbackQueryHandler(handle_coin_option, pattern="^coin_"),
                CallbackQueryHandler(handle_treasury_options, pattern="^treasury_"),
                CallbackQueryHandler(coin_menu, pattern="^narmoon_coin$"),
                CallbackQueryHandler(crypto_menu, pattern="^crypto$"),
                # Fix: Handle back to main menu
                CallbackQueryHandler(start, pattern="^main_menu$")
            ],
            SELECTING_MARKET: [
                CallbackQueryHandler(handle_market_selection, pattern='^market_'),
                # Fix: Add navigation handlers for market selection
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(show_market_selection, pattern="^analyze_charts$")
            ],
            SELECTING_TIMEFRAME: [
                CallbackQueryHandler(handle_timeframe_selection, pattern='^tf_'),
                # Fix: Add navigation handlers for timeframe selection
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(show_market_selection, pattern="^analyze_charts$")
            ],
            SELECTING_STRATEGY: [
                CallbackQueryHandler(handle_strategy_selection, pattern=r'^(strategy_.*|ignore)$'),
                # Fix: Add navigation handlers for strategy selection
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(show_market_selection, pattern="^analyze_charts$"),
                CallbackQueryHandler(show_timeframes, pattern="^back_to_timeframes$")
            ],
            WAITING_IMAGES: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_images),
                # Fix: Add navigation handlers for image waiting state
                CallbackQueryHandler(start, pattern="^main_menu$"),
                CallbackQueryHandler(show_market_selection, pattern="^analyze_charts$")
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            # Fix: Add universal fallback for main menu
            CallbackQueryHandler(start, pattern="^main_menu$")
        ],
        allow_reentry=True
    )

   # افزودن هندلرها
    app.add_handler(conv_handler)

    # Command handlers برای menu shortcuts
    app.add_handler(CommandHandler("analyze", show_market_selection))
    app.add_handler(CommandHandler("crypto", crypto_menu))
    app.add_handler(CommandHandler("subscription", subscription_plans))
    app.add_handler(CommandHandler("terms", terms_and_conditions))
    app.add_handler(CommandHandler("faq", show_faq))
    app.add_handler(CommandHandler("support", support_contact))

    # Command handlers برای توابع پیچیده‌تر
    async def trending_wrapper(update, context):
        # شبیه‌سازی callback query برای trending
        update.callback_query = type('obj', (object,), {
            'data': 'trending_all_networks',
            'answer': lambda: None,
            'edit_message_text': update.message.reply_text
        })()
        await handle_trending_options(update, context)

    async def hotcoins_wrapper(update, context):
        await coin_menu(update, context)

    async def dex_wrapper(update, context):
        await dex_menu(update, context)

    async def coin_wrapper(update, context):
        await coin_menu(update, context)

    async def tokeninfo_wrapper(update, context):
        await update.message.reply_text(
            "🔍 برای اطلاعات توکن، ابتدا به منوی دکس بروید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")
            ]])
        )

    async def holders_wrapper(update, context):
        await update.message.reply_text(
            "👥 برای بررسی هولدرها، ابتدا به منوی دکس بروید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")
            ]])
        )

    # اضافه کردن handlers
    app.add_handler(CommandHandler("dex", dex_wrapper))
    app.add_handler(CommandHandler("coin", coin_wrapper))
    app.add_handler(CommandHandler("trending", trending_wrapper))
    app.add_handler(CommandHandler("hotcoins", hotcoins_wrapper))
    app.add_handler(CommandHandler("tokeninfo", tokeninfo_wrapper))
    app.add_handler(CommandHandler("holders", holders_wrapper)) 
  
    async def holders_wrapper(update, context):
        await update.message.reply_text(
            "👥 برای بررسی هولدرها، ابتدا به منوی دکس بروید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")
            ]])
        )

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
