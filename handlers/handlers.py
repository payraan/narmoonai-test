import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config.constants import (
    MAIN_MENU, SELECTING_MARKET, SELECTING_TIMEFRAME,
    SELECTING_STRATEGY, WAITING_IMAGES, PROCESSING_ANALYSIS,
    MARKETS, TIMEFRAMES, EXPECTED_TIMEFRAMES, STRATEGIES, STRATEGY_CATEGORIES
)
from config.settings import NARMOON_DEX_LINK, NARMOON_COIN_LINK, TUTORIAL_VIDEO_LINK, SOLANA_WALLETS
from database.operations import check_subscription, register_user, activate_subscription
from services.ai_service import analyze_chart_images
from utils.helpers import load_static_texts
# بارگزاری متن‌های ثابت
STATIC_TEXTS = load_static_texts()

# هندلرهای اصلی
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ربات و نمایش منوی اصلی"""
    # ریست وضعیت کاربر
    context.user_data.clear()
    
    # ثبت کاربر در دیتابیس
    user_id = update.effective_user.id
    username = update.effective_user.username
    register_user(user_id, username)
    
   # ایجاد منوی اصلی
    main_menu_buttons = [
        [InlineKeyboardButton("📊 تحلیل نمودارها", callback_data="analyze_charts")],
        [InlineKeyboardButton("🪙 رمزارز", callback_data="crypto")],
        [
        InlineKeyboardButton("📚 راهنمای استفاده", callback_data="guide"),
        InlineKeyboardButton("🛒 محصولات نارموون", callback_data="narmoon_products")
        ],
        [InlineKeyboardButton("💳 خرید اشتراک", callback_data="subscription")],
        [InlineKeyboardButton("🧠 قابلیت‌های دستیار هوش مصنوعی", callback_data="ai_features")],
        [
        InlineKeyboardButton("❓ سوالات متداول", callback_data="faq"),
        InlineKeyboardButton("📜 قوانین و مقررات", callback_data="terms")
        ],
        [InlineKeyboardButton("👨‍💻 ارتباط با پشتیبانی", callback_data="support")]
        ]
    
    main_menu_markup = InlineKeyboardMarkup(main_menu_buttons)
    
    # دریافت نام کاربر برای شخصی‌سازی پیام
    user_name = update.effective_user.first_name if update.effective_user.first_name else "کاربر"
    
    welcome_text = f"""
سلام {user_name} عزیز! 👋✨ به دستیار هوش مصنوعی معامله‌گری **نارموون** خوش اومدی!

🚀 اینجا می‌تونی:
- بازارهای مالی رو با قدرت هوش مصنوعی تحلیل کنی
- آمار لحظه‌ای رمزارزها رو ببینی
- سیگنال بگیری و همیشه یک قدم جلوتر از بازار باشی

🔹 برای شروع می‌تونی از منوی پایین یکی از گزینه‌ها رو انتخاب کنی!
"""
    
    # اگر callback_query داریم (برگشت به منوی اصلی)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text,
            reply_markup=main_menu_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=main_menu_markup,
            parse_mode='Markdown'
        )
    
    return MAIN_MENU

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش دکمه‌های فشرده شده در منوی اصلی"""
    query = update.callback_query
    await query.answer()
    
    # بررسی کدام دکمه فشرده شده است
    if query.data == "main_menu":
        return await start(update, context)
    elif query.data == "guide":
        return await usage_guide(update, context)
    elif query.data == "terms":
        return await terms_and_conditions(update, context)
    elif query.data == "subscription":
        return await subscription_plans(update, context)
    elif query.data == "support":
        return await support_contact(update, context)
    elif query.data == "narmoon_products":
        return await show_narmoon_products(update, context)
    elif query.data == "ai_features":
        return await show_ai_features(update, context)
    elif query.data == "faq":
        return await show_faq(update, context)
    elif query.data == "crypto":
        # این import رو اینجا انجام می‌دیم تا circular import نداشته باشیم
        from handlers.crypto_handlers import crypto_menu
        return await crypto_menu(update, context)
    elif query.data == "analyze_charts":
        # بررسی وضعیت اشتراک کاربر
        user_id = update.effective_user.id
        if check_subscription(user_id):
            return await show_market_selection(update, context)
        else:
            subscription_buttons = [
                [InlineKeyboardButton("💳 خرید اشتراک", callback_data="subscription")],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
            ]
            
            await query.edit_message_text(
                "⚠️ برای استفاده از بخش تحلیل نمودارها نیاز به اشتراک فعال دارید.",
                reply_markup=InlineKeyboardMarkup(subscription_buttons)
            )
            return MAIN_MENU
    elif query.data == "sub_1month":
        # اشتراک ماهانه
        context.user_data['selected_plan'] = "ماهانه"
        context.user_data['plan_amount'] = 14.99
        context.user_data['plan_duration'] = 1
        return await show_payment_info(update, context)
    elif query.data == "sub_3month":
        # اشتراک سه ماهه
        context.user_data['selected_plan'] = "سه ماهه"
        context.user_data['plan_amount'] = 39.99
        context.user_data['plan_duration'] = 3
        return await show_payment_info(update, context)
    
    return MAIN_MENU

async def show_market_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست بازارها برای انتخاب"""
   
    market_buttons = [
        [InlineKeyboardButton("🪙 رمزارزها (کریپتوکارنسی)", callback_data="market_crypto")],
        [
            InlineKeyboardButton("💱 فارکس (جفت ارزها)", callback_data="market_forex"),
            InlineKeyboardButton("🥇 طلا", callback_data="market_gold")
        ],
        [
            InlineKeyboardButton("📈 سهام خارجی", callback_data="market_international_stocks"),
            InlineKeyboardButton("📊 سهام ایران", callback_data="market_iranian_stocks")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
 
    market_markup = InlineKeyboardMarkup(market_buttons)
    
    await update.callback_query.edit_message_text(
        "🎯 لطفاً بازار مورد نظر خود را انتخاب کنید:",
        reply_markup=market_markup
    )
    
    return SELECTING_MARKET

async def handle_market_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت انتخاب بازار"""
    query = update.callback_query
    await query.answer()
    
    # استخراج کلید بازار انتخابی
    market_key = query.data.replace("market_", "")
    context.user_data['selected_market'] = market_key
    
    # انتقال به انتخاب تایم فریم
    return await show_timeframes(update, context)

async def show_timeframes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست تایم‌فریم‌ها برای انتخاب"""

    timeframe_buttons = [
        [
            InlineKeyboardButton("۱ دقیقه", callback_data="tf_۱ دقیقه"),
            InlineKeyboardButton("۵ دقیقه", callback_data="tf_۵ دقیقه"),
            InlineKeyboardButton("۱۵ دقیقه", callback_data="tf_۱۵ دقیقه")
        ],
        [
            InlineKeyboardButton("۱ ساعته", callback_data="tf_۱ ساعته"),
            InlineKeyboardButton("۴ ساعته", callback_data="tf_۴ ساعته"),
            InlineKeyboardButton("روزانه", callback_data="tf_روزانه")
        ],
        [InlineKeyboardButton("هفتگی", callback_data="tf_هفتگی")]
    ]
    
    # Fix: بهبود navigation buttons
    timeframe_buttons.append([
        InlineKeyboardButton("🔙 بازگشت به انتخاب بازار", callback_data="analyze_charts"),
        InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")
    ])
    timeframe_markup = InlineKeyboardMarkup(timeframe_buttons)
    
    # نمایش بازار انتخابی
    selected_market = context.user_data.get('selected_market', 'نامشخص')
    market_name = MARKETS.get(selected_market, 'نامشخص')
    
    await update.callback_query.edit_message_text(
        f"📊 بازار انتخابی: {market_name}\n\n⏰ لطفاً تایم‌فریم مورد نظر خود را انتخاب کنید:",
        reply_markup=timeframe_markup
    )
    
    return SELECTING_TIMEFRAME

async def handle_timeframe_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت انتخاب تایم‌فریم"""
    query = update.callback_query
    await query.answer()
    
    selected_tf = query.data.replace("tf_", "")
    context.user_data['selected_timeframe'] = selected_tf
    context.user_data['expected_frames'] = EXPECTED_TIMEFRAMES[selected_tf]
    context.user_data['received_images'] = []
    
    # انتقال به انتخاب استراتژی
    return await show_strategy_selection(update, context)

async def show_strategy_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست استراتژی‌های معاملاتی"""
    strategy_buttons = []
    
    # افزودن هدر برای هر دسته
    for category, strategies in STRATEGY_CATEGORIES.items():
        # هدر دسته
        strategy_buttons.append([InlineKeyboardButton(f"═══ {category} ═══", callback_data="ignore")])
        
        # استراتژی‌های دسته
        for strategy_key in strategies:
            strategy_name = STRATEGIES[strategy_key]
            strategy_buttons.append([
                InlineKeyboardButton(strategy_name, callback_data=f"strategy_{strategy_key}")
            ])
        
        # خط جداکننده
        strategy_buttons.append([InlineKeyboardButton("───────────", callback_data="ignore")])
    
    # حذف آخرین خط جداکننده
    strategy_buttons.pop()
    
    # Fix: بهبود navigation buttons
    strategy_buttons.append([
        InlineKeyboardButton("🔙 بازگشت به تایم‌فریم", callback_data="back_to_timeframes"),
        InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")
    ])
    
    strategy_markup = InlineKeyboardMarkup(strategy_buttons)
    
    # نمایش اطلاعات انتخاب‌های قبلی
    selected_market = context.user_data.get('selected_market', 'نامشخص')
    selected_timeframe = context.user_data.get('selected_timeframe', 'نامشخص')
    market_name = MARKETS.get(selected_market, 'نامشخص')
    
    await update.callback_query.edit_message_text(
        f"📊 بازار: {market_name}\n⏰ تایم‌فریم: {selected_timeframe}\n\n🎯 لطفاً استراتژی معاملاتی مورد نظر خود را انتخاب کنید:",
        reply_markup=strategy_markup
    )
    
    return SELECTING_STRATEGY

async def handle_strategy_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت انتخاب استراتژی"""
    query = update.callback_query
    await query.answer()
    
    # نادیده گیری کلیک‌های روی هدرها و خط‌های جداکننده
    if query.data == "ignore":
        return SELECTING_STRATEGY
    
    strategy_key = query.data.replace("strategy_", "")
    context.user_data['selected_strategy'] = strategy_key
    
    # بارگیری پرامپت استراتژی از فایل استراتژی‌ها
    from resources.prompts.strategies import STRATEGY_PROMPTS
    context.user_data['strategy_prompt'] = STRATEGY_PROMPTS[strategy_key]
    
    # نمایش پیام برای ارسال تصاویر
    selected_market = context.user_data.get('selected_market', 'نامشخص')
    selected_timeframe = context.user_data.get('selected_timeframe', 'نامشخص')
    selected_strategy_name = STRATEGIES.get(strategy_key, 'نامشخص')
    market_name = MARKETS.get(selected_market, 'نامشخص')
    expected_frames = context.user_data['expected_frames']
    tf_list = " - ".join(expected_frames)
    
    await query.edit_message_text(
        f"✅ **انتخاب‌های شما:**\n" +
        f"📊 بازار: {market_name}\n" +
        f"⏰ تایم‌فریم: {selected_timeframe}\n" +
        f"🎯 استراتژی: {selected_strategy_name}\n\n" +
        f"📸 **مرحله نهایی:** لطفاً **۳ اسکرین‌شات** از نمودار در تایم‌فریم‌های زیر ارسال کنید:\n\n" +
        f"🔹 {tf_list}\n\n" +
        f"💡 برای لغو تحلیل، دستور /cancel را بفرست.",
        parse_mode='Markdown'
    )
    
    return WAITING_IMAGES

async def receive_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت تصاویر چارت از کاربر"""
    # بررسی اشتراک کاربر
    user_id = update.effective_user.id
    if not check_subscription(user_id):
        subscription_buttons = [
            [InlineKeyboardButton("💳 خرید اشتراک", callback_data="subscription")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
        ]
        
        await update.message.reply_text(
            "⚠️ اشتراک شما منقضی شده یا فعال نیست. لطفاً اشتراک خود را تمدید کنید.",
            reply_markup=InlineKeyboardMarkup(subscription_buttons)
        )
        return MAIN_MENU
    
    file = None
    ext = "jpeg"
    
    # پشتیبانی از عکس یا داکیومنت عکس
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
    elif update.message.document and update.message.document.mime_type.startswith('image/'):
        file = await update.message.document.get_file()
        ext = update.message.document.mime_type.split('/')[-1]
    else:
        await update.message.reply_text("فقط عکس ارسال کن رفیق! 😅")
        return WAITING_IMAGES
    
    photo_bytes = await file.download_as_bytearray()
    context.user_data['received_images'].append((photo_bytes, ext))
    
    received = len(context.user_data['received_images'])
    expected = 3
    
    if received < expected:
        await update.message.reply_text(f"عالی! {expected-received} عکس دیگه از تایم‌فریم‌های بعدی رو بفرست 🤩")
        return WAITING_IMAGES
    
    # وقتی هر سه عکس رسید...
    await update.message.reply_text("🔥 در حال تحلیل نمودارها با استراتژی انتخابی شما... ⏳")
    
    try:
        # استفاده از پرامپت اختصاصی استراتژی انتخابی
        strategy_prompt = context.user_data.get('strategy_prompt')
        result = analyze_chart_images(context.user_data['received_images'], strategy_prompt)
        
        # دکمه بازگشت به منوی اصلی
        menu_button = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]])
        
        # نمایش خلاصه انتخاب‌ها و نتیجه
        selected_market = context.user_data.get('selected_market', 'نامشخص')
        selected_timeframe = context.user_data.get('selected_timeframe', 'نامشخص')
        selected_strategy = context.user_data.get('selected_strategy', 'نامشخص')
        market_name = MARKETS.get(selected_market, 'نامشخص')
        strategy_name = STRATEGIES.get(selected_strategy, 'نامشخص')
        
        summary = f"📊 **تحلیل شخصی‌سازی شده نارموون**\n\n"
        summary += f"🎯 **بازار:** {market_name}\n"
        summary += f"⏰ **تایم‌فریم:** {selected_timeframe}\n"
        summary += f"🔧 **استراتژی:** {strategy_name}\n"
        summary += f"{'═' * 30}\n\n"
        
        await update.message.reply_text(
            summary + result,
            reply_markup=menu_button,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در تحلیل! دوباره تلاش کن یا /start رو بزن.\n{str(e)}")
    
    context.user_data.clear()
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات جاری و بازگشت به منوی اصلی"""
    context.user_data.clear()
    
    # دکمه بازگشت به منوی اصلی
    menu_button = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]])
    
    await update.message.reply_text(
        "عملیات لغو شد. می‌توانید به منوی اصلی بازگردید.",
        reply_markup=menu_button
    )
    
    return MAIN_MENU

# سایر هندلرها (منوها و بخش‌ها)
async def show_narmoon_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش محصولات نارموون"""
    products_text = STATIC_TEXTS["narmoon_products"]
    
    products_buttons = [
        [
            InlineKeyboardButton("🔄 نارموون دکس (رایگان)", url=NARMOON_DEX_LINK),
            InlineKeyboardButton("💰 نارموون کوین (رایگان)", url=NARMOON_COIN_LINK)
        ],
        [InlineKeyboardButton("🤖 نارموون TNT (ویژه Pro)", callback_data="subscription")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    
    products_markup = InlineKeyboardMarkup(products_buttons)
    
    await update.callback_query.edit_message_text(
        products_text,
        reply_markup=products_markup,
        parse_mode='Markdown'
    )
    
    return MAIN_MENU

async def show_ai_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش قابلیت‌های دستیار هوش مصنوعی"""
    features_text = STATIC_TEXTS["ai_assistant_features"]
    
    features_buttons = [
        [InlineKeyboardButton("💳 خرید اشتراک", callback_data="subscription")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    
    features_markup = InlineKeyboardMarkup(features_buttons)
    
    await update.callback_query.edit_message_text(
        features_text,
        reply_markup=features_markup,
        parse_mode='Markdown'
    )
    
    return MAIN_MENU

async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش سوالات متداول"""
    faq_text = STATIC_TEXTS["faq_content"]
    
    faq_buttons = [
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    
    faq_markup = InlineKeyboardMarkup(faq_buttons)
    
    await update.callback_query.edit_message_text(
        faq_text,
        reply_markup=faq_markup,
        parse_mode='Markdown'
    )
    
    return MAIN_MENU

async def usage_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش راهنمای استفاده از ربات"""
    guide_text = f"""
📚 راهنمای استفاده از ربات تحلیل چارت
برای آشنایی کامل با نحوه استفاده از ربات، لطفاً ویدیوی آموزشی زیر را مشاهده کنید:

🎬 [مشاهده ویدیوی آموزشی]({TUTORIAL_VIDEO_LINK})

راهنمای سریع:
1️⃣ ابتدا اشتراک خود را از بخش «خرید اشتراک» تهیه کنید
2️⃣ بعد از پرداخت، TXID را به پشتیبان ارسال کنید
3️⃣ پس از تأیید، می‌توانید از بخش «تحلیل نمودارها» استفاده کنید
4️⃣ بازار مورد نظر خود را انتخاب کنید (رمزارز، فارکس، طلا، سهام)
5️⃣ تایم‌فریم مورد نظر را انتخاب کرده
6️⃣ استراتژی معاملاتی خود را انتخاب کنید
7️⃣ سه تصویر از چارت در تایم‌فریم‌های مختلف ارسال کنید
8️⃣ تحلیل کامل و شخصی‌سازی‌شده را دریافت کنید
"""
    
    guide_buttons = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]]
    guide_markup = InlineKeyboardMarkup(guide_buttons)
    
    await update.callback_query.edit_message_text(
        guide_text,
        reply_markup=guide_markup,
        parse_mode='Markdown',
        disable_web_page_preview=False
    )
    
    return MAIN_MENU

async def terms_and_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش قوانین و مقررات"""
    terms_text = STATIC_TEXTS["terms_and_conditions"]
    
    terms_buttons = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]]
    terms_markup = InlineKeyboardMarkup(terms_buttons)
    
    await update.callback_query.edit_message_text(
        terms_text,
        reply_markup=terms_markup,
        parse_mode='Markdown'
    )
    
    return MAIN_MENU

async def subscription_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پلن‌های اشتراکی"""
    subscription_text = """
💳 پلن‌های اشتراکی دستیار هوش مصنوعی نارموون
لطفاً یکی از پلن‌های زیر را انتخاب کنید:

🔄 **نارموون دکس (رایگان)**: افزونه چت‌جی‌پی‌تی مخصوص تحلیل توکن‌های دکس
💰 **نارموون کوین (رایگان)**: افزونه چت‌جی‌پی‌تی مخصوص تحلیل آلتکوین‌ها
🤖 **نارموون TNT (ویژه Pro)**:
🔹 **ماهانه:** ۱۴،۹۹ دلار برای یک ماه دسترسی کامل به تمام امکانات ربات
🔹 **سه ماهه (پیشنهاد ویژه):** ۳۹،۹۹ دلار برای سه ماه --- معادل ماهی فقط ۱۳،۳۳ دلار! 💡
"""
    
    subscription_buttons = [
        [
            InlineKeyboardButton("🔄 نارموون دکس (رایگان)", url=NARMOON_DEX_LINK),
            InlineKeyboardButton("💰 نارموون کوین (رایگان)", url=NARMOON_COIN_LINK)
        ],
        [
            InlineKeyboardButton("🤖 نارموون TNT ماهانه (۱۴،۹۹ دلار)", callback_data="sub_1month"),
            InlineKeyboardButton("🤖 نارموون TNT سه ماهه (۳۹،۹۹ دلار)", callback_data="sub_3month")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    
    subscription_markup = InlineKeyboardMarkup(subscription_buttons)
    
    # اگر callback_query داریم
    if update.callback_query:
        await update.callback_query.edit_message_text(
            subscription_text,
            reply_markup=subscription_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            subscription_text,
            reply_markup=subscription_markup,
            parse_mode='Markdown'
        )
    
    return MAIN_MENU

async def show_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش اطلاعات پرداخت و کیف پول"""
    try:
        # انتخاب تصادفی یک آدرس کیف پول
        wallet_address = random.choice(SOLANA_WALLETS)
        
        # ذخیره آدرس انتخاب شده در دیتای کاربر
        context.user_data['selected_wallet'] = wallet_address
        
        plan = context.user_data['selected_plan']
        amount = context.user_data['plan_amount']
        
        payment_text = f"""
💎 اطلاعات پرداخت اشتراک {plan}
مبلغ: {amount} دلار
آدرس کیف پول سولانا:

<code>{wallet_address}</code>

لطفا پس از پرداخت، با پشتیبان تماس بگیرید و شناسه تراکنش (TXID) را برای فعال‌سازی اشتراک ارسال کنید.
@Sultan_immortal
"""
        
        payment_buttons = [[InlineKeyboardButton("🔙 بازگشت", callback_data="subscription")]]
        payment_markup = InlineKeyboardMarkup(payment_buttons)
        
        await update.callback_query.edit_message_text(
            payment_text,
            reply_markup=payment_markup,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error in show_payment_info: {str(e)}")
        try:
            # روش جایگزین در صورت بروز خطا
            await update.callback_query.message.reply_text(
                payment_text,
                reply_markup=payment_markup,
                parse_mode='HTML'
            )
        except Exception as e2:
            print(f"Second attempt also failed: {str(e2)}")
    
    return MAIN_MENU

async def support_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش اطلاعات تماس با پشتیبان"""
    support_text = """
👨‍💻 پشتیبانی ربات تحلیل چارت
برای ارتباط با پشتیبان و ارسال TXID پرداخت، لطفاً با آیدی زیر در تلگرام تماس بگیرید:

@Sultan_immortal

می‌توانید روی لینک زیر کلیک کنید:
https://t.me/Sultan_immortal

📝 راهنمای ارسال TXID به پشتیبان:
1. پس از پرداخت، شناسه تراکنش (TXID) را کپی کنید
2. به پشتیبان پیام بدهید و TXID را ارسال کنید
3. آیدی تلگرام خود را هم ذکر کنید
4. پس از تأیید تراکنش، اشتراک شما فعال خواهد شد
"""
    
    # دکمه بازگشت به منوی اصلی
    back_button = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]]
    back_markup = InlineKeyboardMarkup(back_button)
    
    await update.callback_query.edit_message_text(
        support_text,
        reply_markup=back_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    
    return MAIN_MENU

# Fix: اضافه کردن handler برای back_to_timeframes
async def handle_back_to_timeframes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بازگشت به انتخاب تایم‌فریم"""
    return await show_timeframes(update, context)
