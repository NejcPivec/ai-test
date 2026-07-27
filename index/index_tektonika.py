"""
index_tektonika.py
Hitrejše batch indexiranje tektonike v pgvector.
Poženi: python index_tektonika.py
"""

import os
import json
import psycopg2
from pathlib import Path
from psycopg2.extras import Json, execute_values

from embedding_service import EMBED_MODEL, embed_many, vector_to_pg

TEKTONIKA_DIR = Path(__file__).resolve().parents[1] / "tektonika_arhivi"
EMBED_BATCH_SIZE = 128
DB_PAGE_SIZE = 500

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "vac_chatbot",
    "user":     "vac_user",
    "password": "geslo123"
}

IMPORTANT_FIELDS = [
    "naziv", "Signatura PE", "Naslov PE", "Čas nastanka PE",
    "Vsebina PE", "Historiat", "Historiat PE",
    "Količina PE", "Jezik", "Dostopnost", "Nivo popisa",
    "Ime ustvarjalca AG", "tektonicna_pot"
]


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def build_chunk(node: dict) -> str:
    parts = []

    naziv = node.get("naziv", "")
    pot = node.get("pot", "")
    url = node.get("url", "")

    parts.append(f"ID vozlišča: {node.get('id', '')}")
    parts.append(f"Naziv: {naziv}")
    parts.append(f"Tip: {node.get('tip', '')}")
    if pot:
        parts.append(f"Pot: {pot}")
    if node.get("parent_id"):
        parts.append(f"Nadrejeno vozlišče: {node['parent_id']}")
    if node.get("level") is not None:
        parts.append(f"Nivo: {node['level']}")

    details = node.get("details", {})
    if details:
        ordered_fields = IMPORTANT_FIELDS + [
            field for field in details if field not in IMPORTANT_FIELDS
        ]
        for field in ordered_fields:
            val = details.get(field)
            if val is None or val == "":
                continue
            if isinstance(val, (list, dict)):
                val = json.dumps(val, ensure_ascii=False)
            val = str(val).strip()
            if len(val) > 1:
                parts.append(f"{field}: {val}")

    if url:
        parts.append(f"URL: https://vac.sjas.gov.si{url}")

    return "\n".join(parts)


def build_source(node: dict, arhiv_naziv: str) -> str:
    details = node.get("details", {})
    signatura = details.get("Signatura PE", node.get("id", ""))
    return f"{arhiv_naziv} | {signatura}"


def index_file(filepath: str):
    filename = os.path.basename(filepath)
    print(f"\n{'='*60}")
    print(f"📂 Obdelujem: {filename}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    arhiv_naziv = data.get("arhiv", filename)
    nodes = data.get("nodes", [])
    total = len(nodes)

    print(f"   Arhiv: {arhiv_naziv}")
    print(f"   Nodov: {total}")
    print(f"   Embedding model: {EMBED_MODEL}")

    prepared = []
    skipped = 0

    for node in nodes:
        chunk = build_chunk(node)
        if len(chunk.strip()) < 20:
            skipped += 1
            continue

        source = build_source(node, arhiv_naziv)
        prepared.append((source, chunk, node))

    print(f"   Pripravljenih chunkov: {len(prepared)}")
    print(f"   Preskočenih praznih:   {skipped}")

    if not prepared:
        print("   ⚠️ Ni nič za indexirati.")
        return

    conn = get_conn()
    cur = conn.cursor()

    # Počisti stare zapise tega arhiva
    cur.execute("DELETE FROM documents WHERE source LIKE %s", (f"{arhiv_naziv} | %",))
    conn.commit()

    indexed = 0

    for start in range(0, len(prepared), EMBED_BATCH_SIZE):
        batch = prepared[start:start + EMBED_BATCH_SIZE]
        batch_texts = [chunk for _, chunk, _ in batch]
        embeddings = embed_many(batch_texts, batch_size=EMBED_BATCH_SIZE)

        rows = [
            (source, chunk, vector_to_pg(embedding), "tektonika", "vsi", Json(node))
            for (source, chunk, node), embedding in zip(batch, embeddings)
        ]

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

        indexed += len(rows)
        print(f"   ✅ {indexed}/{len(prepared)} indexiranih...")

    cur.close()
    conn.close()

    print(f"\n   📊 Rezultat za {arhiv_naziv}:")
    print(f"      Indexiranih: {indexed}")
    print(f"      Preskočenih: {skipped}")


def main():
    print("🚀 Batch indexiranje tektonike...")
    print(f"   Mapa: {TEKTONIKA_DIR}")
    print(f"   Model: {EMBED_MODEL}")
    print(f"   EMBED_BATCH_SIZE: {EMBED_BATCH_SIZE}")

    if not os.path.exists(TEKTONIKA_DIR):
        print(f"❌ Mapa '{TEKTONIKA_DIR}' ne obstaja!")
        return

    json_files = [f for f in os.listdir(TEKTONIKA_DIR) if f.endswith(".json")]

    if not json_files:
        print("❌ Ni JSON datotek v mapi!")
        return

    print(f"   Najdenih datotek: {len(json_files)}")

    for idx, filename in enumerate(sorted(json_files), 1):
        filepath = os.path.join(TEKTONIKA_DIR, filename)
        print(f"\n[{idx}/{len(json_files)}] {filename}")
        index_file(filepath)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM documents")
    total_docs = cur.fetchone()[0]
    cur.close()
    conn.close()

    print(f"\n🎉 Indexiranje zaključeno! Skupaj dokumentov v bazi: {total_docs}")


if __name__ == "__main__":
    main()
