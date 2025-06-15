# کد نهایی، ساده‌شده و صحیح برای coach_usage_migration.py
import sys
import os
from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, BigInteger, Date,
    ForeignKey, UniqueConstraint
)
from dotenv import load_dotenv

# خواندن متغیرها از فایل .env
load_dotenv()

# خواندن مستقیم DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in your .env file or the line is commented out.")

def run_migration():
    """Creates the 'coach_usage' table in the database."""
    sync_db_url = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    
    engine = create_engine(sync_db_url)
    meta = MetaData()

    print("Checking for 'coach_usage' table...")

    coach_usage_table = Table(
        'coach_usage', meta,
        Column('id', Integer, primary_key=True, index=True),
        Column('user_id', BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        Column('usage_date', Date, nullable=False),
        Column('message_count', Integer, default=1, nullable=False),
        UniqueConstraint('user_id', 'usage_date', name='_user_date_uc')
    )

    try:
        meta.create_all(engine, tables=[coach_usage_table], checkfirst=True)
        print("\n✅ 'coach_usage' table created successfully or already exists.")
        print("✅ Phase 1 is now complete!")
    except Exception as e:
        print(f"\nAn error occurred during migration: {e}")

if __name__ == "__main__":
    run_migration()
