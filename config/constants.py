# وضعیت‌های ConversationHandler
MAIN_MENU = 0
SELECTING_MARKET = 1
SELECTING_ANALYSIS_TYPE = 2  # جدید ✨
SELECTING_TIMEFRAME = 3       # تغییر عدد
SELECTING_STRATEGY = 4        # تغییر عدد  
WAITING_IMAGES = 5           # تغییر عدد
PROCESSING_ANALYSIS = 6      # تغییر عدد
TRADING_COACH = 7

# وضعیت‌های جدید برای منوی رمزارز
CRYPTO_MENU = 100
DEX_MENU = 101
DEX_SUBMENU = 102
COIN_MENU = 103
COIN_SUBMENU = 104
MAIN_MENU = 0  # اگر قبلاً تعریف نشده

# === بازارها ===
MARKETS = {
    'crypto': '🔗 رمزارزها',
    'forex': '💱 فارکس',
    'gold': '🥇 طلا',
    'international_stocks': '📈 سهام خارجی',
    'iranian_stocks': '📊 سهام ایران'
}

# === تایم فریم‌ها ===
TIMEFRAMES = ["۱ دقیقه", "۵ دقیقه", "۱۵ دقیقه", "۱ ساعته", "۴ ساعته", "روزانه", "هفتگی"]

# تایم‌فریم‌های مورد انتظار
EXPECTED_TIMEFRAMES = {
    "۱ دقیقه": ["۱ دقیقه", "۵ دقیقه", "۱۵ دقیقه"],
    "۵ دقیقه": ["۵ دقیقه", "۱۵ دقیقه", "۱ ساعته"],
    "۱۵ دقیقه": ["۱۵ دقیقه", "۱ ساعته", "۴ ساعته"],
    "۱ ساعته": ["۱ ساعته", "۴ ساعته", "روزانه"],
    "۴ ساعته": ["۴ ساعته", "روزانه", "هفتگی"],
    "روزانه": ["روزانه", "هفتگی", "ماهانه"],
    "هفتگی": ["هفتگی", "ماهانه", "سالانه"],
}

# === استراتژی‌های معاملاتی ===
STRATEGIES = {
    # دسته اول: استراتژی های شخصی
    'narmoon_ai': '🤖 استراتژی شخصی هوش مصنوعی نارموون',
}

# دسته‌بندی استراتژی‌ها برای منو
STRATEGY_CATEGORIES = {
    'شخصی': ['narmoon_ai'],
}

# === منوهای رمزارز جدید ===
# گزینه‌های نارموون دکس
DEX_OPTIONS = {
    'trending_tokens': '🔥 توکن‌های ترند',
    'new_pairs': '🆕 جفت‌های جدید',
    'top_gainers': '📈 بیشترین رشد',
    'token_analysis': '🔍 تحلیل توکن',
    'liquidity_pools': '💧 استخرهای نقدینگی',
    'whale_movements': '🐋 حرکت نهنگ‌ها',
    'rug_checker': '🚨 بررسی کلاهبرداری'
}

# گزینه‌های نارموون کوین
COIN_OPTIONS = {
    'market_overview': '📊 نمای کلی بازار',
    'top_coins': '🏆 کوین‌های برتر',
    'price_alerts': '🔔 هشدار قیمت',
    'technical_analysis': '📉 تحلیل تکنیکال',
    'onchain_data': '⛓️ داده‌های آنچین',
    'news_sentiment': '📰 اخبار و احساسات',
    'portfolio_tracker': '💼 پورتفولیو'
}

# محدودیت‌های کاربران
USER_LIMITS = {
    'free': {
        'daily_requests': 20,
        'features': ['market_overview', 'trending_tokens', 'top_coins'],
        'cache_time': 300  # 5 دقیقه
    },
    'premium': {
        'daily_requests': 1000,
        'features': 'all',
        'cache_time': 60  # 1 دقیقه
    }
}

# === انواع تحلیل ===
ANALYSIS_TYPES = {
    'classic': '📊 تحلیل کلاسیک',
    'modern': '🔬 تحلیل مدرن'
}
