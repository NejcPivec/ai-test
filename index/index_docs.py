import os
from pathlib import Path
from psycopg2.extras import Json, execute_values

from db_service import get_conn, init_db
from embedding_service import EMBED_MODEL, embed_many, vector_to_pg

MAX_CHUNK_CHARS = 2000
DB_PAGE_SIZE = 500
CORPUS = "docs"
BASE_DIR = Path(__file__).resolve().parents[1]

init_db()


def split_if_too_long(chunk: dict) -> list[dict]:
    content = chunk['content']
    if len(content) <= MAX_CHUNK_CHARS:
        return [chunk]

    parts = []
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    current = []
    current_length = 0

    def flush():
        if not current:
            return
        part_text = '\n\n'.join(current)
        parts.append({
            **chunk,
            'heading': f"{chunk['heading']} (del {len(parts)+1})",
            'content': f"## {chunk['heading']}\n\n{part_text}",
        })

    for paragraph in paragraphs:
        if current and current_length + len(paragraph) + 2 > MAX_CHUNK_CHARS:
            flush()
            current = []
            current_length = 0

        if len(paragraph) > MAX_CHUNK_CHARS:
            words = paragraph.split()
            for i in range(0, len(words), 260):
                part = ' '.join(words[i:i + 260])
                if part:
                    if current:
                        flush()
                        current = []
                        current_length = 0
                    current.append(part)
                    current_length = len(part)
                    flush()
                    current = []
                    current_length = 0
        else:
            current.append(paragraph)
            current_length += len(paragraph) + 2

    flush()

    print(f"    ↳ Sekcija predolga → razrezana na {len(parts)} delov")
    return parts


def chunk_by_headings(text: str, source: str) -> list[dict]:
    chunks = []
    current_heading = "Uvod"
    current_lines = []

    vloga = "vsi"
    stran = ""
    lines = text.split('\n')
    i = 0

    if lines and lines[0].strip() == '---':
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            line = lines[i].strip()
            if line.startswith('vloga:'):
                vloga = line.replace('vloga:', '').strip()
            elif line.startswith('stran:'):
                stran = line.replace('stran:', '').strip()
            i += 1
        i += 1

    def save_section():
        content = '\n'.join(current_lines).strip()
        if content and len(content) > 30:
            chunk = {
                'heading': current_heading,
                'content': f"## {current_heading}\n\n{content}",
                'source': source,
                'vloga': vloga,
                'stran': stran,
            }
            chunks.extend(split_if_too_long(chunk))

    for line in lines[i:]:
        if line.startswith('## '):
            save_section()
            current_heading = line.replace('## ', '').strip()
            current_lines = []
        else:
            current_lines.append(line)

    save_section()
    return chunks


def chunk_by_words(text: str, source: str, size: int = 150, overlap: int = 20) -> list[dict]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunk = ' '.join(words[i:i + size])
        if chunk.strip():
            chunks.append({
                'heading': f"Del {len(chunks)+1}",
                'content': chunk,
                'source': source,
                'vloga': 'vsi',
                'stran': '',
            })
    return chunks


def normalize_visibility(vloga: str) -> str:
    """Map document front matter to the retrieval visibility contract."""
    values = {value.strip().lower() for value in (vloga or "vsi").split(",")}
    if "napredni_uporabnik" in values and "končni_uporabnik" not in values:
        return "nu"
    if "končni_uporabnik" in values and "napredni_uporabnik" not in values:
        return "ku"
    return "vsi"


def index_file(filepath: str):
    print(f"\nIndexiram: {filepath}")
    print(f"  → Embedding model: {EMBED_MODEL}")
    print(f"  → Corpus: {CORPUS}")
    source = os.path.basename(filepath)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if str(filepath).endswith('.md'):
        chunks = chunk_by_headings(content, source)
        print(f"  → Strategija: po naslovih | {len(chunks)} sekcij")
    else:
        chunks = chunk_by_words(content, source)
        print(f"  → Strategija: po besedah | {len(chunks)} kosov")

    if not chunks:
        print("  ⚠️ Ni chunkov za indexiranje")
        return

    embed_inputs = [f"{chunk['heading']}\n\n{chunk['content']}" for chunk in chunks]
    embeddings = embed_many(embed_inputs)

    rows = [
        (source, chunk['content'], vector_to_pg(embedding), CORPUS,
         normalize_visibility(chunk.get('vloga', 'vsi')), Json(chunk))
        for chunk, embedding in zip(chunks, embeddings)
    ]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM documents WHERE source = %s AND corpus = %s", (source, CORPUS))

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
    print(f"✅ {source} indexiran! ({len(rows)} chunkov)")


files = [
    BASE_DIR / "docs/about-VAC.md",
    BASE_DIR / "docs/vac_chatbot_znanje.md",
    BASE_DIR / "docs/vac_instructions.md",
    BASE_DIR / "docs/vac_navodila_clean.md",
]

for f in files:
    if os.path.exists(f):
        index_file(f)
    else:
        print(f"⚠️ Ne najdem: {f}")

print("\n🎉 Indexiranje docs končano!")
