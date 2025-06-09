"""
SQLAlchemy Models for Narmoon Trading Bot
"""
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, Boolean, 
    Numeric, Date, ForeignKey, UniqueConstraint, Index,
    func, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date
import secrets
import string

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    # Primary fields
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    
    # Legacy subscription system (maintained for compatibility)
    subscription_end = Column(Date)
    subscription_type = Column(String(100))
    is_active = Column(Boolean, default=False)
    
    # TNT Plan System (new)
    tnt_plan_type = Column(String(50), default='FREE')
    tnt_monthly_limit = Column(Integer, default=0)
    tnt_hourly_limit = Column(Integer, default=0)
    tnt_plan_start = Column(DateTime)
    tnt_plan_end = Column(DateTime)
    
    # Referral System
    referral_code = Column(String(50), unique=True)
    custom_commission_rate = Column(Numeric(5, 2))
    total_earned = Column(Numeric(10, 2), default=0.00)
    total_paid = Column(Numeric(10, 2), default=0.00)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    api_requests = relationship("ApiRequest", back_populates="user")
    tnt_usage = relationship("TntUsageTracking", back_populates="user")
    
    # Referral relationships
    referred_by = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred_user")
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer_user")
    commissions_earned = relationship("Commission", foreign_keys="Commission.referrer_id", back_populates="referrer")
    
    # Indexes
    __table_args__ = (
        Index('idx_users_subscription', 'subscription_end', 'is_active'),
        Index('idx_users_tnt_plan', 'tnt_plan_type', 'tnt_plan_end'),
        Index('idx_users_referral_code', 'referral_code'),
    )
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username}, tnt_plan={self.tnt_plan_type})>"
    
    @classmethod
    def generate_referral_code(cls, user_id):
        """Generate unique referral code"""
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        return f"REF{user_id}{random_part}"
    
    def is_tnt_plan_active(self):
        """Check if TNT plan is currently active"""
        if self.tnt_plan_type == 'FREE':
            return False
        if not self.tnt_plan_end:
            return True  # Permanent plan
        return datetime.now() <= self.tnt_plan_end
    
    def is_legacy_subscription_active(self):
        """Check if legacy subscription is active"""
        if not self.is_active or not self.subscription_end:
            return False
        return date.today() <= self.subscription_end

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'))
    txid = Column(String(255))
    wallet_address = Column(String(255))
    amount = Column(Numeric(10, 2))
    subscription_type = Column(String(100))
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    commissions = relationship("Commission", back_populates="transaction")
    
    # Indexes
    __table_args__ = (
        Index('idx_transactions_user_id', 'user_id'),
        Index('idx_transactions_status', 'status'),
        Index('idx_transactions_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, status={self.status})>"

class ApiRequest(Base):
    __tablename__ = 'api_requests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'))
    endpoint = Column(String(255))
    request_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_requests")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_requests_date', 'user_id', 'request_date'),
    )
    
    def __repr__(self):
        return f"<ApiRequest(id={self.id}, user_id={self.user_id}, endpoint={self.endpoint})>"

class TntUsageTracking(Base):
    __tablename__ = 'tnt_usage_tracking'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'))
    usage_date = Column(Date, nullable=False)
    usage_hour = Column(Integer, nullable=False)
    analysis_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tnt_usage")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'usage_date', 'usage_hour', name='unique_user_hour_usage'),
        Index('idx_usage_tracking_user_date', 'user_id', 'usage_date'),
        Index('idx_usage_tracking_user_hour', 'user_id', 'usage_date', 'usage_hour'),
    )
    
    def __repr__(self):
        return f"<TntUsageTracking(user_id={self.user_id}, date={self.usage_date}, hour={self.usage_hour})>"

class TntPlan(Base):
    __tablename__ = 'tnt_plans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_name = Column(String(50), unique=True, nullable=False)
    plan_display_name = Column(String(100), nullable=False)
    price_usd = Column(Numeric(10, 2), nullable=False)
    monthly_limit = Column(Integer, nullable=False)
    hourly_limit = Column(Integer, nullable=False)
    vip_access = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_tnt_plans_active', 'plan_name', 'is_active'),
    )
    
    def __repr__(self):
        return f"<TntPlan(name={self.plan_name}, price=${self.price_usd})>"

class Referral(Base):
    __tablename__ = 'referrals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'))
    referred_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'))
    created_at = Column(DateTime, default=func.now())
    status = Column(String(50), default='pending')
    
    # Relationships
    referrer_user = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred_user = relationship("User", foreign_keys=[referred_id], back_populates="referred_by")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('referrer_id', 'referred_id', name='unique_referral_relationship'),
        Index('idx_referrals_referrer', 'referrer_id'),
        Index('idx_referrals_referred', 'referred_id'),
    )
    
    def __repr__(self):
        return f"<Referral(referrer={self.referrer_id}, referred={self.referred_id}, status={self.status})>"

class Commission(Base):
    __tablename__ = 'commissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'))
    referred_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'))
    transaction_id = Column(Integer, ForeignKey('transactions.id', ondelete='SET NULL'))
    plan_type = Column(String(100), nullable=False)
    commission_amount = Column(Numeric(10, 2), nullable=False)
    bonus_amount = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=func.now())
    paid_at = Column(DateTime)
    
    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="commissions_earned")
    transaction = relationship("Transaction", back_populates="commissions")
    
    # Indexes
    __table_args__ = (
        Index('idx_commissions_referrer', 'referrer_id', 'status'),
        Index('idx_commissions_status', 'status'),
    )
    
    def __repr__(self):
        return f"<Commission(referrer={self.referrer_id}, amount=${self.total_amount}, status={self.status})>"

class ReferralSetting(Base):
    __tablename__ = 'referral_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ReferralSetting(key={self.setting_key}, value={self.setting_value})>"

# Default data initialization
DEFAULT_TNT_PLANS = [
    {
        'plan_name': 'FREE',
        'plan_display_name': 'رایگان',
        'price_usd': 0.00,
        'monthly_limit': 0,
        'hourly_limit': 0,
        'vip_access': False
    },
    {
        'plan_name': 'TNT_MINI',
        'plan_display_name': 'TNT MINI',
        'price_usd': 6.00,
        'monthly_limit': 60,
        'hourly_limit': 2,
        'vip_access': False
    },
    {
        'plan_name': 'TNT_PLUS',
        'plan_display_name': 'TNT PLUS+',
        'price_usd': 10.00,
        'monthly_limit': 150,
        'hourly_limit': 4,
        'vip_access': False
    },
    {
        'plan_name': 'TNT_MAX',
        'plan_display_name': 'TNT MAX',
        'price_usd': 22.00,
        'monthly_limit': 400,
        'hourly_limit': 8,
        'vip_access': True
    }
]

DEFAULT_REFERRAL_SETTINGS = [
    {'setting_key': 'min_withdrawal_amount', 'setting_value': '20.00'},
    {'setting_key': 'default_commission_rate', 'setting_value': '35.00'},
    {'setting_key': 'bonus_threshold_5', 'setting_value': '2.00'},
    {'setting_key': 'bonus_threshold_10', 'setting_value': '5.00'},
]
