from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.coinstats_service import coinstats_service
from services.direct_api_service import direct_api_service
from services.holderscan_service import holderscan_service
from utils.crypto_formatter import (
    format_market_overview, format_error_message,
    format_token_info, format_trending_tokens, format_holders_info
)
from config.constants import (
    CRYPTO_MENU, DEX_MENU, COIN_MENU, DEX_SUBMENU, COIN_SUBMENU,
    MAIN_MENU
)
from database.operations import check_subscription, check_user_api_limit, log_api_request
import asyncio
from utils.helpers import format_token_price

async def crypto_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی رمزارز با اطلاعات بازار به‌روزرسانی شده"""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("⏳ در حال دریافت آمار بازار...")

    try:
        # دریافت اطلاعات از APIهای مختلف
        btc_dominance_data = coinstats_service.get_btc_dominance()
        fear_greed_data = coinstats_service.get_fear_and_greed()
        global_data = direct_api_service.coingecko_global()
        
        # فرمت کردن پیام
        message = "🪙 **منوی رمزارز**\n\n"
        
        # دامیننس بیتکوین
        if not btc_dominance_data.get("error"):
            btc_dom = btc_dominance_data.get("btcDominance", 0)
            message += f"₿ **دامیننس بیتکوین:** {btc_dom:.2f}%\n"
        
        # شاخص ترس و طمع
        if not fear_greed_data.get("error"):
            fear_greed = fear_greed_data.get("value", 0)
            fear_greed_text = fear_greed_data.get("valueClassification", "نامشخص")
            message += f"😱 **شاخص ترس و طمع:** {fear_greed} ({fear_greed_text})\n"
        
        # آمار کلی بازار
        if not global_data.get("error") and "data" in global_data:
            data = global_data["data"]
            total_market_cap = data.get("total_market_cap", {}).get("usd", 0)
            total_volume = data.get("total_volume", {}).get("usd", 0)
            market_cap_change = data.get("market_cap_change_percentage_24h_usd", 0)
            
            message += f"📊 **کل بازار:** ${total_market_cap:,.0f}\n"
            message += f"📈 **حجم 24ساعته:** ${total_volume:,.0f}\n"
            message += f"📉 **تغییر 24ساعته:** {market_cap_change:+.2f}%\n"
        
        message += "\n🔹 لطفاً یکی از گزینه‌ها را انتخاب کنید:"
        
        # دکمه‌های منو
        keyboard = [
            [InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")],
            [InlineKeyboardButton("💰 نارموون کوین", callback_data="narmoon_coin")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]

        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

    except Exception as e:
        print(f"Error in crypto_menu: {e}")
        error_message = "🪙 **منوی رمزارز**\n\nلطفاً یکی از گزینه‌ها را انتخاب کنید:"
        keyboard = [
            [InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")],
            [InlineKeyboardButton("💰 نارموون کوین", callback_data="narmoon_coin")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
        ]

        if query:
            await query.edit_message_text(
                error_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.message.reply_text(
                error_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

    return CRYPTO_MENU

async def dex_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی نارموون دکس"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    has_premium = check_subscription(user_id)

    dex_options = {
        'token_info': '🔍 اطلاعات توکن',
        'trending_tokens': '🔥 توکن های داغ', 
        'recently_updated': '🔄 توکن های آپدیت',
        'boosted_tokens': '🚀 توکن‌های تقویت‌شده',
        'token_snipers': '🎯 اسنایپرهای توکن',
        'token_holders': '👥 بررسی هولدرها',
    }

    keyboard = [
    [
        InlineKeyboardButton("🔍 اطلاعات توکن", callback_data="dex_token_info"),
        InlineKeyboardButton("🔥 توکن های داغ", callback_data="dex_trending_tokens")
    ],
    [
        InlineKeyboardButton("🔄 توکن‌های آپدیت", callback_data="dex_recently_updated"),
        InlineKeyboardButton("🚀 توکن‌های تقویت‌شده", callback_data="dex_boosted_tokens")
    ],
    [
        InlineKeyboardButton("🎯 اسنایپرهای توکن", callback_data="dex_token_snipers"),
        InlineKeyboardButton("👥 بررسی هولدر ها", callback_data="dex_token_holders")
    ],
    [InlineKeyboardButton("🔙 بازگشت", callback_data="crypto")]
] 

    await query.edit_message_text(
        "🔄 **نارموون دکس**\n\n"
        "تحلیل تخصصی توکن‌های DEX سولانا\n\n"
        "لطفاً یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return DEX_MENU

async def coin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی نارموون کوین"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    has_premium = check_subscription(user_id)

    coin_options = {
        'general_search': '🔎 جستجوی کوین ها',
        'trending_coins': '🔥 کوین های داغ',
        'global_stats': '🌍 آمار جهانی کریپتو',
        'defi_stats': '🏦 آمار DeFi',
        'companies_treasury': '🏢 ذخایر شرکت‌ها'
    }

    keyboard = [
        [InlineKeyboardButton("🔎 جستجوی کوین ها", callback_data="coin_general_search")],
        [
            InlineKeyboardButton("🔥 کوین های داغ", callback_data="coin_trending_coins"),
            InlineKeyboardButton("🌍 آمار جهانی کریپتو", callback_data="coin_global_stats")
        ],
        [
            InlineKeyboardButton("🏦 آمار DeFi", callback_data="coin_defi_stats"),
            InlineKeyboardButton("🏢 ذخایر شرکت‌ها", callback_data="coin_companies_treasury")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="crypto")]
    ]

    await query.edit_message_text(
        "💰 **نارموون کوین**\n\n"
        "تحلیل تخصصی کوین‌های معتبر و بازارهای متمرکز\n\n"
        "لطفاً یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return COIN_MENU

async def handle_dex_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش گزینه‌های منوی دکس"""
    query = update.callback_query
    await query.answer()

    option = query.data.replace("dex_", "")
    user_id = update.effective_user.id
    has_premium = check_subscription(user_id)

    # بررسی دسترسی - همه قابلیت‌ها آزاد شد
    # premium_required = option in ['token_info', 'token_snipers', 'token_holders'] 
    # if not has_premium and premium_required:
    #     await query.answer("⚠️ این قابلیت نیاز به اشتراک دارد", show_alert=True)
    #     return DEX_MENU

    # بررسی محدودیت API
    if not check_user_api_limit(user_id, has_premium):
        await query.edit_message_text(
            "⚠️ محدودیت روزانه درخواست‌های شما به پایان رسیده است.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="narmoon_dex")
            ]])
        )
        return DEX_MENU

    await query.edit_message_text("⏳ در حال دریافت اطلاعات...")

    try:
        log_api_request(user_id, f"dex_{option}")

        if option == 'token_info':
            context.user_data['waiting_for'] = 'token_address'
            context.user_data['action_type'] = 'token_info'
            
            await query.edit_message_text(
                "🔍 **اطلاعات توکن**\n\n"
                "لطفاً آدرس قرارداد توکن سولانا را ارسال کنید:\n\n"
                "مثال: `7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr`\n\n"
                "برای لغو: /cancel",
            )
            return DEX_SUBMENU

        elif option == 'trending_tokens':
            # نمایش زیر منو های توکن های داغ
            keyboard = [
                [InlineKeyboardButton("🌍 همه شبکه‌ها", callback_data="trending_all_networks")],
                [InlineKeyboardButton("🔗 سولانا فقط", callback_data="trending_solana_only")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="narmoon_dex")]
            ]
            
            await query.edit_message_text(
                "🔥 **توکن های داغ**\n\n"
                "لطفاً یکی از گزینه‌ها را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return DEX_MENU

        elif option == 'recently_updated':
            data = direct_api_service.geckoterminal_recently_updated()
            message = format_recently_updated_tokens(data)
            
        elif option == 'boosted_tokens':
            data = direct_api_service.dexscreener_boosted_tokens()
            message = format_boosted_tokens(data)
            
        elif option == 'token_snipers':
            context.user_data['waiting_for'] = 'pair_address'
            context.user_data['action_type'] = 'token_snipers'
            
            await query.edit_message_text(
                "🎯 **اسنایپرهای توکن**\n\n"
                "لطفاً آدرس جفت (Pair Address) را ارسال کنید:\n\n"
                "برای لغو: /cancel",
            )
            return DEX_SUBMENU
            
        elif option == 'token_holders':
            context.user_data['waiting_for'] = 'token_contract'
            context.user_data['action_type'] = 'token_holders'
            
            await query.edit_message_text(
                "👥 **بررسی هولدرها**\n\n"
                "لطفاً آدرس قرارداد توکن سولانا را ارسال کنید:\n\n"
                "مثال: `7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr`\n\n"
                "برای لغو: /cancel",
            )
            return DEX_SUBMENU

        else:
            message = "🚧 این بخش در حال توسعه است..."

        # دکمه بازگشت
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="narmoon_dex")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        print(f"Error in handle_dex_option: {e}")
        await query.edit_message_text(
            format_error_message("general"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="narmoon_dex")
            ]])
        )

    return DEX_MENU

async def handle_coin_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش گزینه‌های منوی کوین"""
    query = update.callback_query
    await query.answer()

    option = query.data.replace("coin_", "")
    user_id = update.effective_user.id
    has_premium = check_subscription(user_id)

    # بررسی دسترسی - همه قابلیت‌ها آزاد شد
    # free_features = ['general_search', 'trending_coins', 'global_stats']
    # if not has_premium and option not in free_features:
    #     await query.answer("⚠️ این قابلیت نیاز به اشتراک دارد", show_alert=True)
    #     return COIN_MENU

    # بررسی محدودیت API
    if not check_user_api_limit(user_id, has_premium):
        await query.edit_message_text(
            "⚠️ محدودیت روزانه درخواست‌های شما به پایان رسیده است.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="narmoon_coin")
            ]])
        )
        return COIN_MENU

    await query.edit_message_text("⏳ در حال دریافت اطلاعات...")

    try:
        log_api_request(user_id, f"coin_{option}")

        if option == 'general_search':
            context.user_data['waiting_for'] = 'search_query'
            context.user_data['action_type'] = 'general_search'
            
            await query.edit_message_text(
                "🔎 **جستجوی عمومی**\n\n"
                "لطفاً نام یا نماد کوین مورد نظر را وارد کنید:\n\n"
                "مثال: Bitcoin یا BTC\n\n"
                "برای لغو: /cancel",
            )
            return DEX_SUBMENU  # استفاده از همان state

        elif option == 'trending_coins':
            data = direct_api_service.coingecko_trending()
            message = format_trending_coins(data)
            
        elif option == 'global_stats':
            data = direct_api_service.coingecko_global()
            message = format_global_stats(data)
            
        elif option == 'defi_stats':
            data = direct_api_service.coingecko_defi()
            message = format_defi_stats(data)
            
        elif option == 'companies_treasury':
            # دکمه‌های انتخاب کوین
            keyboard = [
                [InlineKeyboardButton("₿ Bitcoin", callback_data="treasury_bitcoin")],
                [InlineKeyboardButton("Ξ Ethereum", callback_data="treasury_ethereum")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="narmoon_coin")]
            ]
            
            await query.edit_message_text(
                "🏢 **ذخایر شرکت‌ها**\n\n"
                "لطفاً کوین مورد نظر را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return COIN_MENU

        else:
            message = "🚧 این بخش در حال توسعه است..."

        # دکمه بازگشت
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="narmoon_coin")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        print(f"Error in handle_coin_option: {e}")
        await query.edit_message_text(
            format_error_message("general"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="narmoon_coin")
            ]])
        )

    return COIN_MENU

async def handle_trending_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
   """پردازش گزینه های توکن های داغ"""
   query = update.callback_query
   await query.answer()
           
   option = query.data
   await query.edit_message_text("⏳ در حال دریافت توکن‌های ترند...")
       
   try:
       if option == "trending_all_networks":
           data = direct_api_service.geckoterminal_trending_all()
           message = format_trending_all_networks(data)
       
       elif option == "trending_solana_only":
           # 🔍 DEBUG - اضافه شده موقتی
           print("🔍 DEBUG: Starting Solana trending...")
           
           # ترکیب داده‌ها از GeckoTerminal و Moralis
           combined_data = await direct_api_service.get_combined_solana_trending()
           
           # 🔍 DEBUG - اضافه شده موقتی  
           print(f"🔍 DEBUG: Got {len(combined_data.get('combined_tokens', []))} tokens")
           
           message = format_combined_solana_trending(combined_data)
           
           # 🔍 DEBUG - اضافه شده موقتی
           print(f"🔍 DEBUG: Message length = {len(message)} characters")
           print(f"🔍 DEBUG: Over limit? {len(message) > 4096}")
           if len(message) > 4000:
               print(f"🔍 DEBUG: First 100 chars: {message[:100]}")
               print(f"🔍 DEBUG: Last 100 chars: {message[-100:]}")
           
       # دکمه بازگشت
       keyboard = [[InlineKeyboardButton("🔙 بازگشت به دکس", callback_data="narmoon_dex")]]
           
       await query.edit_message_text(
           message,
           reply_markup=InlineKeyboardMarkup(keyboard),
       )
       
   except Exception as e:
       print(f"Error in handle_trending_options: {e}")
       # 🔍 DEBUG - اضافه شده موقتی
       print(f"🔍 DEBUG: Error type: {type(e).__name__}")
       if 'message' in locals():
           print(f"🔍 DEBUG: Message length when error occurred: {len(message)}")
       
       await query.edit_message_text(
           format_error_message("general"),
           reply_markup=InlineKeyboardMarkup([[
               InlineKeyboardButton("🔙 بازگشت", callback_data="narmoon_dex")
           ]])  
       )
               
   return DEX_MENU

async def handle_treasury_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش گزینه‌های ذخایر شرکت‌ها"""
    query = update.callback_query
    await query.answer()

    coin_id = query.data.replace("treasury_", "")
    await query.edit_message_text("⏳ در حال دریافت اطلاعات ذخایر...")

    try:
        data = direct_api_service.coingecko_companies_treasury(coin_id)
        message = format_companies_treasury(data, coin_id)

        keyboard = [[InlineKeyboardButton("🔙 بازگشت به کوین", callback_data="narmoon_coin")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        print(f"Error in handle_treasury_options: {e}")
        await query.edit_message_text(
            format_error_message("general"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="narmoon_coin")
            ]])
        )

    return COIN_MENU

async def process_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش ورودی‌های کاربر"""
    waiting_for = context.user_data.get('waiting_for')
    action_type = context.user_data.get('action_type')
    
    if not waiting_for or not action_type:
        return DEX_SUBMENU

    user_input = update.message.text.strip()
    await update.message.reply_text("🔍 در حال پردازش...")

    try:
        if action_type == 'token_info':
            # اطلاعات توکن از GeckoTerminal
            data = direct_api_service.geckoterminal_token_info("solana", user_input)
            message = format_token_info_enhanced(data)
            
        elif action_type == 'token_snipers':
            # اسنایپرهای توکن از Moralis
            data = direct_api_service.moralis_snipers(user_input)
            message = format_snipers_info(data)
            
        elif action_type == 'token_holders':
            # اطلاعات هولدرها
            await update.message.reply_text("⏳ در حال دریافت اطلاعات هولدرها...")
            try:
                holders_data = holderscan_service.token_holders(user_input, limit=20)
                
                # بررسی خطای 404
                if holders_data.get("error") and holders_data.get("status_code") == 404:
                    # پیام خطای دوستانه
                    message = (
                        "❌ **توکن مورد نظر پشتیبانی نمی‌شود**\n\n"
                        f"توکن `{user_input}` در دیتابیس HolderScan یافت نشد.\n\n"
                        "**توکن‌های پشتیبانی شده:**\n"
                        "• BONK: `DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263`\n"
                        "• WIF: `EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm`\n"
                        "• JUP: `JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN`\n"
                        "• PYTH: `HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3`\n"
                        "• ORCA: `orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE`\n\n"
                        "💡 **نکته:** برای توکن‌های دیگر، از گزینه «تحلیل توکن» استفاده کنید."
                    )
                elif holders_data.get("error"):
                    # سایر خطاها
                    message = f"❌ خطا در دریافت اطلاعات: {holders_data.get('error')}"
                else:
                    # موفقیت - دریافت سایر داده‌ها
                    stats_data = holderscan_service.token_stats(user_input)
                    deltas_data = holderscan_service.holder_deltas(user_input)
                    
                    # فرمت کردن پیام
                    message = format_holders_info_enhanced(holders_data, stats_data, deltas_data, user_input)
            except Exception as e:
                print(f"Error in holders processing: {e}")
                message = f"❌ خطا در دریافت اطلاعات هولدرها: {str(e)}"
            
        elif action_type == 'general_search':
            # جستجوی عمومی از CoinGecko
            data = direct_api_service.coingecko_search(user_input)
            message = format_search_results(data)

        else:
            message = "❌ نوع عملیات شناسایی نشد."

        # دکمه‌های بازگشت
        if action_type in ['token_info', 'token_snipers', 'token_holders']:
            back_button = "narmoon_dex"
        else:
            back_button = "narmoon_coin"
            
        keyboard = [
            [InlineKeyboardButton(f"🔙 بازگشت", callback_data=back_button)]
        ]

        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        # پاک کردن وضعیت
        context.user_data.clear()
        return CRYPTO_MENU

    except Exception as e:
        print(f"Error in process_user_input: {e}")
        await update.message.reply_text(
            format_error_message("general"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="crypto")
            ]])
        )
        context.user_data.clear()
        return CRYPTO_MENU

# === Helper Functions for Formatting ===

def format_token_info_enhanced(data):
    """فرمت کردن اطلاعات کامل توکن - نسخه کاملتر"""
    if data.get("error") or "data" not in data:
        return "❌ خطا در دریافت اطلاعات توکن."

    token_data = data["data"]
    attributes = token_data.get("attributes", {})
    pools_data = data.get("pools_data", {})  # داده‌های pool

    message = "🔍 **اطلاعات کامل توکن**\n\n"

    # اطلاعات پایه
    name = attributes.get("name", "نامشخص")
    symbol = attributes.get("symbol", "نامشخص")
    address = attributes.get("address", "نامشخص")
    categories = attributes.get("categories", [])

    message += f"**📋 مشخصات پایه:**\n"
    message += f"• نام: **{name}**\n"
    message += f"• نماد: **{symbol}**\n"
    message += f"• آدرس: `{address}`\n"
    message += f"• شبکه: **Solana**\n"
    if categories:
        cats_text = ", ".join(categories)
        message += f"• دسته‌بندی: **{cats_text}**\n"
    message += "\n"

    # اطلاعات مالی (از pools_data)
    if pools_data:
        message += f"**💰 اطلاعات مالی:**\n"
        
        # قیمت
        price_usd = pools_data.get("base_token_price_usd") or pools_data.get("token_price_usd")
        if price_usd:
            try:
                price_val = float(price_usd)
                if price_val < 0.000001:
                    formatted_price = f"${price_val:.10f}"
                elif price_val < 0.01:
                    formatted_price = f"${price_val:.6f}"
                else:
                    formatted_price = f"${price_val:,.4f}"
                message += f"• قیمت فعلی: **{formatted_price}**\n"
            except:
                message += f"• قیمت فعلی: **{format_token_price(price_usd)}**\n"

        # مارکت کپ
        market_cap = pools_data.get("market_cap_usd")
        if market_cap:
            try:
                mc_val = float(market_cap)
                if mc_val >= 1000000000:
                    market_cap_formatted = f"${mc_val/1000000000:.2f}B"
                elif mc_val >= 1000000:
                    market_cap_formatted = f"${mc_val/1000000:.2f}M"
                elif mc_val >= 1000:
                    market_cap_formatted = f"${mc_val/1000:.2f}K"
                else:
                    market_cap_formatted = f"${mc_val:,.0f}"
                message += f"• مارکت کپ: **{market_cap_formatted}**\n"
            except:
                pass

        # FDV
        fdv = pools_data.get("fdv_usd")
        if fdv:
            try:
                fdv_val = float(fdv)
                if fdv_val >= 1000000000:
                    fdv_formatted = f"${fdv_val/1000000000:.2f}B"
                elif fdv_val >= 1000000:
                    fdv_formatted = f"${fdv_val/1000000:.2f}M"
                elif fdv_val >= 1000:
                    fdv_formatted = f"${fdv_val/1000:.2f}K"
                else:
                    fdv_formatted = f"${fdv_val:,.0f}"
                message += f"• FDV: **{fdv_formatted}**\n"
            except:
                pass

        # حجم معاملات
        volume_24h = pools_data.get("volume_usd", {}).get("h24")
        if volume_24h:
            try:
                vol_val = float(volume_24h)
                if vol_val >= 1000000:
                    volume_formatted = f"${vol_val/1000000:.2f}M"
                elif vol_val >= 1000:
                    volume_formatted = f"${vol_val/1000:.2f}K"
                else:
                    volume_formatted = f"${vol_val:,.0f}"
                message += f"• حجم 24ساعته: **{volume_formatted}**\n"
            except:
                pass

        # نقدینگی
        liquidity = pools_data.get("reserve_in_usd")
        if liquidity:
            try:
                liq_val = float(liquidity)
                if liq_val >= 1000000:
                    liquidity_formatted = f"${liq_val/1000000:.2f}M"
                elif liq_val >= 1000:
                    liquidity_formatted = f"${liq_val/1000:.2f}K"
                else:
                    liquidity_formatted = f"${liq_val:,.0f}"
                message += f"• نقدینگی: **{liquidity_formatted}**\n"
            except:
                pass

        # تغییرات قیمت
        price_changes = pools_data.get("price_change_percentage", {})
        if price_changes:
            message += f"• تغییر 24س: "
            change_24h = price_changes.get("h24")
            if change_24h is not None:
                try:
                    change = float(change_24h)
                    emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
                    message += f"{emoji} **{change:+.2f}%**\n"
                except:
                    message += "**N/A**\n"
            else:
                message += "**N/A**\n"
        
        message += "\n"

    # اطلاعات هولدرها
    holders_info = attributes.get("holders", {})
    if holders_info:
        message += f"**👥 اطلاعات هولدرها:**\n"
        
        holders_count = holders_info.get("count")
        if holders_count:
            message += f"• کل هولدرها: **{holders_count:,} نفر**\n"
        
        distribution = holders_info.get("distribution_percentage", {})
        if distribution:
            top_10 = distribution.get("top_10")
            if top_10:
                message += f"• 10 نفر اول: **{top_10}%**\n"
            
            rest = distribution.get("rest")
            if rest:
                message += f"• بقیه: **{rest}%**\n"
        
        message += "\n"

    # امنیت
    mint_auth = attributes.get("mint_authority")
    freeze_auth = attributes.get("freeze_authority")
    gt_score = attributes.get("gt_score")
    
    if mint_auth is not None or freeze_auth is not None or gt_score is not None:
        message += f"**🔒 امنیت:**\n"
        
        if mint_auth is not None:
            mint_text = "خیر ✅" if mint_auth == "no" else "بله ⚠️"
            message += f"• Mint Authority: **{mint_text}**\n"
        
        if freeze_auth is not None:
            freeze_text = "خیر ✅" if freeze_auth == "no" else "بله ⚠️"
            message += f"• Freeze Authority: **{freeze_text}**\n"
        
        if gt_score is not None:
            try:
                score = float(gt_score)
                score_emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
                message += f"• GT Score: **{score:.0f}/100** {score_emoji}\n"
            except:
                pass
        
        message += "\n"

    # فعالیت 24 ساعته (از pools_data)
    if pools_data:
        transactions = pools_data.get("transactions", {}).get("h24", {})
        if transactions:
            message += f"**⚡ فعالیت 24ساعته:**\n"
            
            buys = transactions.get("buys", 0)
            sells = transactions.get("sells", 0)
            total_txs = buys + sells
            
            if total_txs > 0:
                if total_txs >= 1000:
                    message += f"• معاملات: **{total_txs/1000:.1f}K**\n"
                else:
                    message += f"• معاملات: **{total_txs:,}**\n"
            
            buyers = transactions.get("buyers", 0)
            sellers = transactions.get("sellers", 0)
            total_traders = buyers + sellers
            
            if total_traders > 0:
                if total_traders >= 1000:
                    message += f"• معامله‌گران: **{total_traders/1000:.1f}K نفر**\n"
                else:
                    message += f"• معامله‌گران: **{total_traders:,} نفر**\n"
            
            message += "\n"

    # لینک‌های اجتماعی
    websites = attributes.get("websites", [])
    twitter = attributes.get("twitter_handle")
    telegram = attributes.get("telegram_handle")
    
    if websites or twitter or telegram:
        message += f"**📱 لینک‌ها:**\n"
        
        if websites:
            for website in websites[:2]:  # حداکثر 2 وبسایت
                message += f"• وبسایت: {website}\n"
        
        if telegram:
            message += f"• تلگرام: @{telegram}\n"
        
        if twitter:
            message += f"• توییتر: @{twitter}\n"
        
        message += "\n"

    # سن توکن
    pool_created_at = pools_data.get("pool_created_at") if pools_data else None
    if pool_created_at:
        try:
            from datetime import datetime, timezone
            created_time = datetime.fromisoformat(pool_created_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age = now - created_time

            message += f"**🕐 سن توکن:**\n"
            if age.days > 0:
                message += f"• سن: **{age.days} روز**\n"
            elif age.seconds > 3600:
                hours = age.seconds // 3600
                message += f"• سن: **{hours} ساعت**\n"
            else:
                minutes = age.seconds // 60
                message += f"• سن: **{minutes} دقیقه**\n"
        except:
            pass

    return message

def format_recently_updated_tokens(data):
    """فرمت کردن توکن های آپدیت"""
    if isinstance(data, dict) and data.get("error"):
        return "❌ خطا در دریافت اطلاعات توکن های آپدیت."
    
    message = "🔄 **توکن‌های آپدیت**\n\n"
    
    # بررسی ساختار داده
    tokens = []
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], dict) and "tokens" in data["data"]:
            tokens = data["data"]["tokens"]
        elif "data" in data and isinstance(data["data"], list):
            tokens = data["data"]
        elif "tokens" in data:
            tokens = data["tokens"]
    elif isinstance(data, list):
        tokens = data
    
    if not tokens:
        return "❌ هیچ توکن به‌روزرسانی شده‌ای یافت نشد."
    
    for i, token in enumerate(tokens[:15], 1):
        if isinstance(token, dict):
            attributes = token.get("attributes", {})
            name = attributes.get("name", "نامشخص")
            symbol = attributes.get("symbol", "نامشخص")
            address = attributes.get("address", "")
            
            message += f"{i}. **{name}** ({symbol})\n"
            message += f"   🌐 شبکه: Solana\n"
            
            # آدرس کامل قابل کپی
            if address:
                message += f"   📍 آدرس: `{address}`\n"
            
            # اضافه کردن قیمت در صورت وجود
            price = attributes.get("price_usd")
            if price:
                try:
                    price_val = float(price)
                    if price_val < 0.000001:
                        formatted_price = f"${price_val:.10f}"
                    elif price_val < 0.01:
                        formatted_price = f"${price_val:.6f}"
                    else:
                        formatted_price = f"${price_val:,.4f}"
                    message += f"   💰 قیمت: {formatted_price}\n"
                except:
                    message += f"   💰 قیمت: {format_token_price(price)}\n"
            
            message += "\n"
    
    return message

def format_boosted_tokens(data):
    """فرمت کردن توکن‌های تقویت‌شده - نام بهتر"""
    if not isinstance(data, list) or not data:
        return "❌ هیچ توکن تقویت‌شده‌ای یافت نشد."
    
    message = "🚀 **توکن‌های تقویت‌شده**\n\n"
    
    tokens = data[:15]
    for i, token in enumerate(tokens, 1):
        # استخراج بهتر نام توکن
        token_name = "نامشخص"
        token_symbol = "نامشخص"
        token_address = token.get("tokenAddress", "")
        description = token.get("description", "")
        
        # تلاش برای استخراج نام از description
        if description:
            # جستجو برای نام در ابتدای توضیحات
            words = description.split()
            
            # ابتدا دنبال $ باشیم
            for word in words[:10]:
                if word.startswith("$") and len(word) > 1 and word[1:].replace(".", "").replace(",", "").isalpha():
                    token_name = word
                    token_symbol = word[1:].upper()
                    break
            
            # اگر پیدا نشد، دنبال کلمات بزرگ باشیم
            if token_name == "نامشخص":
                for word in words[:5]:
                    if word.isupper() and len(word) > 2 and len(word) < 15 and word.isalpha():
                        token_name = word
                        token_symbol = word
                        break
            
            # اگر باز پیدا نشد، اولین کلمه بزرگ
            if token_name == "نامشخص":
                for word in words[:3]:
                    if word[0].isupper() and len(word) > 2 and len(word) < 20 and word.isalpha():
                        token_name = word
                        token_symbol = word[:8].upper()
                        break
        
        # اگر نام پیدا نشد، از آدرس استفاده کن
        if token_name == "نامشخص" and token_address:
            token_name = token_address[:8] + "..."
            token_symbol = token_address[:6].upper()
        
        message += f"{i}. **{token_name}** ({token_symbol})\n"
        message += f"   🌐 شبکه: Solana\n"
        
        # آدرس قابل کپی
        if token_address:
            message += f"   📍 آدرس: `{token_address}`\n"
        
        # توضیحات کوتاه
        if description:
            short_desc = description[:80] + "..." if len(description) > 80 else description
            message += f"   📝 {short_desc}\n"
        
        message += "\n"
    
    return message

def format_trending_all_networks(data):
    """فرمت کردن توکن های داغ همه شبکه ها - بهبود یافته"""
    if isinstance(data, dict) and data.get("error"):
        return "❌ خطا در دریافت توکن‌های ترند."
    
    message = "🌍 **توکن های داغ همه شبکه ها**\n\n"
    
    # بررسی ساختار داده
    pools = []
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], dict) and "pools" in data["data"]:
            pools = data["data"]["pools"]
        elif "data" in data and isinstance(data["data"], list):
            pools = data["data"]
        elif "pools" in data:
            pools = data["pools"]
    elif isinstance(data, list):
        pools = data
    
    if not pools:
        return "❌ هیچ توکن ترندی یافت نشد."
    
    for i, pool in enumerate(pools[:15], 1):
        if isinstance(pool, dict):
            attributes = pool.get("attributes", {})
            base_token = attributes.get("base_token", {})
            
            # استخراج نام و نماد
            name = base_token.get("name", "نامشخص")
            symbol = base_token.get("symbol", "نامشخص")
            # پاک کردن کاراکترهای خاص
            name = name.replace("*", "").replace("_", "").replace("[", "").replace("]", "")
            symbol = symbol.replace("*", "").replace("_", "").replace("[", "").replace("]", "")

            # پاک کردن کاراکترهای خاص
            name = name.replace("*", "").replace("_", "").replace("[", "").replace("]", "")
            symbol = symbol.replace("*", "").replace("_", "").replace("[", "").replace("]", "")

            # اگر نام یا نماد خالی باشد، از pool name استفاده کن
            if not name or name == "نامشخص":
                pool_name = attributes.get("name", f"توکن_{i}")
                if " / " in pool_name:
                    name = pool_name.split(" / ")[0]
                else:
                    name = pool_name
            
            if not symbol or symbol == "نامشخص":
                if " / " in attributes.get("name", ""):
                    symbol = attributes.get("name", "").split(" / ")[0][:10]
                else:
                    symbol = name[:6] if name != "نامشخص" else f"TKN{i}"
            
            # استخراج شبکه
            network = "نامشخص"
            token_address = ""
            if "relationships" in pool:
                # شبکه
                dex_data = pool.get("relationships", {}).get("dex", {}).get("data", {})
                network = dex_data.get("id", "نامشخص")
                
                # آدرس توکن
                base_token_data = pool.get("relationships", {}).get("base_token", {}).get("data", {})
                if "id" in base_token_data:
                    token_id = base_token_data["id"]
                    # حذف prefix شبکه از آدرس
                    if "_" in token_id:
                        token_address = token_id.split("_", 1)[1]
                    else:
                        token_address = token_id
            
            # قیمت و تغییرات - با تبدیل ایمن
            price_change_raw = attributes.get("price_change_percentage", {}).get("h24", 0)
            try:
                price_change = float(price_change_raw) if price_change_raw else 0.0
            except (ValueError, TypeError):
                price_change = 0.0
            
            price = attributes.get("base_token_price_usd", "0")
            
            # حجم - با تبدیل ایمن
            volume_raw = attributes.get("volume_usd", {}).get("h24", 0)
            try:
                volume = float(volume_raw) if volume_raw else 0.0
            except (ValueError, TypeError):
                volume = 0.0
            
            message += f"{i}. **{name}** ({symbol})\n"
            message += f"   🌐 شبکه: {network}\n"
            message += f"   💰 قیمت: {format_token_price(price)}\n"
            message += f"   📈 تغییر 24س: {price_change:+.2f}%\n"
            if volume > 0:
                message += f"   📊 حجم: ${volume:,.0f}\n"
            if token_address:
                message += f"   📍 آدرس: `{token_address}`\n"
            message += "\n"
    
    return message

def format_combined_solana_trending(data):
    """فرمت کردن توکن های داغ سولانا ترکیبی - با آدرس"""
    if not data.get("success"):
        return "❌ خطا در دریافت توکن‌های ترند سولانا."
    
    message = "🔗 **توکن های داغ سولانا**\n\n"
    
    tokens = data.get("combined_tokens", [])[:15]
    for i, token in enumerate(tokens, 1):
        name = token.get("name", "نامشخص")
        symbol = token.get("symbol", "نامشخص")
        source = token.get("source", "نامشخص")
        
        # استخراج آدرس کامل
        token_address = token.get("address", "")
        
        # تبدیل ایمن price_change به float
        try:
            price_change = float(token.get("price_change_24h", 0))
        except (ValueError, TypeError):
            price_change = 0.0
        
        # قیمت
        price = token.get("price_usd", "0")
        
        # حجم
        volume = token.get("volume_24h", 0)
        
        message += f"{i}. **{name}** ({symbol})\n"
        message += f"   🌐 شبکه: Solana\n"
        message += f"   📊 منبع: {source}\n"
        message += f"   💰 قیمت: {format_token_price(price)}\n"
        message += f"   📈 تغییر 24س: {price_change:+.2f}%\n"
        
        # اضافه کردن حجم
        if volume and volume > 0:
            try:
                vol_val = float(volume)
                if vol_val >= 1000000:
                    message += f"   📊 حجم: ${vol_val/1000000:.1f}M\n"
                elif vol_val >= 1000:
                    message += f"   📊 حجم: ${vol_val/1000:.1f}K\n"
                else:
                    message += f"   📊 حجم: ${vol_val:.0f}\n"
            except:
                message += f"   📊 حجم: ${volume}\n"

        # ⭐ اطلاعات جدید - نقدینگی
        liquidity = token.get("liquidity_usd", "0")
        if liquidity and liquidity != "0":
            try:
                liq_val = float(liquidity)
                if liq_val >= 1000000:
                    message += f"   💧 نقدینگی: ${liq_val/1000000:.1f}M\n"
                elif liq_val >= 1000:
                    message += f"   💧 نقدینگی: ${liq_val/1000:.1f}K\n"
                else:
                    message += f"   💧 نقدینگی: ${liq_val:.0f}\n"
            except:
                pass
        
        # ⭐ سن توکن
        pool_created = token.get("pool_created_at", "")
        if pool_created:
            try:
                from datetime import datetime, timezone
                created_time = datetime.fromisoformat(pool_created.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age = now - created_time
                
                if age.days > 0:
                    message += f"   🕐 سن: {age.days} روز\n"
                elif age.seconds > 3600:
                    hours = age.seconds // 3600
                    message += f"   🕐 سن: {hours} ساعت\n"
                else:
                    minutes = age.seconds // 60
                    message += f"   🕐 سن: {minutes} دقیقه\n"
            except:
                pass
        
        # ⭐ تعداد معاملات 24 ساعته
        transactions = token.get("transactions_24h", {})
        if transactions:
            try:
                total_buys = transactions.get("buys", 0)
                total_sells = transactions.get("sells", 0)
                total_txs = total_buys + total_sells
                if total_txs > 0:
                    if total_txs >= 1000:
                        message += f"   ⚡ معاملات: {total_txs/1000:.1f}K (24س)\n"
                    else:
                        message += f"   ⚡ معاملات: {total_txs} (24س)\n"
            except:
                pass
        
        # ⭐ تعداد معامله‌گران
        if transactions:
            try:
                buyers = transactions.get("buyers", 0)
                sellers = transactions.get("sellers", 0)
                total_traders = buyers + sellers
                if total_traders > 0:
                    if total_traders >= 1000:
                        message += f"   👥 معامله‌گران: {total_traders/1000:.1f}K نفر\n"
                    else:
                        message += f"   👥 معامله‌گران: {total_traders} نفر\n"
            except:
                pass
        
        # اضافه کردن آدرس کامل قابل کپی
        if token_address and len(token_address) > 10 and not token_address.startswith(("sample", "fallback")):
            message += f"   📍 آدرس: `{token_address}`\n"
        
        message += "\n"
    
    message += f"📈 **مجموع:** {len(tokens)} توکن از {tokens[0].get('source', 'GeckoTerminal') if tokens else 'GeckoTerminal'}\n"
    
    return message

def format_holders_info_enhanced(holders_data, stats_data, deltas_data, token_address):
    """فرمت کردن اطلاعات هولدرها - نسخه کاملتر"""
    message = "👥 **اطلاعات کامل هولدرهای توکن**\n\n"
    
    # اطلاعات توکن
    message += f"📍 **آدرس توکن:** `{token_address}`\n\n"
    
    # آمار کلی بهبود یافته
    if not stats_data.get("error") and isinstance(stats_data, dict):
        message += "**📊 آمار کلی:**\n"
        
        # تعداد کل هولدرها
        if not holders_data.get("error") and "holder_count" in holders_data:
            total_holders = holders_data.get("holder_count", 0)
            message += f"• کل هولدرها: **{total_holders:,}**\n"
        
        # آمار تمرکز
        hhi = stats_data.get("hhi")
        if hhi is not None:
            concentration_level = "بالا" if hhi > 0.15 else "متوسط" if hhi > 0.05 else "پایین"
            message += f"• شاخص تمرکز (HHI): **{hhi:.3f}** ({concentration_level})\n"
        
        gini = stats_data.get("gini")
        if gini is not None:
            inequality_level = "بالا" if gini > 0.8 else "متوسط" if gini > 0.5 else "پایین"
            message += f"• ضریب جینی: **{gini:.3f}** (نابرابری {inequality_level})\n"
        
        median_position = stats_data.get("median_holder_position")
        if median_position:
            formatted_median = f"{median_position:,}" if median_position >= 1000 else f"{median_position:.2f}"
            message += f"• میانه موجودی: **{formatted_median}**\n"
        
        avg_time_held = stats_data.get("avg_time_held")
        if avg_time_held:
            days = avg_time_held // 86400
            message += f"• میانگین مدت نگهداری: **{days} روز**\n"
        
        retention_rate = stats_data.get("retention_rate")
        if retention_rate:
            retention_level = "عالی" if retention_rate > 0.8 else "خوب" if retention_rate > 0.6 else "متوسط"
            message += f"• نرخ نگهداری: **{retention_rate*100:.1f}%** ({retention_level})\n"
        
        message += "\n"
    
    # تغییرات هولدرها بهبود یافته
    if not deltas_data.get("error") and isinstance(deltas_data, dict):
        message += "**📈 تغییرات هولدرها:**\n"
        
        periods = {
            "7days": "7 روز گذشته",
            "14days": "14 روز گذشته", 
            "30days": "30 روز گذشته"
        }
        
        for period, name in periods.items():
            if period in deltas_data:
                change = deltas_data[period]
                if change > 0:
                    emoji = "🟢"
                    trend = "افزایش"
                elif change < 0:
                    emoji = "🔴" 
                    trend = "کاهش"
                else:
                    emoji = "⚪"
                    trend = "ثابت"
                
                message += f"• {name}: {emoji} **{change:+,}** ({trend})\n"
        
        message += "\n"
    
    # بزرگترین هولدرها بهبود یافته
    if not holders_data.get("error") and "holders" in holders_data:
        message += "**🐋 بزرگترین هولدرها:**\n"
        holders = holders_data["holders"][:15]  # 15 تا بجای 10
        
        # محاسبه کل supply برای درصدگیری
        total_supply = sum(holder.get("amount", 0) for holder in holders_data.get("holders", []))
        
        for i, holder in enumerate(holders, 1):
            address = holder.get("address", "نامشخص")
            # نمایش 8 کاراکتر اول و 4 کاراکتر آخر
            if len(address) > 12:
                formatted_address = f"{address[:8]}...{address[-4:]}"
            else:
                formatted_address = address[:12] + "..."
            
            amount = holder.get("amount", 0)
            rank = holder.get("rank", i)
            
            # محاسبه درصد
            percentage = (amount / total_supply * 100) if total_supply > 0 else 0
            
            # تعیین نوع هولدر
            if percentage > 10:
                holder_type = "🐋 نهنگ"
            elif percentage > 1:
                holder_type = "🐬 دلفین"  
            elif percentage > 0.1:
                holder_type = "🐟 ماهی"
            else:
                holder_type = "🦐 میگو"
            
            message += f"{rank}. `{formatted_address}` {holder_type}\n"
            
            # فرمت موجودی
            if amount >= 1000000000000:
                formatted_amount = f"{amount/1000000000000:.2f}T"
            elif amount >= 1000000000:
                formatted_amount = f"{amount/1000000000:.2f}B"
            elif amount >= 1000000:
                formatted_amount = f"{amount/1000000:.2f}M"
            elif amount >= 1000:
                formatted_amount = f"{amount/1000:.2f}K"
            else:
                formatted_amount = f"{amount:,.0f}"
            
            message += f"   💰 موجودی: **{formatted_amount}**\n"
            message += f"   📊 درصد: **{percentage:.2f}%**\n\n"
        
        # خلاصه تحلیل
        message += "**🔍 تحلیل توزیع:**\n"
        top_5_percent = sum(holder.get("amount", 0) for holder in holders[:5]) / total_supply * 100 if total_supply > 0 else 0
        top_10_percent = sum(holder.get("amount", 0) for holder in holders[:10]) / total_supply * 100 if total_supply > 0 else 0
        
        message += f"• 5 هولدر برتر: **{top_5_percent:.1f}%** کل توکن‌ها\n"
        message += f"• 10 هولدر برتر: **{top_10_percent:.1f}%** کل توکن‌ها\n"
        
        # تحلیل تمرکز
        if top_5_percent > 50:
            message += "⚠️ **تمرکز بالا** - ریسک دامپینگ وجود دارد\n"
        elif top_5_percent > 30:
            message += "⚡ **تمرکز متوسط** - نیاز به مراقبت\n"
        else:
            message += "✅ **توزیع مناسب** - ریسک تمرکز پایین\n"
    
    return message

def format_trending_coins(data):
    """فرمت کردن کوین‌های ترند"""
    if data.get("error") or "coins" not in data:
        return "❌ خطا در دریافت کوین‌های ترند."
    
    message = "🔥 **کوین های داغ**\n\n"
    
    coins = data["coins"][:15]
    for i, coin_data in enumerate(coins, 1):
        item = coin_data.get("item", {})
        name = item.get("name", "نامشخص")
        symbol = item.get("symbol", "نامشخص").upper()
        market_cap_rank = item.get("market_cap_rank", "N/A")
        
        message += f"{i}. **{name}** ({symbol})\n"
        message += f"   📊 رنک: #{market_cap_rank}\n\n"
    
    return message

def format_global_stats(data):
    """فرمت کردن آمار جهانی"""
    if data.get("error") or "data" not in data:
        return "❌ خطا در دریافت آمار جهانی."
    
    stats = data["data"]
    message = "🌍 **آمار جهانی کریپتو**\n\n"
    
    # کل بازار
    total_market_cap = stats.get("total_market_cap", {}).get("usd", 0)
    message += f"💰 **کل بازار:** ${total_market_cap:,.0f}\n"
    
    # حجم معاملات
    total_volume = stats.get("total_volume", {}).get("usd", 0)
    message += f"📈 **حجم 24ساعته:** ${total_volume:,.0f}\n"
    
    # دامیننس
    btc_dominance = stats.get("market_cap_percentage", {}).get("btc", 0)
    eth_dominance = stats.get("market_cap_percentage", {}).get("eth", 0)
    message += f"₿ **دامیننس BTC:** {btc_dominance:.1f}%\n"
    message += f"Ξ **دامیننس ETH:** {eth_dominance:.1f}%\n"
    
    # تعداد کوین‌ها
    active_cryptocurrencies = stats.get("active_cryptocurrencies", 0)
    message += f"🪙 **کوین‌های فعال:** {active_cryptocurrencies:,}\n"
    
    # تغییر 24 ساعته
    market_cap_change = stats.get("market_cap_change_percentage_24h_usd", 0)
    message += f"📊 **تغییر 24ساعته:** {market_cap_change:+.2f}%\n"
    
    return message

def format_defi_stats(data):
    """فرمت کردن آمار DeFi - اصلاح شده"""
    if data.get("error") or "data" not in data:
        return "❌ خطا در دریافت آمار DeFi."
    
    stats = data["data"]
    message = "🏦 آمار DeFi\n\n"
    
    # کل بازار DeFi - اصلاح تبدیل string به float
    defi_market_cap = stats.get("defi_market_cap", 0)
    try:
        if isinstance(defi_market_cap, str):
            defi_market_cap = float(defi_market_cap.replace(",", ""))
        else:
            defi_market_cap = float(defi_market_cap)
        
        if defi_market_cap >= 1000000000:
            message += f"💎 کل بازار DeFi: ${defi_market_cap/1000000000:.2f}B\n"
        elif defi_market_cap >= 1000000:
            message += f"💎 کل بازار DeFi: ${defi_market_cap/1000000:.2f}M\n"
        else:
            message += f"💎 کل بازار DeFi: ${defi_market_cap:,.0f}\n"
    except (ValueError, TypeError):
        message += f"💎 کل بازار DeFi: نامشخص\n"
    
    # درصد از کل بازار - اصلاح
    defi_dominance_raw = stats.get("defi_to_eth_ratio", 0)
    try:
        if isinstance(defi_dominance_raw, str):
            defi_dominance = float(defi_dominance_raw) * 100
        else:
            defi_dominance = float(defi_dominance_raw) * 100
        message += f"📊 سهم از کل بازار: {defi_dominance:.2f}%\n"
    except (ValueError, TypeError):
        message += f"📊 سهم از کل بازار: نامشخص\n"
    
    # حجم معاملات DeFi - اصلاح
    trading_volume_raw = stats.get("trading_volume_24h", 0)
    try:
        if isinstance(trading_volume_raw, str):
            trading_volume = float(trading_volume_raw.replace(",", ""))
        else:
            trading_volume = float(trading_volume_raw)
        
        if trading_volume >= 1000000000:
            message += f"📈 حجم معاملات 24ساعته: ${trading_volume/1000000000:.2f}B\n"
        elif trading_volume >= 1000000:
            message += f"📈 حجم معاملات 24ساعته: ${trading_volume/1000000:.2f}M\n"
        else:
            message += f"📈 حجم معاملات 24ساعته: ${trading_volume:,.0f}\n"
    except (ValueError, TypeError):
        message += f"📈 حجم معاملات 24ساعته: نامشخص\n"
    
    return message

def format_companies_treasury(data, coin_id):
    """فرمت کردن ذخایر شرکت‌ها"""
    if data.get("error") or "companies" not in data:
        return f"❌ خطا در دریافت اطلاعات ذخایر {coin_id}."
    
    coin_name = "Bitcoin" if coin_id == "bitcoin" else "Ethereum"
    symbol = "BTC" if coin_id == "bitcoin" else "ETH"
    
    message = f"🏢 **ذخایر {coin_name} شرکت‌ها**\n\n"
    
    companies = data["companies"][:15]
    total_holdings = 0
    
    for i, company in enumerate(companies, 1):
        name = company.get("name", "نامشخص")
        holdings = company.get("total_holdings", 0)
        total_holdings += holdings
        
        message += f"{i}. **{name}**\n"
        message += f"   💰 {holdings:,.0f} {symbol}\n\n"
    
    message += f"📊 **مجموع ده شرکت برتر:** {total_holdings:,.0f} {symbol}\n"
    
    return message

def format_search_results(data):
    """فرمت کردن نتایج جستجو"""
    if data.get("error"):
        return "❌ خطا در جستجو."
    
    message = "🔎 **نتایج جستجو**\n\n"
    
    # کوین‌ها
    coins = data.get("coins", [])[:5]
    if coins:
        message += "**💰 کوین‌ها:**\n"
        for coin in coins:
            name = coin.get("name", "نامشخص")
            symbol = coin.get("symbol", "نامشخص")
            market_cap_rank = coin.get("market_cap_rank")
            
            message += f"• **{name}** ({symbol})"
            if market_cap_rank:
                message += f" - رنک #{market_cap_rank}"
            message += "\n"
        message += "\n"
    
    # صرافی‌ها
    exchanges = data.get("exchanges", [])[:3]
    if exchanges:
        message += "**🏪 صرافی‌ها:**\n"
        for exchange in exchanges:
            name = exchange.get("name", "نامشخص")
            message += f"• {name}\n"
        message += "\n"
    
    if not coins and not exchanges:
        message += "هیچ نتیجه‌ای یافت نشد."
    
    return message

def format_snipers_info(data):
    """فرمت کردن اطلاعات اسنایپرها"""
    if data.get("error"):
        return "❌ خطا در دریافت اطلاعات اسنایپرها."
    
    message = "🎯 **اسنایپرهای توکن**\n\n"
    
    if isinstance(data, list) and data:
        for i, sniper in enumerate(data[:15], 1):
            address = sniper.get("address", "نامشخص")[:8] + "..."
            amount = sniper.get("amount", 0)
            
            message += f"{i}. **آدرس:** {address}\n"
            message += f"   💰 مقدار: {amount}\n\n"
    else:
        message += "هیچ اسنایپری یافت نشد."
    
    return message
