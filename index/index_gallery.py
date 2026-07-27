"""
index_gallery.py
Indexira virtualne razstave (corpus='gallery') v pgvector.
Poženi: python index_gallery.py
"""

import os
from pathlib import Path
from psycopg2.extras import Json, execute_values

from db_service import get_conn, init_db
from embedding_service import EMBED_MODEL, embed_many, vector_to_pg

GALLERY_FILE = Path(__file__).resolve().parents[1] / "docs/virtualne-razstave.md"
DB_PAGE_SIZE = 500
CORPUS = "gallery"
MAX_CHUNK_CHARS = 2000

init_db()


def chunk_gallery(text: str, source: str) -> list[dict]:
    """
    Razreže virtualne razstave po ## naslovih.
    Vsaka razstava dobi svoj chunk.
    """
    chunks = []
    current_heading = "Uvod"
    current_lines = []
    lines = text.split('\n')
    i = 0

    # Preskoči frontmatter
    if lines and lines[0].strip() == '---':
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            i += 1
        i += 1

    def save_section():
        content = '\n'.join(current_lines).strip()
        if content and len(content) > 30:
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            part = []
            part_length = 0
            for paragraph in paragraphs:
                if part and part_length + len(paragraph) + 2 > MAX_CHUNK_CHARS:
                    part_text = '\n\n'.join(part)
                    chunks.append({
                        'heading': current_heading,
                        'content': f"## {current_heading}\n\n{part_text}",
                        'source': source,
                        'visibility': 'vsi',
                    })
                    part = []
                    part_length = 0
                part.append(paragraph)
                part_length += len(paragraph) + 2
            if part:
                part_text = '\n\n'.join(part)
                chunks.append({
                    'heading': current_heading,
                    'content': f"## {current_heading}\n\n{part_text}",
                    'source': source,
                    'visibility': 'vsi',
                })

    for line in lines[i:]:
        if line.startswith('## '):
            save_section()
            current_heading = line.replace('## ', '').strip()
            current_lines = []
        else:
            current_lines.append(line)

    save_section()
    return chunks


def index_gallery():
    if not os.path.exists(GALLERY_FILE):
        print(f"⚠️ Ne najdem: {GALLERY_FILE}")
        print("   Najprej poženi: python scrape-virtualne-razstave.py")
        return

    print(f"\nIndexiram: {GALLERY_FILE}")
    print(f"  → Embedding model: {EMBED_MODEL}")
    print(f"  → Corpus: {CORPUS}")

    source = os.path.basename(GALLERY_FILE)

    with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    chunks = chunk_gallery(content, source)
    print(f"  → Chunkov: {len(chunks)}")

    if not chunks:
        print("  ⚠️ Ni chunkov za indexiranje")
        return

    embed_inputs = [f"{chunk['heading']}\n\n{chunk['content']}" for chunk in chunks]
    embeddings = embed_many(embed_inputs)

    rows = [
        (source, chunk['content'], vector_to_pg(embedding), CORPUS, chunk['visibility'], Json(chunk))
        for chunk, embedding in zip(chunks, embeddings)
    ]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM documents WHERE corpus = %s", (CORPUS,))

    execute_values(
        cur,
        """
        INSERT INTO documents (source, chunk, embedding, corpus, visibility, metadata)
        VALUES %s
        """,
        rows,
        template="(%s, %s, %s::vector, %s, %s, %s)",
        page_size=DB_PAGE_SIZE
    )

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Gallery indexirana! ({len(rows)} chunkov)")
    print("\n🎉 Indexiranje gallery končano!")


if __name__ == "__main__":
    index_gallery()
