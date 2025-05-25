"""
هندلرهای مستقل برای command ها که نیاز به callback_query ندارن
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from database.operations import get_subscription_status

async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای /start"""
    user = update.effective_user
    welcome_text = f"""
سلام {user.first_name} عزیز! 👋
من ربات تحلیل و معاملات کریپتو هستم.

🎯 با من می‌تونید:
• نمودارهای تکنیکال رو تحلیل کنید
• اطلاعات لحظه‌ای ارزها رو دریافت کنید
• توکن‌های ترندینگ رو پیدا کنید
• هولدرها و ترژری رو بررسی کنید

از منوی زیر شروع کنید:
"""
    
    keyboard = [
        [InlineKeyboardButton("🔮 محصولات", callback_data="products")],
        [InlineKeyboardButton("📊 تحلیل نمودار", callback_data="analyze_charts")],
        [InlineKeyboardButton("🪙 کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("🤖 ویژگی‌های AI", callback_data="ai_features")],
        [InlineKeyboardButton("❓ سوالات متداوال", callback_data="faq")],
        [InlineKeyboardButton("📖 راهنمای استفاده", callback_data="usage_guide")],
        [InlineKeyboardButton("📜 قوانین و مقررات", callback_data="terms")],
        [InlineKeyboardButton("💳 خرید اشتراک", callback_data="subscription_plans")],
        [InlineKeyboardButton("📞 ارتباط با پشتیبانی", callback_data="support")]
    ]
    
    await update.message.reply_text(
        welcome_text, 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای /analyze"""
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

async def handle_crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای /crypto"""
    keyboard = [
        [InlineKeyboardButton("🔄 نارموون دکس", callback_data="narmoon_dex")],
        [InlineKeyboardButton("🪙 نارموون کوین", callback_data="narmoon_coin")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    
    await update.message.reply_text(
        "🪙 منوی کریپتو - انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_dex_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای /dex"""
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

async def handle_coin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای /coin"""
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

async def handle_trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای /trending"""
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

async def handle_hotcoins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای /hotcoins"""
    await handle_coin_command(update, context)

async def handle_tokeninfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای /tokeninfo"""
    await update.message.reply_text(
        "🔍 برای دریافت اطلاعات توکن:\n\n"
        "1️⃣ ابتدا به منوی دکس بروید\n"
        "2️⃣ گزینه 'اطلاعات توکن' را انتخاب کنید\n"
        "3️⃣ آدرس توکن را ارسال کنید",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 رفتن به نارموون دکس", callback_data="narmoon_dex")
        ]])
    )

async def handle_holders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای /holders"""
    await update.message.reply_text(
        "👥 برای بررسی هولدرها:\n\n"
        "1️⃣ ابتدا به منوی دکس بروید\n"
        "2️⃣ گزینه 'تحلیل هولدرها' را انتخاب کنید\n"
        "3️⃣ آدرس توکن را ارسال کنید",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 رفتن به نارموون دکس", callback_data="narmoon_dex")
        ]])
    )

async def handle_subscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای /subscription"""
    plans_text = """
💳 پلن‌های اشتراک ربات

🔹 پلن ماهانه: 350,000 تومان  
🔹 پلن 3 ماهه: 850,000 تومان (19% تخفیف)
🔹 پلن 6 ماهه: 1,500,000 تومان (28% تخفیف)

✅ مزایای اشتراک:
• دسترسی به تمام ابزارهای تحلیل
• اطلاعات لحظه‌ای بازار
• آنالیز هولدرها و ترژری
• پشتیبانی اختصاصی

برای خرید با پشتیبانی تماس بگیرید.
"""
    
    keyboard = [
        [InlineKeyboardButton("📞 تماس با پشتیبانی", url="https://t.me/mmpouya")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    
    await update.message.reply_text(
        plans_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای /terms"""
    terms_text = """
📋 قوانین و مقررات استفاده از ربات

1️⃣ استفاده از خدمات:
• ربات صرفاً جهت کمک به تحلیل است
• مسئولیت تصمیمات معاملاتی با کاربر است

2️⃣ حساب کاربری:
• هر کاربر فقط یک حساب می‌تواند داشته باشد
• اشتراک‌گذاری حساب ممنوع است

3️⃣ پرداخت و اشتراک:
• پرداخت‌ها غیرقابل بازگشت هستند
• اشتراک از زمان فعالسازی محاسبه می‌شود

4️⃣ محدودیت‌ها:
• استفاده تجاری نیاز به مجوز دارد
• کپی‌برداری از محتوا ممنوع است

نسخه: 1.0 | تاریخ: 1403/01/01
"""
    
    await update.message.reply_text(
        terms_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
        ]])
    )

async def handle_faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر برای /faq"""
    faq_text = """
❓ سوالات متداول

1️⃣ ربات چگونه کار می‌کند؟
پاسخ: ربات با استفاده از هوش مصنوعی تصاویر چارت را تحلیل کرده و سیگنال‌های معاملاتی ارائه می‌دهد.

2️⃣ آیا نیاز به دانش تخصصی دارم؟
پاسخ: خیر، ربات به زبان ساده توضیح می‌دهد ولی آشنایی اولیه مفید است.

3️⃣ دقت تحلیل‌ها چقدر است؟
پاسخ: دقت به کیفیت تصویر و شرایط بازار بستگی دارد. همیشه با احتیاط معامله کنید.

4️⃣ چگونه اشتراک تهیه کنم؟
پاسخ: از طریق منوی اشتراک یا تماس با پشتیبانی.

5️⃣ آیا اطلاعات من محفوظ است؟
پاسخ: بله، تمام اطلاعات رمزنگاری شده ذخیره می‌شود.
"""
    
    await update.message.reply_text(
        faq_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
        ]])
    )

async def handle_support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندлر برای /support"""
    support_text = """
📞 ارتباط با پشتیبانی

🆔 آیدی پشتیبان: @mmpouya

⏰ ساعات پاسخگویی:
شنبه تا پنجشنبه: 9 صبح تا 9 شب
جمعه: 2 بعدازظهر تا 8 شب

📧 ایمیل: support.narmoon@gmail.com

لطفاً برای پیگیری سریع‌تر، شماره کاربری خود را ارسال کنید.
شماره کاربری شما: {}
""".format(update.effective_user.id)
    
    keyboard = [
        [InlineKeyboardButton("💬 ارسال پیام به پشتیبان", url="https://t.me/mmpouya")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    
    await update.message.reply_text(
        support_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
