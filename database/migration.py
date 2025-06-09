from sqlalchemy import text
from .connection import get_session

def run_migration():
    """اجرای migration برای اضافه کردن column های جدید"""
    session = get_session()
    try:
        # اضافه کردن column های جدید اگر وجود نداشتن
        migration_queries = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tnt_plan_type VARCHAR(20) DEFAULT 'free'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tnt_monthly_limit INTEGER DEFAULT 0", 
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tnt_hourly_limit INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code VARCHAR(50)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS custom_commission_rate DECIMAL(5,2)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS total_earned DECIMAL(10,2) DEFAULT 0.00",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS total_paid DECIMAL(10,2) DEFAULT 0.00",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tnt_plan_start TIMESTAMP",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tnt_plan_end TIMESTAMP"
        ]
        
        for query in migration_queries:
            session.execute(text(query))
        
        session.commit()
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        session.close()
