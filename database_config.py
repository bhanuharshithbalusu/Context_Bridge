"""
Database configuration for storing idioms in PostgreSQL
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'contextbridge_idioms',
    'user': 'postgres',
    'password': '',  # Empty password for local PostgreSQL
    'port': 5432
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def create_idiom_tables():
    """Create tables for each language"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    # SQL for creating idiom tables for each language
    languages = ['english', 'hindi', 'telugu', 'chinese', 'german']
    
    try:
        for lang in languages:
            table_name = f"{lang}_idioms"
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                idiom TEXT NOT NULL,
                meaning TEXT NOT NULL,
                username VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(idiom, username)
            );
            
            CREATE INDEX IF NOT EXISTS idx_{lang}_username ON {table_name}(username);
            CREATE INDEX IF NOT EXISTS idx_{lang}_created_at ON {table_name}(created_at);
            """
            cursor.execute(create_table_query)
        
        # Create a summary table to track counts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS idiom_statistics (
                id SERIAL PRIMARY KEY,
                language VARCHAR(50) NOT NULL,
                total_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(language)
            );
        """)
        
        # Initialize statistics for each language
        for lang in languages:
            cursor.execute("""
                INSERT INTO idiom_statistics (language, total_count)
                VALUES (%s, 0)
                ON CONFLICT (language) DO NOTHING;
            """, (lang,))
        
        conn.commit()
        print("✓ All idiom tables created successfully!")
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def add_idiom(language, idiom, meaning, username):
    """Add a new idiom to the appropriate language table"""
    conn = get_db_connection()
    if not conn:
        return {'success': False, 'error': 'Database connection failed'}
    
    cursor = conn.cursor()
    table_name = f"{language}_idioms"
    
    try:
        # Insert idiom
        cursor.execute(f"""
            INSERT INTO {table_name} (idiom, meaning, username)
            VALUES (%s, %s, %s)
            ON CONFLICT (idiom, username) 
            DO UPDATE SET meaning = EXCLUDED.meaning, updated_at = CURRENT_TIMESTAMP
            RETURNING id;
        """, (idiom, meaning, username))
        
        idiom_id = cursor.fetchone()[0]
        
        # Update statistics
        cursor.execute("""
            UPDATE idiom_statistics 
            SET total_count = (SELECT COUNT(*) FROM {})
            WHERE language = %s;
        """.format(table_name), (language,))
        
        conn.commit()
        return {'success': True, 'id': idiom_id, 'message': 'Idiom saved successfully'}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        cursor.close()
        conn.close()

def get_idioms(language, username=None):
    """Get all idioms for a specific language"""
    conn = get_db_connection()
    if not conn:
        return {'success': False, 'error': 'Database connection failed'}
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    table_name = f"{language}_idioms"
    
    try:
        if username:
            cursor.execute(f"""
                SELECT id, idiom, meaning, username, created_at, updated_at 
                FROM {table_name}
                WHERE username = %s
                ORDER BY created_at DESC;
            """, (username,))
        else:
            cursor.execute(f"""
                SELECT id, idiom, meaning, username, created_at, updated_at 
                FROM {table_name}
                ORDER BY created_at DESC;
            """)
        
        idioms = cursor.fetchall()
        return {'success': True, 'idioms': idioms}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        cursor.close()
        conn.close()

def delete_idiom(language, idiom_id, username):
    """Delete an idiom"""
    conn = get_db_connection()
    if not conn:
        return {'success': False, 'error': 'Database connection failed'}
    
    cursor = conn.cursor()
    table_name = f"{language}_idioms"
    
    try:
        cursor.execute(f"""
            DELETE FROM {table_name}
            WHERE id = %s AND username = %s;
        """, (idiom_id, username))
        
        # Update statistics
        cursor.execute("""
            UPDATE idiom_statistics 
            SET total_count = (SELECT COUNT(*) FROM {})
            WHERE language = %s;
        """.format(table_name), (language,))
        
        conn.commit()
        return {'success': True, 'message': 'Idiom deleted successfully'}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        cursor.close()
        conn.close()

def get_statistics():
    """Get idiom count statistics for all languages"""
    conn = get_db_connection()
    if not conn:
        return {'success': False, 'error': 'Database connection failed'}
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT language, total_count, last_updated
            FROM idiom_statistics
            ORDER BY language;
        """)
        
        stats = cursor.fetchall()
        return {'success': True, 'statistics': stats}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        cursor.close()
        conn.close()

def get_training_data(language, min_count=10):
    """Get idioms for model training if threshold is met"""
    stats = get_statistics()
    if not stats['success']:
        return {'success': False, 'error': 'Could not fetch statistics'}
    
    lang_stat = next((s for s in stats['statistics'] if s['language'] == language), None)
    if not lang_stat or lang_stat['total_count'] < min_count:
        return {
            'success': False, 
            'error': f'Not enough idioms. Need {min_count}, have {lang_stat["total_count"] if lang_stat else 0}'
        }
    
    return get_idioms(language)

def search_idioms(language, search_term, username=None):
    """Search for idioms in a specific language"""
    conn = get_db_connection()
    if not conn:
        return {'success': False, 'error': 'Database connection failed'}
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    table_name = f"{language}_idioms"
    
    try:
        # Search in both idiom text and meaning using case-insensitive ILIKE
        if username:
            cursor.execute(f"""
                SELECT id, idiom, meaning, username, created_at, updated_at 
                FROM {table_name}
                WHERE (idiom ILIKE %s OR meaning ILIKE %s)
                  AND username = %s
                ORDER BY 
                    CASE 
                        WHEN idiom ILIKE %s THEN 1  -- Exact match in idiom gets priority
                        WHEN idiom ILIKE %s THEN 2  -- Starting match in idiom
                        WHEN meaning ILIKE %s THEN 3 -- Starting match in meaning
                        ELSE 4
                    END,
                    created_at DESC;
            """, (f'%{search_term}%', f'%{search_term}%', username, 
                  f'{search_term}%', f'{search_term}%', f'{search_term}%'))
        else:
            cursor.execute(f"""
                SELECT id, idiom, meaning, username, created_at, updated_at 
                FROM {table_name}
                WHERE idiom ILIKE %s OR meaning ILIKE %s
                ORDER BY 
                    CASE 
                        WHEN idiom ILIKE %s THEN 1  -- Exact match in idiom gets priority
                        WHEN idiom ILIKE %s THEN 2  -- Starting match in idiom
                        WHEN meaning ILIKE %s THEN 3 -- Starting match in meaning
                        ELSE 4
                    END,
                    created_at DESC;
            """, (f'%{search_term}%', f'%{search_term}%', 
                  f'{search_term}%', f'{search_term}%', f'{search_term}%'))
        
        idioms = cursor.fetchall()
        return {'success': True, 'idioms': idioms}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Initialize database tables
    print("Creating database tables...")
    create_idiom_tables()
    print("\nDatabase setup complete!")
    
    # Display statistics
    stats = get_statistics()
    if stats['success']:
        print("\nCurrent Statistics:")
        for stat in stats['statistics']:
            print(f"  {stat['language'].capitalize()}: {stat['total_count']} idioms")
