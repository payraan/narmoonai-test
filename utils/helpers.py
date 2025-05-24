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

# کش ساده در حافظه (به جای Redis)
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
    
    def set(self, key, value):
        """ذخیره در کش"""
        import time
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self):
        """پاک کردن کل کش"""
        self.cache.clear()
        self.timestamps.clear()

# نمونه global از کش
cache = SimpleCache()
