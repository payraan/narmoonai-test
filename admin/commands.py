from telegram import Update
from telegram.ext import ContextTypes
from config.settings import ADMIN_ID
from database.operations import activate_subscription, get_user_info, get_user_api_stats, get_connection

async def admin_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فعال‌سازی اشتراک کاربر توسط ادمین (فرمت: /activate user_id duration plan_type)"""
    # بررسی دسترسی ادمین
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی به این دستور را ندارید.")
        return
    
    try:
        # بررسی پارامترها
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "فرمت صحیح: /activate user_id duration plan_type\n"
                "مثال: /activate 123456789 3 سه_ماهه"
            )
            return
        
        user_id = int(args[0])
        duration = int(args[1])
        plan_type = args[2]
        
        # فعال‌سازی اشتراک
        end_date = activate_subscription(user_id, duration, plan_type)
        
        # ارسال پیام به ادمین
        await update.message.reply_text(
            f"اشتراک کاربر {user_id} با موفقیت فعال شد.\n"
            f"تاریخ پایان: {end_date}"
        )
        
        # ارسال پیام به کاربر
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 اشتراک شما با موفقیت فعال شد!\n\n"
                     f"نوع اشتراک: {plan_type}\n"
                     f"تاریخ پایان: {end_date}\n\n"
                     f"از خرید شما متشکریم! برای شروع دستور /start را بزنید."
            )
        except Exception as e:
            await update.message.reply_text(
                f"اشتراک فعال شد اما ارسال پیام به کاربر با خطا مواجه شد: {str(e)}"
            )
    
    except Exception as e:
        await update.message.reply_text(f"خطا در فعال‌سازی اشتراک: {str(e)}")

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنمای دستورات ادمین"""
    # بررسی دسترسی ادمین
    if update.effective_user.id != ADMIN_ID:
        return
    
    help_text = """
👨‍💻 راهنمای دستورات مدیریتی:

/adminhelp - نمایش این راهنما
/activate user_id duration plan_type - فعال‌سازی اشتراک کاربر
مثال: /activate 123456789 3 سه_ماهه

/userinfo user_id - نمایش اطلاعات کاربر
مثال: /userinfo 123456789

/stats - آمار کلی ربات
/broadcast - ارسال پیام به همه کاربران
    """
    
    await update.message.reply_text(help_text)

async def admin_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش اطلاعات کاربر برای ادمین"""
    # بررسی دسترسی ادمین
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        # بررسی پارامترها
        args = context.args
        if not args:
            await update.message.reply_text(
                "فرمت صحیح: /userinfo user_id\n"
                "مثال: /userinfo 123456789"
            )
            return
        
        user_id = int(args[0])
        
        # دریافت اطلاعات کاربر
        user_info = get_user_info(user_id)
        
        if not user_info:
            await update.message.reply_text(f"کاربری با شناسه {user_id} یافت نشد.")
            return
        
        user_data = user_info["user_data"]
        transactions = user_info["transactions"]
        
        # دریافت آمار API
        api_stats = get_user_api_stats(user_id)
        
        # نمایش اطلاعات کاربر
        response = f"""
👤 اطلاعات کاربر:
شناسه: {user_data[0]}
نام کاربری: {user_data[1] or 'نامشخص'}
تاریخ پایان اشتراک: {user_data[2] or 'ندارد'}
نوع اشتراک: {user_data[3] or 'ندارد'}
وضعیت اشتراک: {'فعال' if user_data[4] else 'غیرفعال'}

📊 آمار API:
درخواست‌های امروز: {api_stats['today']}
کل درخواست‌ها: {api_stats['total']}
        """
        
        # اضافه کردن اطلاعات تراکنش‌ها
        if transactions:
            response += "\n💰 تراکنش‌های اخیر:\n"
            for tx in transactions:
                response += f"TXID: {tx[2]}\n"
                response += f"کیف پول: {tx[3]}\n"
                response += f"مبلغ: {tx[4]}\n"
                response += f"وضعیت: {tx[6]}\n"
                response += f"تاریخ: {tx[7]}\n\n"
        
        await update.message.reply_text(response)
    
    except Exception as e:
        await update.message.reply_text(f"خطا در دریافت اطلاعات کاربر: {str(e)}")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کلی ربات - PostgreSQL Compatible"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    from datetime import datetime, timedelta
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # تعداد کل کاربران
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # کاربران فعال (با اشتراک)
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = %s", (True,))
        active_users = cursor.fetchone()[0]
        
        # کاربران جدید امروز
        today = datetime.now().date()
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE DATE(created_at) = %s",
            (today,)
        )
        new_users_today = cursor.fetchone()[0]
        
        # درآمد ماه جاری
        first_day = today.replace(day=1)
        cursor.execute(
            "SELECT SUM(amount) FROM transactions WHERE status = 'completed' AND DATE(created_at) >= %s",
            (first_day,)
        )
        monthly_revenue = cursor.fetchone()[0] or 0
        
        conn.close()
        
        stats_text = f"""
📊 آمار کلی ربات:

👥 تعداد کل کاربران: {total_users}
✅ کاربران فعال: {active_users}
🆕 کاربران جدید امروز: {new_users_today}
💰 درآمد ماه جاری: ${monthly_revenue:.2f}

🤖 وضعیت ربات: فعال ✅
        """
        
        await update.message.reply_text(stats_text)
        
    except Exception as e:
        await update.message.reply_text(f"خطا در دریافت آمار: {str(e)}")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام به همه کاربران - PostgreSQL Compatible"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        # بررسی وجود پیام
        if not context.args:
            await update.message.reply_text(
                "لطفاً پیام خود را بعد از دستور بنویسید.\n"
                "مثال: /broadcast سلام به همه کاربران عزیز!"
            )
            return
        
        message = ' '.join(context.args)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # دریافت لیست کاربران
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        conn.close()
        
        success_count = 0
        fail_count = 0
        
        await update.message.reply_text(f"شروع ارسال پیام به {len(users)} کاربر...")
        
        # اضافه کردن delay برای جلوگیری از rate limiting
        import asyncio
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user[0],
                    text=f"📢 اطلاعیه:\n\n{message}"
                )
                success_count += 1
                # delay کوتاه برای جلوگیری از spam detection
                await asyncio.sleep(0.05)  # 20 پیام در ثانیه
            except Exception as e:
                fail_count += 1
                print(f"Failed to send message to {user[0]}: {e}")
        
        await update.message.reply_text(
            f"✅ ارسال پیام کامل شد!\n"
            f"موفق: {success_count}\n"
            f"ناموفق: {fail_count}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"خطا در ارسال پیام: {str(e)}")
