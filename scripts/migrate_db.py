"""
Database migration script.
Creates all tables from schemas/db.schema.sql.
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

def convert_postgres_to_sqlite(sql: str) -> str:
    """Convert Postgres SQL to SQLite-compatible SQL."""
    # Replace JSONB with TEXT
    sql = sql.replace("JSONB", "TEXT")
    sql = sql.replace("::jsonb", "")
    sql = sql.replace("'{}'::jsonb", "'{}'")
    sql = sql.replace("'[]'::jsonb", "'[]'")
    
    # Replace TIMESTAMPTZ with TEXT (store ISO 8601 strings)
    sql = sql.replace("TIMESTAMPTZ", "TEXT")
    
    # Replace BIGSERIAL with INTEGER
    sql = sql.replace("BIGSERIAL", "INTEGER")
    
    # SQLite doesn't support IF NOT EXISTS on indexes in older versions
    # But modern SQLite does, so keep it
    
    return sql

def run_migrations(database_url: str = None):
    """
    Run database migrations from schemas/db.schema.sql.
    """
    if database_url is None:
        database_url = os.getenv("DATABASE_URL", "sqlite:///./data/et_heatmap.db")
    
    # Ensure data directory exists for SQLite
    if database_url.startswith("sqlite"):
        os.makedirs("data", exist_ok=True)
    
    is_sqlite = database_url.startswith("sqlite")
    
    # Create engine with appropriate settings
    if is_sqlite:
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(database_url)
    
    schema_file = Path(__file__).parent.parent / "schemas" / "db.schema.sql"
    
    if not schema_file.exists():
        print(f"Error: Schema file not found at {schema_file}")
        sys.exit(1)
    
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    # Convert to SQLite if needed
    if is_sqlite:
        schema_sql = convert_postgres_to_sqlite(schema_sql)
    
    with engine.connect() as conn:
        # Split SQL into statements (split by semicolon followed by whitespace/newline)
        # But preserve multi-line statements
        statements = []
        current_stmt = []
        
        for line in schema_sql.split('\n'):
            stripped = line.strip()
            # Skip empty lines and comments
            if not stripped or stripped.startswith('--'):
                if current_stmt:
                    current_stmt.append('')
                continue
            
            current_stmt.append(line)
            
            # Check if line ends with semicolon (statement complete)
            if stripped.endswith(';'):
                stmt = '\n'.join(current_stmt).strip()
                if stmt:
                    statements.append(stmt)
                current_stmt = []
        
        # Handle any remaining statement
        if current_stmt:
            stmt = '\n'.join(current_stmt).strip()
            if stmt:
                statements.append(stmt)
        
        # Separate CREATE TABLE from CREATE INDEX statements
        create_table_statements = []
        create_index_statements = []
        other_statements = []
        
        for stmt in statements:
            stmt_upper = stmt.upper().strip()
            if stmt_upper.startswith('CREATE TABLE'):
                create_table_statements.append(stmt)
            elif stmt_upper.startswith('CREATE INDEX') or stmt_upper.startswith('CREATE UNIQUE INDEX'):
                create_index_statements.append(stmt)
            elif not stmt_upper.startswith('--'):
                other_statements.append(stmt)
        
        # Check existing tables
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        
        executed = 0
        skipped = 0
        errors = []
        
        # Execute CREATE TABLE statements first
        for statement in create_table_statements:
            try:
                conn.execute(text(statement))
                executed += 1
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    skipped += 1
                else:
                    errors.append((statement[:50], error_msg))
                    print(f"Warning: {error_msg}")
        
        # Execute other statements (ALTER TABLE, etc.)
        for statement in other_statements:
            try:
                conn.execute(text(statement))
                executed += 1
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    skipped += 1
                else:
                    errors.append((statement[:50], error_msg))
                    print(f"Warning: {error_msg}")
        
        # Execute CREATE INDEX statements last
        for statement in create_index_statements:
            try:
                conn.execute(text(statement))
                executed += 1
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    skipped += 1
                else:
                    errors.append((statement[:50], error_msg))
                    print(f"Warning: {error_msg}")
        
        conn.commit()
    
    print(f"\nMigration complete!")
    print(f"  - Executed: {executed} statements")
    print(f"  - Skipped (already exists): {skipped} statements")
    if errors:
        print(f"  - Errors: {len(errors)} statements")
        for stmt, err in errors:
            print(f"    {stmt}... -> {err}")
    else:
        print(f"  - Errors: 0")
    print(f"\nDatabase URL: {database_url}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("--url", help="Database URL (overrides DATABASE_URL env var)")
    args = parser.parse_args()
    
    run_migrations(args.url)
