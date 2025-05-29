def format_large_number(num):
    """فرمت کردن اعداد بزرگ"""
    try:
        num = float(num)
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.2f}K"
        else:
            return f"{num:.2f}"
    except (ValueError, TypeError):
        return "0"

def format_percentage(num):
    """فرمت کردن درصدها"""
    try:
        num = float(num)
        return f"{num:+.2f}%"
    except (ValueError, TypeError):
        return "0.00%"

def format_price(price):
    """فرمت کردن قیمت"""
    try:
        price = float(price)
        if price < 0.01:
            return f"${price:.6f}"
        elif price < 1:
            return f"${price:.4f}"
        else:
            return f"${price:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

def format_market_overview(data):
    """فرمت کردن نمای کلی بازار"""
    if data.get("error"):
        return "❌ خطا در دریافت اطلاعات بازار."
    
    message = "📊 **نمای کلی بازار**\n\n"
    
    # دامیننس بیتکوین
    btc_dominance = data.get("btc_dominance", 0)
    message += f"₿ **دامیننس BTC:** {btc_dominance:.2f}%\n"
    
    # کل بازار
    total_market_cap = data.get("total_market_cap", 0)
    message += f"💰 **کل بازار:** ${format_large_number(total_market_cap)}\n"
    
    # حجم معاملات
    total_volume = data.get("total_volume", 0)
    message += f"📈 **حجم 24ساعته:** ${format_large_number(total_volume)}\n"
    
    # تغییر بازار
    market_change = data.get("market_cap_change_24h", 0)
    message += f"📊 **تغییر 24ساعته:** {format_percentage(market_change)}\n"
    
    # کوین‌های اصلی
    main_coins = data.get("main_coins", {})
    if main_coins:
        message += "\n**💎 کوین‌های اصلی:**\n"
        for symbol, coin_data in main_coins.items():
            price = coin_data.get("price", 0)
            change = coin_data.get("change_24h", 0)
            message += f"• **{symbol}:** {format_price(price)} ({format_percentage(change)})\n"
    
    return message

def format_token_info(data):
    """فرمت کردن اطلاعات توکن - آدرس قابل کپی"""
    if data.get("error") or "data" not in data:
        return "❌ خطا در دریافت اطلاعات توکن."
    
    token_data = data["data"]
    attributes = token_data.get("attributes", {})
    
    message = "🔍 **اطلاعات توکن**\n\n"
    
    # اطلاعات پایه
    name = attributes.get("name", "نامشخص")
    symbol = attributes.get("symbol", "???")
    address = attributes.get("address", "نامشخص")
    
    message += f"**نام:** {name}\n"
    message += f"**نماد:** {symbol}\n"
    
    # ⭐ آدرس قابل کپی - اصلاح شده
    if address and address != "نامشخص":
        message += f"**آدرس:** `{address}`\n\n"
    else:
        message += "\n"
    
    # قیمت و بازار
    price_usd = attributes.get("price_usd")
    if price_usd:
        message += f"**💰 قیمت:** {format_price(price_usd)}\n"
    
    market_cap = attributes.get("fdv_usd")
    if market_cap:
        message += f"**📊 ارزش بازار:** ${format_large_number(market_cap)}\n"
    
    volume_24h = attributes.get("volume_usd", {}).get("h24")
    if volume_24h:
        message += f"**📈 حجم 24ساعته:** ${format_large_number(volume_24h)}\n"
    
    # تغییرات قیمت
    price_changes = attributes.get("price_change_percentage", {})
    if price_changes:
        message += "\n**📊 تغییرات قیمت:**\n"
        for period, change in price_changes.items():
            if change and period in ['h1', 'h6', 'h24']:
                period_name = {"h1": "1 ساعت", "h6": "6 ساعت", "h24": "24 ساعت"}[period]
                message += f"• {period_name}: {format_percentage(change)}\n"
    
    return message

def format_holders_info(holders_data, stats_data, deltas_data):
    """فرمت کردن اطلاعات هولدرها - آدرس قابل کپی"""
    message = "👥 **اطلاعات هولدرهای توکن**\n\n"
    
    # آمار کلی
    if not stats_data.get("error"):
        message += "**📊 آمار کلی:**\n"
        total_holders = stats_data.get("total_holders", 0)
        message += f"• کل هولدرها: {total_holders:,}\n"
        
        avg_balance = stats_data.get("average_balance", 0)
        if avg_balance:
            message += f"• میانگین موجودی: {format_large_number(avg_balance)}\n"
        
        message += "\n"
    
    # تغییرات اخیر
    if not deltas_data.get("error") and isinstance(deltas_data, list):
        message += "**📈 تغییرات اخیر:**\n"
        for delta in deltas_data[:5]:
            change_type = "خرید" if delta.get("delta", 0) > 0 else "فروش"
            amount = abs(delta.get("delta", 0))
            address = delta.get("address", "نامشخص")
            
            # ⭐ آدرس قابل کپی - اصلاح شده  
            if len(address) > 8:
                formatted_address = f"`{address[:8]}...{address[-4:]}`"
            else:
                formatted_address = f"`{address}`"
            
            message += f"• {formatted_address}: {change_type} {format_large_number(amount)}\n"
        message += "\n"
    
    # بزرگترین هولدرها
    if not holders_data.get("error") and "holders" in holders_data:
        message += "**🐋 بزرگترین هولدرها:**\n"
        holders = holders_data["holders"][:10]
        
        for i, holder in enumerate(holders, 1):
            address = holder.get("address", "نامشخص")
            balance = holder.get("balance", 0)
            percentage = holder.get("percentage", 0)
            
            # ⭐ آدرس قابل کپی - اصلاح شده
            if len(address) > 12:
                formatted_address = f"`{address[:8]}...{address[-4:]}`"
            else:
                formatted_address = f"`{address[:12]}...`"
            
            message += f"{i}. {formatted_address}\n"
            message += f"   💰 موجودی: {format_large_number(balance)}\n"
            message += f"   📊 درصد: {percentage:.2f}%\n\n"
    
    return message

def format_trending_tokens(data):
    """فرمت کردن توکن‌های ترند - آدرس قابل کپی"""
    if data.get("error"):
        return "❌ خطا در دریافت توکن‌های ترند."
    
    message = "🔥 **توکن‌های ترند**\n\n"
    
    if isinstance(data, list):
        tokens = data[:10]
        for i, token in enumerate(tokens, 1):
            name = token.get("name", "نامشخص")
            symbol = token.get("symbol", "???")
            price = token.get("price", 0)
            price_change = token.get("price_change_24h", 0)
            volume = token.get("volume_24h", 0)
            address = token.get("address", "")
            
            message += f"{i}. **{name}** ({symbol})\n"
            message += f"   💰 قیمت: {format_price(price)}\n"
            message += f"   📈 تغییر: {format_percentage(price_change)}\n"
            message += f"   📊 حجم: ${format_large_number(volume)}\n"
            
            # ⭐ آدرس قابل کپی - اصلاح شده
            if address:
                message += f"   📍 آدرس: `{address}`\n"
            
            message += "\n"
    else:
        message += "هیچ توکن ترندی یافت نشد."
    
    return message

def format_error_message(error_type):
    """فرمت کردن پیام‌های خطا"""
    error_messages = {
        "general": "❌ خطایی رخ داده است. لطفاً دوباره تلاش کنید.",
        "api_limit": "⚠️ محدودیت درخواست‌های روزانه به پایان رسیده است.",
        "invalid_address": "❌ آدرس وارد شده نامعتبر است.",
        "no_data": "📭 هیچ داده‌ای یافت نشد.",
        "network_error": "🌐 خطا در اتصال به شبکه. لطفاً دوباره تلاش کنید."
    }
    
    return error_messages.get(error_type, error_messages["general"])
