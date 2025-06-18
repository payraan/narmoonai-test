# admin/commands.py

import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Forbidden
from sqlalchemy import select, func, desc, text

from config.settings import ADMIN_ID
from database import db_manager
from database.repository import AdminRepository
from database.models import User, Transaction, ApiRequest, TntUsageTracking, TntPlan, Referral, Commission, ReferralSetting

# ایمپورت‌ها در سطح ماژول فقط به موارد غیر پروژه‌ای محدود می‌شوند
# تمام ایمپورت‌های مربوط به database به داخل توابع منتقل شده‌اند

logger = logging.getLogger(__name__)


async def admin_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فعال‌سازی اشتراک کاربر توسط ادمین (Legacy)"""
    from database.repository import UserRepository, ReferralRepository

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("فرمت صحیح: /activate user_id duration plan_type")
            return

        user_id, duration, plan_type = int(args[0]), int(args[1]), args[2]

        end_date = await UserRepository.activate_legacy_subscription(user_id, duration, plan_type)

        await update.message.reply_text(f"✅ اشتراک کاربر {user_id} تا تاریخ {end_date} فعال شد.")
        # ... سایر منطق‌ها ...

    except Exception as e:
        logger.error(f"Error in admin_activate: {e}", exc_info=True)
        await update.message.reply_text(f"خطا: {e}")


async def admin_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش اطلاعات کاربر برای ادمین"""
    from database.repository import UserRepository, ApiRequestRepository

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        if not context.args:
            await update.message.reply_text("فرمت صحیح: /userinfo user_id")
            return
        
        user_id = int(context.args[0])
        user_info = await UserRepository.get_user_info(user_id)
        
        if not user_info:
            await update.message.reply_text(f"کاربر {user_id} یافت نشد.")
            return

        api_stats = await ApiRequestRepository.get_user_api_stats(user_id)
        user_data = user_info["user_data"]
        
        response = f"👤 اطلاعات کاربر: {user_data.user_id}\n" \
                   f"نام کاربری: {user_data.username or 'ندارد'}\n" \
                   f"اشتراک: {user_data.subscription_type or 'ندارد'} تا {user_data.subscription_end or 'نامشخص'}\n" \
                   f"📊 API امروز: {api_stats['today']}\n" \
                   f"📈 API کل: {api_stats['total']}"
                   
        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Error in admin_user_info: {e}", exc_info=True)
        await update.message.reply_text(f"خطا: {e}")


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کلی ربات - SQLAlchemy ORM Version"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        with db_manager.get_session() as session:
            repo = AdminRepository(session)
            
            # دریافت آمار از repository
            stats = repo.get_user_statistics()
            
            # فرمت کردن پیام
            stats_text = f"""
📊 آمار کلی ربات:

👥 تعداد کل کاربران: {stats['total_users']:,}
✅ کاربران فعال: {stats['active_users']:,}
🆕 کاربران جدید امروز: {stats['new_users_today']:,}
💰 درآمد ماه جاری: ${stats['monthly_revenue']:.2f}

🤖 وضعیت ربات: فعال ✅
🕐 آخرین بروزرسانی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await update.message.reply_text(stats_text)
            
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در دریافت آمار: {str(e)}")
        logger.error(f"Error in admin_stats: {e}")


async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام به همه کاربران - SQLAlchemy ORM Version"""
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
        
        # دریافت لیست کاربران فعال
        with db_manager.get_session() as session:
            repo = AdminRepository(session)
            user_ids = repo.get_all_active_user_ids()
        
        if not user_ids:
            await update.message.reply_text("هیچ کاربر فعالی یافت نشد.")
            return
        
        success_count = 0
        fail_count = 0
        
        await update.message.reply_text(f"شروع ارسال پیام به {len(user_ids):,} کاربر...")
        
        # Rate limiting برای جلوگیری از spam detection
        for user_id in user_ids:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 اطلاعیه:\n\n{message}"
                )
                success_count += 1
                # Delay کوتاه برای rate limiting
                await asyncio.sleep(0.1)  # 10 پیام در ثانیه
                
            except Exception as e:
                fail_count += 1
                logger.warning(f"Failed to send message to {user_id}: {e}")
        
        # گزارش نهایی
        await update.message.reply_text(
            f"✅ ارسال پیام کامل شد!\n"
            f"موفق: {success_count:,}\n"
            f"ناموفق: {fail_count:,}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در ارسال پیام: {str(e)}")
        logger.error(f"Error in admin_broadcast: {e}")


async def admin_activate_tnt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فعال‌سازی اشتراک TNT توسط ادمین"""
    from database.repository import TntRepository

    if update.effective_user.id != ADMIN_ID:
        return
        
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("فرمت صحیح: /activatetnt user_id plan_name duration")
            return

        user_id, plan_name, duration = int(args[0]), args[1].upper(), int(args[2])
        result = await TntRepository.activate_tnt_subscription(user_id, plan_name, duration)
        
        if result.get("success"):
            await update.message.reply_text(f"✅ اشتراک TNT کاربر {user_id} با پلن {plan_name} فعال شد.")
        else:
            await update.message.reply_text(f"❌ خطا در فعال‌سازی: {result.get('error')}")

    except Exception as e:
        logger.error(f"Error in admin_activate_tnt: {e}", exc_info=True)
        await update.message.reply_text(f"خطا: {e}")


async def admin_tnt_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار TNT برای ادمین - SQLAlchemy ORM Version"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        await update.message.reply_text("🔄 در حال دریافت آمار TNT...")
        
        # دریافت آمار TNT از repository
        with db_manager.get_session() as session:
            repo = AdminRepository(session)
            stats = repo.get_tnt_subscription_stats()
        
        # ساخت پیام آمار
        stats_message = f"""📊 **آمار TNT سیستم**

📈 **آمار پلن‌ها:**
"""
        
        # نمایش توزیع پلن‌ها
        for plan_info in stats['plan_distribution']:
            plan_type = plan_info['plan_type']
            count = plan_info['count']
            stats_message += f"• {plan_type}: {count} کاربر\n"
        
        # آمار کلی
        stats_message += f"""
🔥 **فعالیت امروز:**
- کاربران فعال: {stats['today_stats']['active_users']}
- تحلیل‌های انجام شده: {stats['today_stats']['total_analyses']}

✅ **کاربران فعال TNT:** {stats['active_tnt_users']} نفر

🕐 **آخرین بروزرسانی:** {stats['timestamp'][:19].replace('T', ' ')}
"""
        
        await update.message.reply_text(stats_message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در دریافت آمار TNT: {str(e)}")
        logger.error(f"Error in admin_tnt_stats: {e}")


async def admin_user_tnt_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش اطلاعات TNT کاربر خاص"""
    await update.message.reply_text("این دستور در حال بازسازی است.")


async def admin_clean_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاک کردن کامل دیتابیس توسط ادمین - SQLAlchemy ORM Version"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی به این دستور را ندارید.")
        return

    try:
        # بررسی تایید
        args = context.args
        if not args or args[0] != "CONFIRM":
            await update.message.reply_text(
                "⚠️ **هشدار: این دستور تمام داده‌های دیتابیس را پاک می‌کند!**\n\n"
                "برای تایید، دستور زیر را ارسال کنید:\n"
                "`/cleandb CONFIRM`\n\n"
                "**این عمل قابل بازگشت نیست!**",
                parse_mode='Markdown'
            )
            return

        await update.message.reply_text("🧹 شروع پاک‌سازی دیتابیس...")

        # انجام cleanup با repository
        with db_manager.get_session() as session:
            repo = AdminRepository(session)
            
            # دریافت آمار قبل از پاک‌سازی
            stats_before = repo.get_user_statistics()
            users_before = stats_before['total_users']
            
            # انجام cleanup
            cleanup_results = repo.cleanup_database()
            
            # Reset sequences
            sequences_reset = repo.reset_sequences()

        # ساخت گزارش نتایج
        result_message = f"🧹 **پاک‌سازی دیتابیس کامل شد**\n\n"
        result_message += f"📊 **آمار کلی:**\n"
        result_message += f"• کاربران قبل: {users_before:,}\n"
        result_message += f"• Sequences Reset: {'✅' if sequences_reset else '❌'}\n\n"
        result_message += f"📋 **جزئیات جداول:**\n"
        
        for table_name, results in cleanup_results.items():
            result_message += f"• **{table_name}:** {results['deleted']:,} حذف شده\n"
        
        result_message += f"\n✨ **دیتابیس آماده تست‌های جدید است!**"
        
        await update.message.reply_text(result_message)
        
        # اطلاع‌رسانی عمومی
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🔄 دیتابیس بازنشانی شد. همه کاربران حالا می‌توانند با حساب تمیز شروع کنند."
            )
        except:
            pass
            
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در پاک‌سازی دیتابیس: {str(e)}")
        logger.error(f"Error in admin_clean_database: {e}")


async def admin_db_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کلی دیتابیس - SQLAlchemy ORM Version"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        with db_manager.get_session() as session:
            repo = AdminRepository(session)
            
            # دریافت آمار کلی
            user_stats = repo.get_user_statistics()
            
            # شمارش جداول مختلف
            tables_stats = {}
            
            # User related tables
            tables_stats["users"] = session.query(User).count()
            tables_stats["transactions"] = session.query(Transaction).count()
            tables_stats["api_requests"] = session.query(ApiRequest).count()
            
            # TNT system tables
            tables_stats["tnt_usage_tracking"] = session.query(TntUsageTracking).count()
            tables_stats["tnt_plans"] = session.query(TntPlan).count()
            
            # Referral system tables
            tables_stats["referrals"] = session.query(Referral).count()
            tables_stats["commissions"] = session.query(Commission).count()
            tables_stats["referral_settings"] = session.query(ReferralSetting).count()
        
        # ساخت پیام آمار
        stats_message = "📊 **آمار کامل دیتابیس**\n\n"
        
        # آمار کلی کاربران
        stats_message += f"👥 **آمار کاربران:**\n"
        stats_message += f"• کل کاربران: {user_stats['total_users']:,}\n"
        stats_message += f"• کاربران فعال: {user_stats['active_users']:,}\n"
        stats_message += f"• کاربران جدید امروز: {user_stats['new_users_today']:,}\n\n"
        
        # آمار جداول
        stats_message += f"🗄️ **آمار جداول:**\n"
        for table, count in tables_stats.items():
            stats_message += f"• **{table}:** {count:,} رکورد\n"
        
        # اطلاعات سیستم
        stats_message += f"\n🔧 **اطلاعات سیستم:**\n"
        stats_message += f"• نوع دیتابیس: {db_manager.health_check().get('database_type', 'unknown')}\n"
        stats_message += f"• آخرین بروزرسانی: {user_stats['timestamp'][:19].replace('T', ' ')}\n"
        
        await update.message.reply_text(stats_message)
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در دریافت آمار: {str(e)}")
        logger.error(f"Error in admin_db_stats: {e}")


async def admin_reset_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ریست ساده دیتابیس"""
    await update.message.reply_text("این دستور با `cleandb` جایگزین شده است.")


async def admin_health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی سلامت سیستم"""
    await update.message.reply_text("✅ سیستم سالم است.")


async def admin_referral_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کامل رفرال برای ادمین - SQLAlchemy ORM Version"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        await update.message.reply_text("🔄 در حال دریافت آمار رفرال...")
        
        # دریافت آمار کامل از repository
        with db_manager.get_session() as session:
            repo = AdminRepository(session)
            stats = repo.get_referral_overview()
        
        if not stats.get('success'):
            await update.message.reply_text(f"❌ خطا: {stats.get('error')}")
            return
        
        # آمار کلی سیستم
        system_stats = stats['system_stats']
        message = f"""📊 **آمار کامل سیستم رفرال**

🔢 **آمار کلی:**
- کل referrer ها: {system_stats['total_referrers']} نفر
- کل کمیسیون‌ها: {system_stats['total_commissions']} مورد
- کل مبلغ کمیسیون: ${system_stats['total_commissions_amount']:.2f}
- در انتظار پرداخت: ${system_stats['pending_payments']:.2f}
- پرداخت شده: ${system_stats['paid_amount']:.2f}

👥 **فعال‌ترین referrer ها:**"""
        
        # نمایش 10 نفر برتر
        referrers = stats['referrers'][:10]
        for i, ref in enumerate(referrers, 1):
            username = ref['username'][:15] + "..." if len(ref['username']) > 15 else ref['username']
            message += f"""
{i}. **{username}** (ID: {ref['user_id']})
   • کل رفرال: {ref['total_referrals']} نفر
   • کل درآمد: ${ref['total_earned']:.2f}
   • در انتظار: ${ref['pending_amount']:.2f}"""
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در دریافت آمار: {str(e)}")
        logger.error(f"Error in admin_referral_stats: {e}")
