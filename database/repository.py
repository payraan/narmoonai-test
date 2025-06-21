"""
Repository layer for admin operations
Clean SQLAlchemy ORM implementation without any raw SQL
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, or_, desc, case, text

from .connection import db_manager
from .models import (
    User, Transaction, ApiRequest, TntUsageTracking, TntPlan,
    Referral, Commission, ReferralSetting
)

logger = logging.getLogger(__name__)

class AdminRepository:
    """Repository for admin operations with clean SQLAlchemy ORM"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    # === USER STATISTICS ===
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            today = date.today()
            
            # Basic counts
            total_users = self.db_session.query(User).count()
            active_users = self.db_session.query(User).filter(User.is_active == True).count()
            
            # Today's new users
            new_users_today = self.db_session.query(User).filter(
                func.date(User.created_at) == today
            ).count()
            
            # Monthly revenue
            first_day = today.replace(day=1)
            monthly_revenue = self.db_session.query(func.sum(Transaction.amount)).filter(
                Transaction.status == 'completed',
                func.date(Transaction.created_at) >= first_day
            ).scalar() or 0
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "new_users_today": new_users_today,
                "monthly_revenue": float(monthly_revenue),
                "timestamp": datetime.now().isoformat()
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting user statistics: {e}")
            raise
    
    # === BROADCAST SUPPORT ===
    def get_all_active_user_ids(self) -> List[int]:
        """Get list of all active user IDs for broadcast"""
        try:
            user_ids = self.db_session.query(User.user_id).filter(
                User.is_active == True
            ).all()
            
            return [user_id[0] for user_id in user_ids]
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting active user IDs: {e}")
            raise
      
    # === TNT SUBSCRIPTION STATISTICS ===
    def get_tnt_subscription_stats(self) -> Dict[str, Any]:
        """Get TNT subscription statistics"""
        try:
            # Count by plan type
            plan_stats = self.db_session.query(
                User.tnt_plan_type,
                func.count(User.user_id).label('count')
            ).filter(
                User.tnt_plan_type.isnot(None),
                User.tnt_plan_type != 'FREE'
            ).group_by(User.tnt_plan_type).all()

            # Active TNT users
            active_tnt_users = self.db_session.query(User).filter(
                User.tnt_plan_type != 'FREE',
                User.tnt_plan_end > datetime.now()
            ).count()

            # Today's usage
            today = date.today()
            today_usage = self.db_session.query(
                func.count(func.distinct(TntUsageTracking.user_id)).label('active_users'),
                func.sum(TntUsageTracking.analysis_count).label('total_analyses')
            ).filter(
                TntUsageTracking.usage_date == today
            ).first()

            return {
                "plan_distribution": [
                    {"plan_type": plan_type, "count": count}
                    for plan_type, count in plan_stats
                ],
                "active_tnt_users": active_tnt_users,
                "today_stats": {
                    "active_users": today_usage.active_users or 0,
                    "total_analyses": today_usage.total_analyses or 0
                },
                "timestamp": datetime.now().isoformat()
            }

        except SQLAlchemyError as e:
            logger.error(f"Error getting TNT statistics: {e}")
            raise


    # === REFERRAL SYSTEM OVERVIEW ===
    def get_referral_overview(self) -> Dict[str, Any]:
        """Get comprehensive referral system overview - REWRITTEN"""
        try:
            # System totals
            total_referrers = self.db_session.query(
                func.count(func.distinct(Commission.referrer_id))
            ).scalar() or 0

            total_commissions = self.db_session.query(Commission).count()
            
            total_amount = self.db_session.query(
                func.sum(Commission.total_amount)
            ).scalar() or 0

            pending_amount = self.db_session.query(
                func.sum(Commission.total_amount)
            ).filter(
                Commission.status == 'pending'
            ).scalar() or 0

            paid_amount = self.db_session.query(
                func.sum(Commission.total_amount)
            ).filter(
                Commission.status == 'paid'
            ).scalar() or 0

            # Top referrers
            top_referrers = self.db_session.query(
                User.user_id,
                User.username,
                User.referral_code,
                func.count(Commission.id).label('total_referrals'),
                func.sum(Commission.total_amount).label('total_earned'),
                func.sum(
                    case((Commission.status == 'pending', Commission.total_amount), else_=0)
                ).label('pending_amount')
            ).join(
                Commission, User.user_id == Commission.referrer_id
            ).group_by(
                User.user_id, User.username, User.referral_code
            ).order_by(
                desc('total_earned')
            ).limit(10).all()

            return {
                "success": True,
                "system_stats": {
                    "total_referrers": total_referrers,
                    "total_commissions": total_commissions,
                    "total_commissions_amount": float(total_amount),
                    "pending_payments": float(pending_amount),
                    "paid_amount": float(paid_amount)
                },
                "referrers": [
                    {
                        "user_id": ref.user_id,
                        "username": ref.username or f"User_{ref.user_id}",
                        "referral_code": ref.referral_code,
                        "total_referrals": ref.total_referrals,
                        "total_earned": float(ref.total_earned),
                        "pending_amount": float(ref.pending_amount)
                    }
                    for ref in top_referrers
                ],
                "timestamp": datetime.now().isoformat()
            }

        except SQLAlchemyError as e:
            logger.error(f"Error getting referral overview: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # === DATABASE CLEANUP ===
    def cleanup_database(self) -> Dict[str, int]:
        """Clean database tables in correct order (respecting foreign keys)"""
        try:
            # Tables in deletion order (foreign key dependencies)
            tables_to_clean = [
                (TntUsageTracking, "tnt_usage_tracking"),
                (ApiRequest, "api_requests"),
                (Transaction, "transactions"),
                (Commission, "commissions"),
                (Referral, "referrals"),
                (User, "users")
            ]
            
            cleanup_results = {}
            
            for model_class, table_name in tables_to_clean:
                # Count before deletion
                before_count = self.db_session.query(model_class).count()
                
                # Delete all records
                deleted_count = self.db_session.query(model_class).delete()
                
                cleanup_results[table_name] = {
                    "before": before_count,
                    "deleted": deleted_count,
                    "remaining": before_count - deleted_count
                }
            
            # Commit all deletions
            self.db_session.commit()
            
            return cleanup_results

        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Error cleaning database: {e}")
            raise

    # === SEQUENCE RESET ===
    def reset_sequences(self) -> bool:
        """Reset auto-increment sequences (PostgreSQL only)"""
        try:
            # Check if we're using PostgreSQL
            if 'postgresql' in str(self.db_session.bind.url):
                sequences = [
                    "users_user_id_seq",
                    "transactions_id_seq",
                    "api_requests_id_seq",
                    "tnt_usage_tracking_id_seq",
                    "referrals_id_seq",
                    "commissions_id_seq"
                ]
                
                for seq_name in sequences:
                    try:
                        self.db_session.execute(
                            text(f"ALTER SEQUENCE {seq_name} RESTART WITH 1")
                        )
                        logger.info(f"✅ Reset sequence: {seq_name}")
                    except SQLAlchemyError as seq_error:
                        logger.warning(f"⚠️ Could not reset sequence {seq_name}: {seq_error}")
                
                self.db_session.commit()
                return True
            else:
                # SQLite handles auto-increment automatically
                logger.info("ℹ️ SQLite detected - sequences reset automatically")
                return True

        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Error resetting sequences: {e}")
            return False

    def get_user_referral_details(self, user_id: int) -> dict:
        """دریافت جزئیات رفرال کاربر"""
        try:
            user = self.db_session.query(User).filter_by(user_id=user_id).first()
            if not user:
                return {"success": False, "error": "کاربر یافت نشد"}
            
            referrals = self.db_session.query(Referral).filter_by(
                referrer_id=user_id
            ).all()
            
            buyers = []
            for ref in referrals:
                if ref.purchased:
                    buyers.append({
                        "username": ref.referred.username or "Unknown",
                        "purchase_date": ref.purchase_date,
                        "commission": ref.commission_amount
                    })
            
            return {
                "success": True,
                "referral_code": f"REF{user_id}",
                "buyers": buyers
            }
        except Exception as e:
            logger.error(f"Error in get_user_referral_details: {e}")
            return {"success": False, "error": str(e)}  

    def create_referral_relationship(self, referral_code: str, new_user_id: int) -> dict:
        """ایجاد رابطه رفرال جدید"""
        try:
            # استخراج referrer_id از کد رفرال
            if not referral_code.startswith("REF"):
                return {"success": False, "error": "کد رفرال نامعتبر"}
            
            # حذف "REF" و "TEMP" از کد
            referrer_part = referral_code[3:]  # حذف REF
            if referrer_part.endswith("TEMP"):
                referrer_part = referrer_part[:-4]  # حذف TEMP
            
            try:
                referrer_id = int(referrer_part)
            except ValueError:
                return {"success": False, "error": "فرمت کد نامعتبر"}
            
            # بررسی وجود referrer
            referrer = self.db_session.query(User).filter_by(user_id=referrer_id).first()
            if not referrer:
                return {"success": False, "error": "کاربر دعوت‌کننده یافت نشد"}
            
            # بررسی تکراری نبودن
            existing = self.db_session.query(Referral).filter_by(
                referrer_id=referrer_id, 
                referred_id=new_user_id
            ).first()
            
            if existing:
                return {"success": False, "error": "رفرال قبلاً ثبت شده"}
            
            # ایجاد رفرال جدید
            new_referral = Referral(
                referrer_id=referrer_id,
                referred_id=new_user_id,
                status='pending'
            )
            
            self.db_session.add(new_referral)
            self.db_session.commit()
            
            return {"success": True, "referrer_id": referrer_id}
            
        except Exception as e:
            self.db_session.rollback()
            return {"success": False, "error": str(e)}  

class TntRepository:
    """Repository for TNT-related operations for users."""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def check_analysis_limit(self, user_id: int) -> dict:
        """
        Checks if a user has reached their daily TNT analysis limit.
        Returns dict with allowed status and details
        """
        try:
            user = self.db_session.query(User).filter_by(user_id=user_id).first()
            if not user or not user.tnt_plan_type or user.tnt_plan_type == 'FREE':
                return {
                    "allowed": False,
                    "reason": "plan_required",
                    "message": "برای استفاده از تحلیل TNT نیاز به اشتراک دارید"
                }
            
            # بررسی انقضای پلن
            if user.tnt_plan_end and datetime.now() > user.tnt_plan_end:
                return {
                    "allowed": False,
                    "reason": "plan_expired",
                    "message": "اشتراک شما منقضی شده است"
                }
            
    # بررسی محدودیت ساعتی و ماهانه از جدول TntUsageTracking
            
            now = datetime.now()
            today = now.date()
            current_hour = now.hour
            
            # محاسبه استفاده ساعتی (ساعت جاری)
            hourly_usage = self.db_session.query(TntUsageTracking).filter_by(
                user_id=user_id,
                usage_date=today,
                usage_hour=current_hour
            ).first()
            
            current_hour_count = hourly_usage.analysis_count if hourly_usage else 0
            
            # محاسبه استفاده ماهانه (30 روز گذشته)
            month_ago = today - timedelta(days=30)
            monthly_usage = self.db_session.query(
                func.sum(TntUsageTracking.analysis_count)
            ).filter(
                TntUsageTracking.user_id == user_id,
                TntUsageTracking.usage_date >= month_ago
            ).scalar() or 0
            
            # بررسی محدودیت‌ها
            if current_hour_count >= user.tnt_hourly_limit:
                return {
                    "allowed": False,
                    "reason": "hourly_limit",
                    "message": "سقف ساعتی به پایان رسیده است",
                    "usage": current_hour_count,
                    "limit": user.tnt_hourly_limit
                }
            
            if monthly_usage >= user.tnt_monthly_limit:
                return {
                    "allowed": False,
                    "reason": "monthly_limit", 
                    "message": "سقف ماهانه به پایان رسیده است",
                    "usage": monthly_usage,
                    "limit": user.tnt_monthly_limit
                }
            
            # اجازه داده شد
            return {
                "allowed": True,
                "remaining_monthly": max(0, user.tnt_monthly_limit - monthly_usage),
                "remaining_hourly": max(0, user.tnt_hourly_limit - current_hour_count)
            }
            
        except Exception as e:
            logger.error(f"Error in check_analysis_limit: {e}")
            return {
                "allowed": False,
                "reason": "error",
                "message": "خطا در بررسی محدودیت"
            }

    def record_analysis_usage(self, user_id: int):
        """
        Records or updates an analysis usage record in the TntUsageTracking table.
        Implements an "upsert" logic.
        """
        try:
            from datetime import datetime
            from .models import TntUsageTracking  # Make sure TntUsageTracking is imported

            now = datetime.now()
            today = now.date()
            current_hour = now.hour

            # Check for an existing record for the current user and hour
            existing_record = self.db_session.query(TntUsageTracking).filter_by(
                user_id=user_id,
                usage_date=today,
                usage_hour=current_hour
            ).first()

            if existing_record:
                # If it exists, increment the analysis count
                existing_record.analysis_count += 1
                logger.info(f"Incremented analysis count for user {user_id} at {today} hour {current_hour}")
            else:
                # If not, create a new record
                new_record = TntUsageTracking(
                    user_id=user_id,
                    usage_date=today,
                    usage_hour=current_hour,
                    analysis_count=1  # Starts at 1
                )
                self.db_session.add(new_record)
                logger.info(f"Created new analysis record for user {user_id} at {today} hour {current_hour}")

            self.db_session.commit()

        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error in record_analysis_usage (upsert): {e}")
            raise

    def get_user_plan(self, user_id: int) -> dict:
        """دریافت اطلاعات پلن فعال کاربر"""
        try:
            user = self.db_session.query(User).filter_by(user_id=user_id).first()
            if not user:
                return {"plan_active": False, "plan_type": "FREE"}
            
            # بررسی وضعیت پلن TNT
            plan_active = False
            if user.tnt_plan_type and user.tnt_plan_type != 'FREE':
                if user.tnt_plan_end:
                    plan_active = datetime.now() <= user.tnt_plan_end
                else:
                    plan_active = True  # پلن دائمی
            
            return {
                "plan_active": plan_active,
                "plan_type": user.tnt_plan_type or "FREE",
                "plan_end": user.tnt_plan_end,
                "monthly_limit": user.tnt_monthly_limit or 0,
                "hourly_limit": user.tnt_hourly_limit or 0
            }
            
        except Exception as e:
            logger.error(f"Error in get_user_plan: {e}")
            return {"plan_active": False, "plan_type": "FREE"}

    def activate_tnt_subscription(self, user_id: int, plan_name: str, duration_days: int) -> dict:
        """فعال‌سازی اشتراک TNT"""
        try:
            user = self.db_session.query(User).filter_by(user_id=user_id).first()
            if not user:
                return {"success": False, "error": "کاربر یافت نشد"}
            
            # دریافت اطلاعات پلن از جدول TntPlan
            plan = self.db_session.query(TntPlan).filter_by(
                plan_name=plan_name, is_active=True
            ).first()
            
            if not plan:
                return {"success": False, "error": "پلن یافت نشد"}
            
            # بروزرسانی اطلاعات کاربر
            user.tnt_plan_type = plan_name
            user.tnt_monthly_limit = plan.monthly_limit
            user.tnt_hourly_limit = plan.hourly_limit
            user.tnt_plan_start = datetime.now()
            user.tnt_plan_end = datetime.now() + timedelta(days=duration_days)
            
            self.db_session.commit()
            
            return {
                "success": True,
                "plan_name": plan_name,
                "end_date": user.tnt_plan_end
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error in activate_tnt_subscription: {e}")
            return {"success": False, "error": str(e)}
