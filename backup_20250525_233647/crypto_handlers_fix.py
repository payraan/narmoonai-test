# این کد را در قسمت process_user_input باید جایگزین کنید
# بخش مربوط به token_holders

elif action_type == 'token_holders':
    # اطلاعات هولدرها
    await update.message.reply_text("⏳ در حال دریافت اطلاعات هولدرها...")
    
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
