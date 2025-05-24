# وضعیت‌های ConversationHandler
MAIN_MENU = 0
SELECTING_MARKET = 1
SELECTING_TIMEFRAME = 2
SELECTING_STRATEGY = 3
WAITING_IMAGES = 4
PROCESSING_ANALYSIS = 5

# وضعیت‌های جدید برای منوی رمزارز
CRYPTO_MENU = 100
DEX_MENU = 101
DEX_SUBMENU = 102
COIN_MENU = 103
COIN_SUBMENU = 104
MAIN_MENU = 0  # اگر قبلاً تعریف نشده

# === بازارها ===
MARKETS = {
    'crypto': '🔗 رمزارزها (کریپتوکارنسی)',
    'forex': '💱 فارکس (جفت ارزها)',
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
    
    # دسته دوم: اسکالپینگ
    'ema_scalping': '⚡ اسکالپینگ با EMA',
    'rsi_scalping': '📊 اسکالپینگ با RSI',
    'squeeze_momentum': '💥 اسکوییز مومنتوم (شتاب ناگهانی)',
    'volatility_breakout': '🔥 شکست نوسان (Volatility Breakout)',
    'breakout_retest': '🔄 پولبک به شکست (Breakout Retest)',
    'mean_reversion': '⚖️ بازگشت به میانگین (Mean Reversion)',
    
    # دسته سوم: سوئینگ
    'momentum_swing': '🚀 مومنتوم سوئینگ (نوسان با شتاب)',
    'trend_following': '📈 دنبال‌کننده روند (Trend Following)',
    'trend_reversal': '🔀 برگشت روند (Trend Reversal)',
    'divergence_play': '📉 معامله بر اساس واگرایی (Divergence Play)',
    'continuation_pattern': '🔁 الگوی ادامه‌دهنده (Continuation Pattern)',
    'range_bound': '📏 معامله در محدوده رنج (Range Bound)',
    
    # دسته چهارم: پیشرفته
    'triple_confluence': '🎯 همگرایی سه‌گانه (Triple Confluence)',
    'pullback_retracement': '↩️ اصلاح پولبک (Pullback Retracement)',
    'liquidity_sweep': '🌊 لیکوئیدیتی سویپ (جارو یا شکار نقدینگی)'
}

# دسته‌بندی استراتژی‌ها برای منو
STRATEGY_CATEGORIES = {
    'شخصی': ['narmoon_ai'],
    'اسکالپینگ': ['ema_scalping', 'rsi_scalping', 'squeeze_momentum',
                 'volatility_breakout', 'breakout_retest', 'mean_reversion'],
    'سوئینگ': ['momentum_swing', 'trend_following', 'trend_reversal',
               'divergence_play', 'continuation_pattern', 'range_bound'],
    'پیشرفته': ['triple_confluence', 'pullback_retracement', 'liquidity_sweep']
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
