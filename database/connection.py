"""
Database Connection Management with SQLAlchemy
"""
import os
import logging
from typing import Optional
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from .models import Base, DEFAULT_TNT_PLANS, DEFAULT_REFERRAL_SETTINGS, TntPlan, ReferralSetting

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize database engine based on environment"""
        database_url = os.getenv("DATABASE_URL")
        
        if database_url and database_url.startswith("postgres"):
            # Production: PostgreSQL
            logger.info("🐘 Initializing PostgreSQL connection...")
            
            # Fix postgres:// to postgresql:// for SQLAlchemy 2.0
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            
            self.engine = create_engine(
                database_url,
                poolclass=pool.QueuePool,
                pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,  # 1 hour
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
            logger.info("✅ PostgreSQL engine initialized")
            
        else:
            # Development: SQLite
            logger.info("🗄️ Initializing SQLite connection...")
            sqlite_path = os.getenv("SQLITE_PATH", "bot_database.db")
            
            self.engine = create_engine(
                f"sqlite:///{sqlite_path}",
                poolclass=pool.StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30
                },
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
            logger.info("✅ SQLite engine initialized")
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all tables if they don't exist"""
        try:
            logger.info("🔨 Creating database tables...")
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created successfully")
            
            # Initialize default data
            self._initialize_default_data()
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Error creating tables: {e}")
            raise
    
    def _initialize_default_data(self):
        """Initialize default TNT plans and referral settings"""
        try:
            with self.get_session() as session:
                # Initialize TNT Plans
                existing_plans = session.query(TntPlan).count()
                if existing_plans == 0:
                    logger.info("📋 Initializing default TNT plans...")
                    for plan_data in DEFAULT_TNT_PLANS:
                        plan = TntPlan(**plan_data)
                        session.add(plan)
                    
                    logger.info("✅ Default TNT plans initialized")
                
                # Initialize Referral Settings
                existing_settings = session.query(ReferralSetting).count()
                if existing_settings == 0:
                    logger.info("⚙️ Initializing default referral settings...")
                    for setting_data in DEFAULT_REFERRAL_SETTINGS:
                        setting = ReferralSetting(**setting_data)
                        session.add(setting)
                    
                    logger.info("✅ Default referral settings initialized")
                
                session.commit()
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Error initializing default data: {e}")
            # Don't raise here, let the app continue
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"❌ Database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """Get database session (manual management)"""
        return self.SessionLocal()
    
    def health_check(self) -> dict:
        """Check database connection health"""
        try:
            with self.get_session() as session:
                # Simple query to test connection
                result = session.execute("SELECT 1")
                result.fetchone()
                
                # Get basic stats
                from .models import User, Transaction
                user_count = session.query(User).count()
                transaction_count = session.query(Transaction).count()
                
                return {
                    "status": "healthy",
                    "database_type": "postgresql" if "postgresql" in str(self.engine.url) else "sqlite",
                    "connection_pool_size": self.engine.pool.size() if hasattr(self.engine.pool, 'size') else "N/A",
                    "user_count": user_count,
                    "transaction_count": transaction_count,
                    "url": str(self.engine.url).split('@')[0] + "@****"  # Hide credentials
                }
                
        except SQLAlchemyError as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_type": "postgresql" if "postgresql" in str(self.engine.url) else "sqlite"
            }
    
    def close(self):
        """Close database connections"""
        if self.engine:
            logger.info("🔒 Closing database connections...")
            self.engine.dispose()
            logger.info("✅ Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for backward compatibility
def init_db():
    """Initialize database - compatibility function"""
    db_manager.create_tables()

def get_connection():
    """Get session - compatibility function"""
    return db_manager.get_session_direct()

def get_session():
    """Get session context manager"""
    return db_manager.get_session()

# Session dependency for dependency injection
def get_db_session():
    """Dependency for getting database session"""
    session = db_manager.get_session_direct()
    try:
        yield session
    finally:
        session.close()
