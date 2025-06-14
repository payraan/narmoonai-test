"""
Repository Layer for Database Operations
All business logic and CRUD operations using SQLAlchemy ORM
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import func, and_, or_, desc, case

from .connection import db_manager
from .models import (
    User, Transaction, ApiRequest, TntUsageTracking, TntPlan,
    Referral, Commission, ReferralSetting
)

logger = logging.getLogger(__name__)

class UserRepository:
    """Repository for User operations"""
    
    @staticmethod
    def create_or_update_user(user_id: int, username: str = None) -> User:
        """Create new user or update existing one"""
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            
            if user:
                # Update existing user
                if username:
                    user.username = username
            else:
                # Create new user
                referral_code = User.generate_referral_code(user_id)
                user = User(
                    user_id=user_id,
                    username=username,
                    referral_code=referral_code
                )
                session.add(user)
            
            session.commit()
            session.refresh(user)
            logger.info(f"✅ User {user_id} created/updated with referral code: {user.referral_code}")
            return user
    
    @staticmethod
    def get_user(user_id: int) -> Optional[User]:
        """Get user by ID"""
        with db_manager.get_session() as session:
            return session.query(User).filter(User.user_id == user_id).first()
    
    @staticmethod
    def get_user_by_referral_code(referral_code: str) -> Optional[User]:
        """Get user by referral code"""
        with db_manager.get_session() as session:
            return session.query(User).filter(User.referral_code == referral_code).first()
    
    @staticmethod
    def activate_legacy_subscription(user_id: int, duration_months: int, sub_type: str) -> str:
        """Activate legacy subscription system"""
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            today = date.today()
            end_date = today + timedelta(days=30 * duration_months)
            
            user.subscription_end = end_date
            user.subscription_type = sub_type
            user.is_active = True
            
            session.commit()
            logger.info(f"✅ Legacy subscription activated for user {user_id}")
            return end_date.strftime('%Y-%m-%d')
    
    @staticmethod
    def activate_tnt_subscription(user_id: int, plan_name: str, duration_months: int = 1) -> Dict[str, Any]:
        """Activate TNT subscription"""
        with db_manager.get_session() as session:
            # Get user
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get plan info
            plan = session.query(TntPlan).filter(
                TntPlan.plan_name == plan_name,
                TntPlan.is_active == True
            ).first()
            
            if not plan:
                raise ValueError(f"Plan {plan_name} not found or inactive")
            
            # Calculate dates
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30 * duration_months)
            
            # Update user
            user.tnt_plan_type = plan_name
            user.tnt_monthly_limit = plan.monthly_limit
            user.tnt_hourly_limit = plan.hourly_limit
            user.tnt_plan_start = start_date
            user.tnt_plan_end = end_date
            user.is_active = True
            
            session.commit()
            
            logger.info(f"✅ TNT subscription {plan_name} activated for user {user_id}")
            
            return {
                "success": True,
                "plan_name": plan_name,
                "plan_display": plan.plan_display_name,
                "monthly_limit": plan.monthly_limit,
                "hourly_limit": plan.hourly_limit,
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "vip_access": plan.vip_access
            }
    
    @staticmethod
    def check_legacy_subscription(user_id: int) -> bool:
        """Check if legacy subscription is active"""
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return False
            
            return user.is_legacy_subscription_active()
    
    @staticmethod
    def get_user_info(user_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive user information"""
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return None
            
            # Get recent transactions
            transactions = session.query(Transaction).filter(
                Transaction.user_id == user_id
            ).order_by(desc(Transaction.created_at)).limit(5).all()
            
            return {
                "user_data": user,
                "transactions": transactions
            }
    
    @staticmethod
    def get_user_stats() -> Dict[str, Any]:
        """Get user statistics"""
        with db_manager.get_session() as session:
            today = date.today()
            
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count()
            new_users_today = session.query(User).filter(
                func.date(User.created_at) == today
            ).count()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "new_users_today": new_users_today
            }

class TransactionRepository:
    """Repository for Transaction operations"""
    
    @staticmethod
    def create_transaction(user_id: int, txid: str, wallet_address: str, 
                         amount: float, subscription_type: str) -> Transaction:
        """Create new transaction"""
        with db_manager.get_session() as session:
            transaction = Transaction(
                user_id=user_id,
                txid=txid,
                wallet_address=wallet_address,
                amount=amount,
                subscription_type=subscription_type,
                status='pending'
            )
            
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            
            logger.info(f"✅ Transaction created: {txid} for user {user_id}")
            return transaction
    
    @staticmethod
    def get_monthly_revenue() -> float:
        """Get monthly revenue from completed transactions"""
        with db_manager.get_session() as session:
            today = date.today()
            first_day = today.replace(day=1)
            
            result = session.query(func.sum(Transaction.amount)).filter(
                Transaction.status == 'completed',
                func.date(Transaction.created_at) >= first_day
            ).scalar()
            
            return float(result or 0)

class ApiRequestRepository:
    """Repository for API Request operations"""
    
    @staticmethod
    def log_api_request(user_id: int, endpoint: str):
        """Log API request"""
        with db_manager.get_session() as session:
            api_request = ApiRequest(
                user_id=user_id,
                endpoint=endpoint,
                request_date=date.today()
            )
            
            session.add(api_request)
            session.commit()
            
            logger.debug(f"📊 API request logged: {endpoint} for user {user_id}")
    
    @staticmethod
    def check_api_limit(user_id: int, is_premium: bool = False) -> bool:
        """Check if user has exceeded API limit"""
        with db_manager.get_session() as session:
            today = date.today()
            
            count = session.query(ApiRequest).filter(
                ApiRequest.user_id == user_id,
                ApiRequest.request_date == today
            ).count()
            
            limit = 1000 if is_premium else 20
            return count < limit
    
    @staticmethod
    def get_user_api_stats(user_id: int) -> Dict[str, int]:
        """Get user API usage statistics"""
        with db_manager.get_session() as session:
            today = date.today()
            
            today_count = session.query(ApiRequest).filter(
                ApiRequest.user_id == user_id,
                ApiRequest.request_date == today
            ).count()
            
            total_count = session.query(ApiRequest).filter(
                ApiRequest.user_id == user_id
            ).count()
            
            return {
                "today": today_count,
                "total": total_count
            }

class TntRepository:
    """Repository for TNT (Analysis) system operations"""
    
    @staticmethod
    def get_user_plan(user_id: int) -> Dict[str, Any]:
        """Get user's TNT plan information"""
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            
            if not user:
                return {
                    "plan_type": "FREE",
                    "monthly_limit": 0,
                    "hourly_limit": 0,
                    "plan_active": False,
                    "expired": False
                }
            
            # Check if plan is expired
            plan_active = user.is_tnt_plan_active()
            expired = False
            
            if user.tnt_plan_end and datetime.now() > user.tnt_plan_end:
                expired = True
                # Reset to FREE plan
                user.tnt_plan_type = 'FREE'
                user.tnt_monthly_limit = 0
                user.tnt_hourly_limit = 0
                user.tnt_plan_start = None
                user.tnt_plan_end = None
                user.is_active = False
                session.commit()
                
                return {
                    "plan_type": "FREE",
                    "monthly_limit": 0,
                    "hourly_limit": 0,
                    "plan_active": False,
                    "expired": True
                }
            
            return {
                "plan_type": user.tnt_plan_type or "FREE",
                "monthly_limit": user.tnt_monthly_limit or 0,
                "hourly_limit": user.tnt_hourly_limit or 0,
                "plan_start": user.tnt_plan_start,
                "plan_end": user.tnt_plan_end,
                "plan_active": plan_active,
                "expired": expired
            }
    
    @staticmethod
    def get_monthly_usage(user_id: int) -> int:
        """Get user's monthly TNT usage"""
        with db_manager.get_session() as session:
            now = datetime.now()
            start_of_month = date(now.year, now.month, 1)
            
            usage = session.query(func.sum(TntUsageTracking.analysis_count)).filter(
                TntUsageTracking.user_id == user_id,
                TntUsageTracking.usage_date >= start_of_month
            ).scalar()
            
            return int(usage or 0)
    
    @staticmethod
    def get_hourly_usage(user_id: int) -> int:
        """Get user's current hour TNT usage"""
        with db_manager.get_session() as session:
            now = datetime.now()
            current_date = now.date()
            current_hour = now.hour
            
            usage = session.query(TntUsageTracking.analysis_count).filter(
                TntUsageTracking.user_id == user_id,
                TntUsageTracking.usage_date == current_date,
                TntUsageTracking.usage_hour == current_hour
            ).first()
            
            return int(usage[0] if usage else 0)
    
    @staticmethod
    def record_analysis_usage(user_id: int) -> bool:
        """Record TNT analysis usage"""
        with db_manager.get_session() as session:
            now = datetime.now()
            current_date = now.date()
            current_hour = now.hour
            
            try:
                # Try to get existing record
                usage_record = session.query(TntUsageTracking).filter(
                    TntUsageTracking.user_id == user_id,
                    TntUsageTracking.usage_date == current_date,
                    TntUsageTracking.usage_hour == current_hour
                ).first()
                
                if usage_record:
                    # Update existing record
                    usage_record.analysis_count += 1
                    usage_record.created_at = datetime.now()
                else:
                    # Create new record
                    usage_record = TntUsageTracking(
                        user_id=user_id,
                        usage_date=current_date,
                        usage_hour=current_hour,
                        analysis_count=1
                    )
                    session.add(usage_record)
                
                session.commit()
                logger.info(f"✅ TNT usage recorded for user {user_id}")
                return True
                
            except IntegrityError:
                session.rollback()
                logger.warning(f"⚠️ Duplicate TNT usage record for user {user_id}")
                return True  # Consider it successful as record exists
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"❌ Error recording TNT usage: {e}")
                return False
    
    @staticmethod
    def check_analysis_limit(user_id: int) -> Dict[str, Any]:
        """Check if user can perform TNT analysis"""
        user_plan = TntRepository.get_user_plan(user_id)
        
        # Check if plan is active
        if user_plan["plan_type"] == "FREE":
            return {
                "allowed": False,
                "reason": "plan_required",
                "message": "برای استفاده از تحلیل TNT نیاز به اشتراک دارید"
            }
        
        if user_plan["expired"] or not user_plan["plan_active"]:
            return {
                "allowed": False,
                "reason": "plan_expired",
                "message": "اشتراک شما منقضی شده است"
            }
        
        # Check monthly limit
        monthly_usage = TntRepository.get_monthly_usage(user_id)
        if monthly_usage >= user_plan["monthly_limit"]:
            return {
                "allowed": False,
                "reason": "monthly_limit",
                "message": f"سقف ماهانه شما ({user_plan['monthly_limit']} تحلیل) تمام شده است",
                "usage": monthly_usage,
                "limit": user_plan["monthly_limit"]
            }
        
        # Check hourly limit
        hourly_usage = TntRepository.get_hourly_usage(user_id)
        if hourly_usage >= user_plan["hourly_limit"]:
            return {
                "allowed": False,
                "reason": "hourly_limit",
                "message": f"سقف ساعتی شما ({user_plan['hourly_limit']} تحلیل) تمام شده است",
                "usage": hourly_usage,
                "limit": user_plan["hourly_limit"]
            }
        
        # All checks passed
        return {
            "allowed": True,
            "monthly_usage": monthly_usage,
            "monthly_limit": user_plan["monthly_limit"],
            "hourly_usage": hourly_usage,
            "hourly_limit": user_plan["hourly_limit"],
            "remaining_monthly": user_plan["monthly_limit"] - monthly_usage,
            "remaining_hourly": user_plan["hourly_limit"] - hourly_usage
        }
    
    @staticmethod
    def get_user_usage_stats(user_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive TNT usage statistics for user"""
        user_plan = TntRepository.get_user_plan(user_id)
        if not user_plan:
            return None
        
        monthly_usage = TntRepository.get_monthly_usage(user_id)
        hourly_usage = TntRepository.get_hourly_usage(user_id)
        
        return {
            "plan_info": user_plan,
            "monthly_usage": monthly_usage,
            "hourly_usage": hourly_usage,
            "monthly_remaining": max(0, user_plan["monthly_limit"] - monthly_usage),
            "hourly_remaining": max(0, user_plan["hourly_limit"] - hourly_usage),
            "monthly_percentage": (monthly_usage / user_plan["monthly_limit"] * 100) if user_plan["monthly_limit"] > 0 else 0,
            "hourly_percentage": (hourly_usage / user_plan["hourly_limit"] * 100) if user_plan["hourly_limit"] > 0 else 0
        }
    
    @staticmethod
    def get_all_plans() -> List[TntPlan]:
        """Get all active TNT plans"""
        with db_manager.get_session() as session:
            return session.query(TntPlan).filter(
                TntPlan.is_active == True
            ).order_by(TntPlan.price_usd).all()
    
    @staticmethod
    def get_plan_info(plan_name: str) -> Optional[TntPlan]:
        """Get specific TNT plan information"""
        with db_manager.get_session() as session:
            return session.query(TntPlan).filter(
                TntPlan.plan_name == plan_name,
                TntPlan.is_active == True
            ).first()

class ReferralRepository:
    """Repository for Referral system operations"""
    
    @staticmethod
    def create_referral_relationship(referrer_code: str, referred_user_id: int) -> Dict[str, Any]:
        """Create referral relationship between users"""
        with db_manager.get_session() as session:
            # Find referrer by code
            referrer = session.query(User).filter(
                User.referral_code == referrer_code
            ).first()
            
            if not referrer:
                return {"success": False, "error": "کد رفرال نامعتبر"}
            
            # Prevent self-referral
            if referrer.user_id == referred_user_id:
                return {"success": False, "error": "نمی‌توانید خودتان را دعوت کنید"}
            
            # Check if relationship already exists
            existing = session.query(Referral).filter(
                Referral.referrer_id == referrer.user_id,
                Referral.referred_id == referred_user_id
            ).first()
            
            if existing:
                return {"success": False, "error": "رابطه رفرال قبلاً ثبت شده"}
            
            # Create new referral relationship
            referral = Referral(
                referrer_id=referrer.user_id,
                referred_id=referred_user_id,
                status='pending'
            )
            
            session.add(referral)
            session.commit()
            
            logger.info(f"✅ Referral relationship created: {referrer.user_id} -> {referred_user_id}")
            
            return {
                "success": True,
                "referrer_id": referrer.user_id,
                "message": f"رابطه رفرال بین {referrer.user_id} و {referred_user_id} ثبت شد"
            }
    
    @staticmethod
    def calculate_commission(referrer_id: int, referred_user_id: int, 
                           plan_type: str, transaction_id: Optional[int] = None) -> Dict[str, Any]:
        """Calculate and record commission for successful referral"""
        with db_manager.get_session() as session:
            # Get referrer's custom commission rate
            referrer = session.query(User).filter(User.user_id == referrer_id).first()
            custom_rate = referrer.custom_commission_rate if referrer else None
            
            # Define plan prices (updated for TNT)
            plan_prices = {
                "TNT_MINI": 6.00,
                "TNT_PLUS": 10.00,
                "TNT_MAX": 22.00,
                # Legacy plans
                "ماهانه": 25.00,
                "سه_ماهه": 65.00
            }
            
            plan_price = plan_prices.get(plan_type, 0)
            
            # Calculate base commission (35% default)
            if custom_rate:
                base_commission = plan_price * (custom_rate / 100)
            else:
                base_commission = plan_price * 0.35
            
            # Calculate volume bonus
            successful_referrals = session.query(Commission).filter(
                Commission.referrer_id == referrer_id,
                Commission.status == 'pending'
            ).count() + 1
            
            bonus_amount = 0.00
            if successful_referrals >= 10:
                bonus_amount = 5.00
            elif successful_referrals >= 5:
                bonus_amount = 2.00
            
            total_amount = base_commission + bonus_amount
            
            # Record commission
            commission = Commission(
                referrer_id=referrer_id,
                referred_id=referred_user_id,
                transaction_id=transaction_id,
                plan_type=plan_type,
                commission_amount=base_commission,
                bonus_amount=bonus_amount,
                total_amount=total_amount,
                status='pending'
            )
            
            session.add(commission)
            
            # Update referral status
            referral = session.query(Referral).filter(
                Referral.referrer_id == referrer_id,
                Referral.referred_id == referred_user_id
            ).first()
            
            if referral:
                referral.status = 'completed'
            
            # Update user total earned
            if referrer:
                referrer.total_earned = (referrer.total_earned or 0) + total_amount
            
            session.commit()
            
            logger.info(f"✅ Commission calculated: {referrer_id} -> {referred_user_id}: ${total_amount}")
            
            return {
                "success": True,
                "commission_amount": base_commission,
                "bonus_amount": bonus_amount,
                "total_amount": total_amount,
                "successful_referrals": successful_referrals,
                "plan_price": plan_price,
                "commission_rate": custom_rate if custom_rate else 35
            }
    
    @staticmethod
    def get_referral_stats(user_id: int) -> Dict[str, Any]:
        """Get comprehensive referral statistics for user"""
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            
            if not user:
                return {"success": False, "error": "کاربر یافت نشد"}
            
            # Get successful buyers (commissions)
            buyers = session.query(Commission, User).join(
                User, Commission.referred_id == User.user_id
            ).filter(
                Commission.referrer_id == user_id
            ).order_by(desc(Commission.created_at)).all()
            
            # Get commission statistics
            commission_stats = session.query(
                func.count(Commission.id).label('total_referrals'),
                func.coalesce(func.sum(
                    case((Commission.status == 'pending', Commission.total_amount), else_=0)
                ), 0).label('pending_amount'),
                func.coalesce(func.sum(
                    case((Commission.status == 'paid', Commission.total_amount), else_=0)
                ), 0).label('paid_amount')
            ).filter(Commission.referrer_id == user_id).first()
            
            return {
                "success": True,
                "referral_code": user.referral_code,
                "total_earned": float(user.total_earned or 0),
                "total_paid": float(user.total_paid or 0),
                "pending_amount": float(commission_stats.pending_amount or 0),
                "successful_referrals": commission_stats.total_referrals or 0,
                "custom_commission_rate": user.custom_commission_rate,
                "buyers": [
                    {
                        "username": buyer.User.username or f"User_{buyer.User.user_id}",
                        "user_id": buyer.User.user_id,
                        "plan_type": buyer.Commission.plan_type,
                        "amount": float(buyer.Commission.total_amount),
                        "date": str(buyer.Commission.created_at),
                        "status": buyer.Commission.status
                    }
                    for buyer in buyers
                ]
            }
    
    @staticmethod
    def get_admin_referral_stats() -> Dict[str, Any]:
        """Get comprehensive referral statistics for admin"""
        with db_manager.get_session() as session:
            # Get all referrers with statistics
            referrers_query = session.query(
                User.user_id,
                User.username,
                User.referral_code,
                User.custom_commission_rate,
                User.total_earned,
                User.total_paid,
                func.count(Commission.id).label('total_referrals'),
                func.coalesce(func.sum(
                    (Commission.status == 'pending', Commission.total_amount), 0
                )).label('pending_amount')
            ).outerjoin(
                Commission, User.user_id == Commission.referrer_id
            ).filter(
                or_(User.total_earned > 0, Commission.id.isnot(None))
            ).group_by(
                User.user_id, User.username, User.referral_code,
                User.custom_commission_rate, User.total_earned, User.total_paid
            ).order_by(desc(User.total_earned)).all()
            
            # Get system statistics
            system_stats = session.query(
                func.count(func.distinct(Commission.referrer_id)).label('total_referrers'),
                func.count(Commission.id).label('total_commissions'),
                func.sum(Commission.total_amount).label('total_commissions_amount'),
                func.coalesce(func.sum(
                    (Commission.status == 'pending', Commission.total_amount), 0
                )).label('pending_payments'),
                func.coalesce(func.sum(
                    (Commission.status == 'paid', Commission.total_amount), 0
                )).label('paid_amount')
            ).first()
            
            return {
                "success": True,
                "system_stats": {
                    "total_referrers": system_stats.total_referrers or 0,
                    "total_commissions": system_stats.total_commissions or 0,
                    "total_commissions_amount": float(system_stats.total_commissions_amount or 0),
                    "pending_payments": float(system_stats.pending_payments or 0),
                    "paid_amount": float(system_stats.paid_amount or 0)
                },
                "referrers": [
                    {
                        "user_id": ref.user_id,
                        "username": ref.username or f"User_{ref.user_id}",
                        "referral_code": ref.referral_code,
                        "custom_rate": ref.custom_commission_rate,
                        "total_earned": float(ref.total_earned or 0),
                        "total_paid": float(ref.total_paid or 0),
                        "total_referrals": ref.total_referrals or 0,
                        "pending_amount": float(ref.pending_amount or 0)
                    }
                    for ref in referrers_query
                ]
            }

# Backward compatibility functions
def register_user(user_id: int, username: str = None):
    """Backward compatibility function"""
    return UserRepository.create_or_update_user(user_id, username)

def check_subscription(user_id: int) -> bool:
    """Backward compatibility function"""
    return UserRepository.check_legacy_subscription(user_id)

def activate_subscription(user_id: int, duration_months: int, sub_type: str) -> str:
    """Backward compatibility function"""
    return UserRepository.activate_legacy_subscription(user_id, duration_months, sub_type)

def get_user_info(user_id: int):
    """Backward compatibility function"""
    return UserRepository.get_user_info(user_id)

def save_transaction(user_id: int, txid: str, wallet_address: str, amount: float, subscription_type: str):
    """Backward compatibility function"""
    return TransactionRepository.create_transaction(user_id, txid, wallet_address, amount, subscription_type)

def check_user_api_limit(user_id: int, is_premium: bool = False) -> bool:
    """Backward compatibility function"""
    return ApiRequestRepository.check_api_limit(user_id, is_premium)

def log_api_request(user_id: int, endpoint: str):
    """Backward compatibility function"""
    return ApiRequestRepository.log_api_request(user_id, endpoint)

def get_user_api_stats(user_id: int):
    """Backward compatibility function"""
    return ApiRequestRepository.get_user_api_stats(user_id)

# TNT System backward compatibility
def check_tnt_analysis_limit(user_id: int):
    """Backward compatibility function"""
    return TntRepository.check_analysis_limit(user_id)

def record_tnt_analysis_usage(user_id: int) -> bool:
    """Backward compatibility function"""
    return TntRepository.record_analysis_usage(user_id)

def activate_tnt_subscription(user_id: int, plan_name: str, duration_months: int = 1):
    """Backward compatibility function"""
    return UserRepository.activate_tnt_subscription(user_id, plan_name, duration_months)

def get_user_tnt_plan(user_id: int):
    """Backward compatibility function"""
    return TntRepository.get_user_plan(user_id)

def get_user_tnt_usage_stats(user_id: int):
    """Backward compatibility function"""
    return TntRepository.get_user_usage_stats(user_id)

def get_all_tnt_plans():
    """Backward compatibility function"""
    return TntRepository.get_all_plans()

def get_tnt_plan_info(plan_name: str):
    """Backward compatibility function"""
    return TntRepository.get_plan_info(plan_name)

# Referral system backward compatibility
def create_referral_relationship(referrer_code: str, referred_user_id: int):
    """Backward compatibility function"""
    return ReferralRepository.create_referral_relationship(referrer_code, referred_user_id)

def calculate_commission(referrer_id: int, referred_user_id: int, plan_type: str, transaction_id: int = None):
    """Backward compatibility function"""
    return ReferralRepository.calculate_commission(referrer_id, referred_user_id, plan_type, transaction_id)

def get_referral_stats(user_id: int):
    """Backward compatibility function"""
    return ReferralRepository.get_referral_stats(user_id)

def get_admin_referral_stats():
    """Backward compatibility function"""
    return ReferralRepository.get_admin_referral_stats()
