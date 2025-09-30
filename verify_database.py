"""
Verify database tables and connections
Run from project root: uv run python verify_database.py
"""

from sqlalchemy import inspect, text
from app.database import engine, check_db_connection
from models import Ticket, Interaction, ConversationHistory, MediaFile, FileAttachment

def verify_database():
    """Verify database connection and tables"""
    
    print("=" * 60)
    print("Database Verification")
    print("=" * 60)
    
    # Check connection
    print("\n1. Checking database connection...")
    if check_db_connection():
        print("   ✅ Database connection successful")
    else:
        print("   ❌ Database connection failed")
        return
    
    # Get inspector
    inspector = inspect(engine)
    
    # Check tables
    print("\n2. Checking tables...")
    tables = inspector.get_table_names()
    
    expected_tables = [
        "tickets",
        "interactions",
        "conversation_history",
        "media_files",
        "file_attachments",
        "alembic_version"  # Alembic's version tracking table
    ]
    
    for table in expected_tables:
        if table in tables:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} - MISSING")
    
    # Check columns for each main table
    print("\n3. Checking table structures...")
    
    model_tables = [
        ("tickets", Ticket),
        ("interactions", Interaction),
        ("conversation_history", ConversationHistory),
        ("media_files", MediaFile),
        ("file_attachments", FileAttachment),
    ]
    
    for table_name, model in model_tables:
        if table_name in tables:
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            print(f"\n   {table_name}: {len(columns)} columns")
            print(f"   Sample columns: {', '.join(columns[:5])}...")
    
    # Check foreign keys
    print("\n4. Checking foreign key relationships...")
    
    fk_tables = ["interactions", "conversation_history", "media_files", "file_attachments"]
    for table in fk_tables:
        if table in tables:
            fks = inspector.get_foreign_keys(table)
            if fks:
                print(f"   ✅ {table}: {len(fks)} foreign key(s)")
                for fk in fks:
                    print(f"      → {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            else:
                print(f"   ⚠️  {table}: No foreign keys found")
    
    # Check indexes
    print("\n5. Checking indexes...")
    index_count = 0
    for table in expected_tables[:-1]:  # Skip alembic_version
        if table in tables:
            indexes = inspector.get_indexes(table)
            index_count += len(indexes)
    
    print(f"   ✅ Total indexes created: {index_count}")
    
    # Get current Alembic version
    print("\n6. Checking migration version...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.fetchone()
            if version:
                print(f"   ✅ Current migration: {version[0]}")
            else:
                print("   ⚠️  No migration version found")
    except Exception as e:
        print(f"   ❌ Error checking version: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Database verification complete!")
    print("=" * 60)

if __name__ == "__main__":
    verify_database()