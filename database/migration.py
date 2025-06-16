from sqlalchemy import text
from .connection import db_manager

def run_migration():
    """Legacy migration - SQLAlchemy handles table creation automatically"""
    print("ℹ️ Database tables are created automatically by SQLAlchemy")
    print("ℹ️ See database/connection.py -> create_tables()")
    return True

def manual_schema_update():
    """Manual schema updates if needed in future"""
    try:
        with db_manager.get_session() as session:
            # Add manual schema updates here if needed
            print("🔧 No manual updates needed")
            session.commit()
            return True
    except Exception as e:
        print(f"❌ Manual update failed: {e}")
        return False
