import psycopg2
import time

DB_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def init_db():
    print(f"Connecting to {DB_URL}...")
    while True:
        try:
            conn = psycopg2.connect(DB_URL)
            break
        except Exception as e:
            print(f"Waiting for DB... {e}")
            time.sleep(2)
            
    conn.autocommit = True
    cur = conn.cursor()
    
    print("Enabling pgvector extension...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    print("Ensuring tables exist: knowledge_base, user_chats, board_ideas...")
    
    # Таблица векторов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id bigserial primary key,
            content text,
            embedding vector(1024),
            metadata jsonb
        )
    """)
    
    # Таблица чатов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_chats (
            id uuid primary key default gen_random_uuid(),
            user_id varchar(255) not null,
            thread_id varchar(255) not null,
            role varchar(50) not null,
            content text not null,
            metadata jsonb,
            created_at timestamp with time zone default now()
        )
    """)
    
    # Таблица идей для доски
    cur.execute("""
        CREATE TABLE IF NOT EXISTS board_ideas (
            id uuid primary key default gen_random_uuid(),
            title varchar(255) not null,
            content text,
            status varchar(50) default 'todo',
            cover_type varchar(50),
            created_at timestamp with time zone default now(),
            updated_at timestamp with time zone default now(),
            metadata jsonb
        )
    """)
    
    # Таблица стратегии пользователя
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_strategy (
            id uuid primary key default gen_random_uuid(),
            user_id varchar(255) unique not null,
            positioning text,
            target_audience text,
            customer_pains text,
            triggers text,
            goals text,
            content_architecture jsonb,
            shorts_structure jsonb,
            cases text,
            monetization jsonb,
            shorts_logic jsonb,
            full_context text,
            content_plan_config jsonb,
            updated_at timestamp with time zone default now()
        )
    """)
    
    # Пытаемся добавить колонки если их нет (для миграции)
    try:
        cur.execute("ALTER TABLE user_strategy ADD COLUMN IF NOT EXISTS goals text")
        cur.execute("ALTER TABLE user_strategy ADD COLUMN IF NOT EXISTS content_architecture jsonb")
        cur.execute("ALTER TABLE user_strategy ADD COLUMN IF NOT EXISTS shorts_structure jsonb")
        cur.execute("ALTER TABLE user_strategy ADD COLUMN IF NOT EXISTS cases text")
        cur.execute("ALTER TABLE user_strategy ADD COLUMN IF NOT EXISTS monetization jsonb")
        cur.execute("ALTER TABLE user_strategy ADD COLUMN IF NOT EXISTS shorts_logic jsonb")
        cur.execute("ALTER TABLE user_strategy ADD COLUMN IF NOT EXISTS full_context text")
    except:
        pass
    
    print("Creating match_documents function...")
    cur.execute("""
        CREATE OR REPLACE FUNCTION match_documents (
            query_embedding vector(1024),
            match_threshold float,
            match_count int,
            filter jsonb default '{}'
        )
        RETURNS TABLE (
            id bigint,
            content text,
            metadata jsonb,
            similarity float
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                knowledge_base.id,
                knowledge_base.content,
                knowledge_base.metadata,
                1 - (knowledge_base.embedding <=> query_embedding) AS similarity
            FROM knowledge_base
            WHERE 1 - (knowledge_base.embedding <=> query_embedding) > match_threshold
                AND (
                    filter = '{}'::jsonb
                    OR knowledge_base.metadata @> filter
                )
            ORDER BY knowledge_base.embedding <=> query_embedding
            LIMIT match_count;
        END;
        $$;
    """)
    
    print("Local database initialized successfully!")
    cur.close()
    conn.close()

if __name__ == "__main__":
    init_db()
