"""
Database package initialization
"""
from .connection import db_manager, init_db, get_connection, get_session
from .models import Base, User, Transaction, ApiRequest, TntUsageTracking, TntPlan, Referral, Commission, ReferralSetting
from .repository import (
    UserRepository, TransactionRepository, ApiRequestRepository, 
    TntRepository, ReferralRepository,
    # Backward compatibility functions
    register_user, check_subscription, activate_subscription, get_user_info,
    save_transaction, check_user_api_limit, log_api_request, get_user_api_stats,
    check_tnt_analysis_limit, record_tnt_analysis_usage, activate_tnt_subscription,
    get_user_tnt_plan, get_user_tnt_usage_stats, get_all_tnt_plans, get_tnt_plan_info,
    create_referral_relationship, calculate_commission, get_referral_stats, get_admin_referral_stats
)

__all__ = [
    # Core components
    'db_manager', 'init_db', 'get_connection', 'get_session',
    
    # Models
    'Base', 'User', 'Transaction', 'ApiRequest', 'TntUsageTracking', 
    'TntPlan', 'Referral', 'Commission', 'ReferralSetting',
    
    # Repositories
    'UserRepository', 'TransactionRepository', 'ApiRequestRepository',
    'TntRepository', 'ReferralRepository',
    
    # Backward compatibility functions
    'register_user', 'check_subscription', 'activate_subscription', 'get_user_info',
    'save_transaction', 'check_user_api_limit', 'log_api_request', 'get_user_api_stats',
    'check_tnt_analysis_limit', 'record_tnt_analysis_usage', 'activate_tnt_subscription',
    'get_user_tnt_plan', 'get_user_tnt_usage_stats', 'get_all_tnt_plans', 'get_tnt_plan_info',
    'create_referral_relationship', 'calculate_commission', 'get_referral_stats', 'get_admin_referral_stats'
]
