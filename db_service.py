import json
import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "vac_chatbot",
    "user": "vac_user",
    "password": "geslo123"
}

EMBED_DIM = 384


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id          SERIAL PRIMARY KEY,
            user_id     VARCHAR(100),
            user_type   VARCHAR(10),
            question    TEXT,
            answer      TEXT,
            rating      INTEGER DEFAULT 0,
            comment     TEXT,
            guard_flags TEXT,
            created_at  TIMESTAMP DEFAULT NOW()
        );
    """)

    # Migracija session_id → user_id
    cur.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='chat_history' AND column_name='session_id'
            ) THEN
                ALTER TABLE chat_history RENAME COLUMN session_id TO user_id;
            END IF;
        END
        $$;
    """)

    cur.execute("""
        ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS guard_flags TEXT;
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_chat_history_user_id
        ON chat_history (user_id, created_at DESC);
    """)

    # Documents tabela s corpus stolpcem
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS documents (
            id        SERIAL PRIMARY KEY,
            source    VARCHAR(200),
            chunk     TEXT,
            embedding vector({EMBED_DIM}),
            corpus    VARCHAR(20) DEFAULT 'docs',
            visibility VARCHAR(10) DEFAULT 'vsi',
            metadata  JSONB
        );
    """)

    # Migracija za obstoječe documents tabele brez corpus stolpca
    cur.execute("""
        ALTER TABLE documents ADD COLUMN IF NOT EXISTS corpus VARCHAR(20) DEFAULT 'docs';
    """)

    cur.execute("""
        ALTER TABLE documents ADD COLUMN IF NOT EXISTS visibility VARCHAR(10) DEFAULT 'vsi';
    """)

    cur.execute("""
        ALTER TABLE documents ADD COLUMN IF NOT EXISTS metadata JSONB;
    """)

    cur.execute("""
        UPDATE documents SET visibility = 'vsi'
        WHERE visibility IS NULL OR visibility NOT IN ('ku', 'nu', 'vsi');
    """)

    # Posodobi obstoječe vrstice kjer corpus še ni nastavljen
    cur.execute("""
        UPDATE documents SET corpus = 'tektonika'
        WHERE corpus = 'docs' AND source LIKE '%|%';
    """)

    # Indeks za hitrejše iskanje po corpusu
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_corpus
        ON documents (corpus);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_visibility
        ON documents (visibility);
    """)

    conn.commit()
    cur.close()
    conn.close()
    print(f"Baza inicializirana (embedding dim = {EMBED_DIM})")


def save_message(user_id, user_type, question, answer, guard_flags: dict | None = None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    flags_json = json.dumps(guard_flags, ensure_ascii=False) if guard_flags else None
    cur.execute("""
        INSERT INTO chat_history (user_id, user_type, question, answer, guard_flags)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    """, (user_id, user_type, question, answer, flags_json))
    message_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return message_id


def save_rating(message_id: int, rating: int, comment: str = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE chat_history SET rating = %s, comment = %s WHERE id = %s
    """, (rating, comment, message_id))
    conn.commit()
    cur.close()
    conn.close()
