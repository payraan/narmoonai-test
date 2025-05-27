import os

def load_text(filename):
    """بارگذاری فایل متنی از پوشه resources/texts"""
    path = f"resources/texts/{filename}.txt"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"هشدار: فایل متنی {path} یافت نشد")
        return f"[متن {filename} یافت نشد]"

def load_static_texts():
    """بارگذاری تمام متن‌های ثابت مورد نیاز"""
    texts = {
        "terms_and_conditions": load_text("terms"),
        "faq_content": load_text("faq"),
        "ai_assistant_features": load_text("features"),
        "narmoon_products": load_text("products")
    }
    return texts

def format_number_fa(number):
    """تبدیل اعداد انگلیسی به فارسی"""
    persian_numbers = "۰۱۲۳۴۵۶۷۸۹"
    english_numbers = "0123456789"
    
    result = str(number)
    for i, e in enumerate(english_numbers):
        result = result.replace(e, persian_numbers[i])
    return result

def format_large_number(num):
    """تبدیل اعداد بزرگ به فرمت خوانا"""
    if num >= 1e12:
        return f"{num/1e12:.2f}T"
    elif num >= 1e9:
        return f"{num/1e9:.2f}B"
    elif num >= 1e6:
        return f"{num/1e6:.2f}M"
    elif num >= 1e3:
        return f"{num/1e3:.2f}K"
    return f"{num:.2f}"

def format_price(price):
    """فرمت کردن قیمت با کاما"""
    if price >= 1:
        return f"{price:,.2f}"
    else:
        # برای قیمت‌های کمتر از 1 دلار، دقت بیشتر
        return f"{price:.6f}"

def format_percentage(value):
    """فرمت کردن درصد با رنگ"""
    if value > 0:
        return f"🟢 +{value:.2f}%"
    elif value < 0:
        return f"🔴 {value:.2f}%"
    else:
        return f"⚪ {value:.2f}%"

def truncate_text(text, max_length=50):
    """کوتاه کردن متن طولانی"""
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text

def escape_markdown(text):
    """Escape کردن کاراکترهای خاص Markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_token_price(price_str):
    """
    فرمت کردن قیمت توکن با حداکثر 4 رقم اعشار
    """
    try:
        price = float(price_str)
        
        if price >= 1:
            # قیمت‌های بالای 1 دلار - 2 رقم اعشار
            return f"${price:,.2f}"
        elif price >= 0.0001:
            # قیمت‌های بین 0.0001 تا 1 دلار - 4 رقم اعشار
            return f"${price:.4f}"
        elif price > 0:
            # قیمت‌های خیلی کوچک - نمایش علمی
            return f"${price:.2e}"
        else:
            return "$0.0000"
    except (ValueError, TypeError):
        return str(price_str)

# === Redis Cache Integration ===
# Import Redis cache service
try:
    from services.redis_cache_service import redis_cache as cache
    print("✅ Redis cache loaded successfully")
except ImportError as e:
    print(f"⚠️ Redis cache import failed: {e}")
    print("📝 Using fallback memory cache")
    
    # Fallback to simple memory cache
    class SimpleCache:
        def __init__(self):
            self.cache = {}
            self.timestamps = {}
        
        def get(self, key):
            """دریافت از کش"""
            import time
            
            if key in self.cache:
                # بررسی انقضا (5 دقیقه)
                if time.time() - self.timestamps[key] < 300:
                    return self.cache[key]
                else:
                    # حذف داده منقضی شده
                    del self.cache[key]
                    del self.timestamps[key]
            return None
        
        def set(self, key, value, ttl=300):
            """ذخیره در کش"""
            import time
            self.cache[key] = value
            self.timestamps[key] = time.time()
            return True
        
        def delete(self, key):
            """حذف از کش"""
            if key in self.cache:
                del self.cache[key]
                if key in self.timestamps:
                    del self.timestamps[key]
                return True
            return False
        
        def exists(self, key):
            """بررسی وجود کلید"""
            return key in self.cache
        
        def clear(self):
            """پاک کردن کل کش"""
            self.cache.clear()
            self.timestamps.clear()
        
        def health_check(self):
            """بررسی سلامت کش"""
            return {
                "redis_connected": False,
                "fallback_memory": True,
                "total_keys": len(self.cache)
            }
    
    # نمونه global از کش
    cache = SimpleCache()

# Cache decorators and utilities
def cache_result(key_prefix: str, ttl: int = 300):
    """دکوریتور برای کش کردن نتایج تابع"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # ساخت کلید کش
            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # چک کردن کش
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                print(f"📦 Cache hit for {key_prefix}")
                return cached_result
            
            # اجرای تابع و ذخیره نتیجه
            print(f"🔄 Cache miss for {key_prefix}, fetching...")
            result = await func(*args, **kwargs)
            
            if result is not None:
                cache.set(cache_key, result, ttl)
                print(f"💾 Cached result for {key_prefix}")
            
            return result
        
        def sync_wrapper(*args, **kwargs):
            # ساخت کلید کش
            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # چک کردن کش
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                print(f"📦 Cache hit for {key_prefix}")
                return cached_result
            
            # اجرای تابع و ذخیره نتیجه
            print(f"🔄 Cache miss for {key_prefix}, fetching...")
            result = func(*args, **kwargs)
            
            if result is not None:
                cache.set(cache_key, result, ttl)
                print(f"💾 Cached result for {key_prefix}")
            
            return result
        
        # تشخیص نوع تابع (async یا sync)
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def invalidate_cache_pattern(pattern: str):
    """پاک کردن کش با الگوی خاص"""
    try:
        deleted_count = cache.clear_pattern(pattern)
        print(f"🗑️ Invalidated {deleted_count} cache entries matching: {pattern}")
        return deleted_count
    except Exception as e:
        print(f"❌ Cache invalidation error: {e}")
        return 0

def get_cache_stats():
    """دریافت آمار کش"""
    try:
        health = cache.health_check()
        return {
            "status": "connected" if health.get("redis_connected") else "memory_fallback",
            "redis_connected": health.get("redis_connected", False),
            "using_memory_fallback": health.get("fallback_memory", False),
            "test_operations": {
                "write": health.get("test_write", False),
                "read": health.get("test_read", False)
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
