# handlers/ui_helpers.py (فایل جدید)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# الگوهای استاندارد callback
CALLBACKS = {
    "MAIN_MENU": "main_menu",
    "CRYPTO": "crypto",
    "DEX": "narmoon_dex", 
    "COIN": "narmoon_coin",
    "TRADE_COACH": "trade_coach",
    "ANALYZE_CHARTS": "analyze_charts"
}

# پیام‌های استاندارد
STANDARD_MESSAGES = {
    "PROCESSING": "⏳ در حال پردازش، لطفاً صبر کنید...",
    "ERROR": "❌ خطایی رخ داده است. لطفاً دوباره تلاش کنید.",
    "SUCCESS": "✅ عملیات با موفقیت انجام شد!"
}

def main_menu_button():
    """دکمه استاندارد منوی اصلی"""
    return InlineKeyboardButton("🏠 منوی اصلی", callback_data=CALLBACKS["MAIN_MENU"])

def back_button(text: str, callback_data: str):
    """دکمه استاندارد بازگشت"""
    return InlineKeyboardButton(f"🔙 {text}", callback_data=callback_data)

def single_row_keyboard(*buttons):
    """کیبورد تک ردیفه"""
    return InlineKeyboardMarkup([list(buttons)])

def multi_row_keyboard(buttons_list):
    """کیبورد چند ردیفه"""
    return InlineKeyboardMarkup(buttons_list)

# کیبوردهای پرکاربرد
def main_menu_only():
    return single_row_keyboard(main_menu_button())

def back_and_main(back_text: str, back_callback: str):
    return multi_row_keyboard([
        [back_button(back_text, back_callback)],
        [main_menu_button()]
    ])

def breadcrumb_navigation(current_menu: str, parent_menus: list):
    """ناوبری breadcrumb برای منوهای عمیق"""
    buttons = []
    
    # دکمه‌های والدین
    for menu_text, menu_callback in parent_menus:
        buttons.append([back_button(menu_text, menu_callback)])
    
    # دکمه منوی اصلی
    buttons.append([main_menu_button()])
    
    return InlineKeyboardMarkup(buttons)

# مثال‌های استفاده
def dex_submenu_navigation():
    """ناوبری برای زیرمنوی دکس"""
    return breadcrumb_navigation("زیرمنوی دکس", [
        ("دکس", CALLBACKS["DEX"]),
        ("رمزارز", CALLBACKS["CRYPTO"])
    ])

def coin_submenu_navigation():
    """ناوبری برای زیرمنوی کوین"""
    return breadcrumb_navigation("زیرمنوی کوین", [
        ("کوین", CALLBACKS["COIN"]),
        ("رمزارز", CALLBACKS["CRYPTO"])
    ])

def enhanced_back_navigation(back_text: str, back_callback: str, show_crypto: bool = False):
    """ناوبری پیشرفته با گزینه نمایش منوی کریپتو"""
    buttons = [
        [back_button(back_text, back_callback)]
    ]
    
    if show_crypto:
        buttons.append([back_button("رمزارز", CALLBACKS["CRYPTO"])])
    
    buttons.append([main_menu_button()])
    
    return InlineKeyboardMarkup(buttons)
