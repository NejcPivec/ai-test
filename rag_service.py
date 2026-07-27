import re
import unicodedata

from db_service import get_conn
from embedding_service import EMBED_MODEL, embed_text, vector_to_pg
from reranker_service import rerank

SIMILARITY_THRESHOLD_DOCS    = 0.65
SIMILARITY_THRESHOLD_TEKTONIKA = 0.75
SIMILARITY_THRESHOLD_GALLERY = 0.75

SEMANTIC_LIMIT = 40
KEYWORD_LIMIT  = 40

STOP_WORDS = {
    "se", "za", "na", "in", "je", "ki", "so", "bi", "da", "mi",
    "me", "si", "ga", "jo", "to", "ta", "te", "ti", "po", "iz",
    "od", "do", "pri", "ali", "kot", "sem", "kaj", "kar", "kje",
    "kako", "kdaj", "kdo", "imam", "imaš", "ima", "zanimam",
    "zanima", "gradivo", "arhiv", "arhivsko", "dokument", "dokumenti",
    "iščem", "iscem", "najdi", "poišči", "poisci", "prosim",
    "mi", "kašno", "kakšno", "kaj", "nekaj"
}

GENERIC_TERMS = {
    "slovenija", "slovenije", "slovenski", "slovenska", "slovensko",
    "slovenskih", "slovenskem", "slovenskega", "slovenskim",
    "jugoslavija", "jugoslavije", "jugoslovanski", "jugoslovanska",
    "arhiv", "arhivsko", "gradivo", "dokumenti", "fond", "zbirka"
}


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^0-9a-zA-ZčšžČŠŽ\s]", " ", text)
    return " ".join(text.split())


def fold_diacritics(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )


def dedup_keep_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def extract_terms(question: str) -> tuple[list[str], list[str]]:
    normalized = normalize_text(question)
    words = dedup_keep_order(normalized.split() + fold_diacritics(normalized).split())
    strong_terms = []
    generic_terms = []
    for word in words:
        if word in STOP_WORDS or len(word) <= 3:
            continue
        if word in GENERIC_TERMS:
            generic_terms.append(word)
        else:
            strong_terms.append(word)
    return dedup_keep_order(strong_terms)[:6], dedup_keep_order(generic_terms)[:6]


def term_match(term: str, text: str) -> bool:
    if term in text:
        return True
    if len(term) >= 7 and term[:6] in text:
        return True
    if len(term) >= 5 and term[:5] in text:
        return True
    return False


def build_keyword_variants(terms: list[str]) -> list[str]:
    variants = []
    for term in terms:
        variants.append(term)
        variants.append(fold_diacritics(term))
        if len(term) >= 7:
            variants.append(term[:6])
        if len(term) >= 5:
            variants.append(term[:5])
    return dedup_keep_order(variants)


def lexical_scores(chunk: str, strong_terms: list[str], generic_terms: list[str]) -> tuple[int, int]:
    text = normalize_text(chunk)
    strong_score = sum(1 for term in strong_terms if term_match(term, text))
    generic_score = sum(1 for term in generic_terms if term_match(term, text))
    return strong_score, generic_score


def query_semantic(cur, embedding_str: str, corpus: str, extra_where: str, extra_params: list, threshold: float, limit: int):
    where = f"corpus = %s"
    params = [embedding_str, corpus]
    if extra_where:
        where += f" AND ({extra_where})"
        params.extend(extra_params)
    params.extend([embedding_str, threshold, limit])

    cur.execute(f"""
        SELECT chunk, source, embedding <=> %s::vector AS distance, visibility, metadata
        FROM documents
        WHERE {where}
          AND embedding <=> %s::vector < %s
        ORDER BY distance
        LIMIT %s
    """, params)
    return cur.fetchall()


def query_keyword(cur, embedding_str: str, corpus: str, variants: list[str], limit: int, user_type: str):
    if not variants:
        return []
    conditions = " OR ".join(["unaccent(chunk) ILIKE unaccent(%s)" for _ in variants])
    patterns = [f"%{v}%" for v in variants]
    visibility_sql = " AND visibility IN ('ku', 'vsi')" if user_type == "KU" else ""
    cur.execute(f"""
        SELECT chunk, source, embedding <=> %s::vector AS distance, visibility, metadata
        FROM documents
        WHERE corpus = %s
          {visibility_sql}
          AND ({conditions})
        ORDER BY distance
        LIMIT %s
    """, [embedding_str, corpus, *patterns, limit])
    return cur.fetchall()


def rerank_rows(rows, question: str):
    strong_terms, generic_terms = extract_terms(question)
    unique = {}
    for chunk, source, distance, visibility, metadata in rows:
        key = (source, chunk)
        if key not in unique or distance < unique[key][2]:
            unique[key] = (chunk, source, distance, visibility, metadata)

    scored = []
    for chunk, source, distance, visibility, metadata in unique.values():
        strong_score, generic_score = lexical_scores(chunk, strong_terms, generic_terms)
        scored.append((strong_score, generic_score, distance, chunk, source, visibility, metadata))

    if strong_terms and sum(1 for row in scored if row[0] > 0) >= 3:
        scored = [row for row in scored if row[0] > 0]

    scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
    lexical_rows = [
        (chunk, source, distance, visibility, metadata)
        for _, _, distance, chunk, source, visibility, metadata in scored
    ]
    return rerank(lexical_rows, question, len(lexical_rows))


def get_context(
    question: str,
    user_type: str = "KU",
    current_page: str = None,
    intent: str = "faq",
    corpus: str = "mixed",
    top_k: int = 5
) -> str:
    try:
        if corpus == "none":
            return ""

        embedding = embed_text(question)
        embedding_str = vector_to_pg(embedding)

        conn = get_conn()
        cur = conn.cursor()

        page_chunks      = []
        doc_chunks       = []
        tektonika_chunks = []
        gallery_chunks   = []

        visibility_where = "visibility IN ('ku', 'vsi')" if user_type == "KU" else ""

        # ── 1. Page-aware docs ────────────────────────────────────────────────
        if current_page and corpus in ("docs", "mixed"):
            page_slug = current_page.strip("/").split("/")[-1]
            if page_slug:
                page_chunks = query_semantic(
                    cur, embedding_str, "docs",
                    f"{visibility_where + ' AND ' if visibility_where else ''}(source ILIKE %s OR chunk ILIKE %s)",
                    [f"%{page_slug}%", f"%{page_slug}%"],
                    SIMILARITY_THRESHOLD_DOCS, 3
                )

        # ── 2. Docs corpus ────────────────────────────────────────────────────
        if corpus in ("docs", "mixed"):
            doc_chunks = query_semantic(
                cur, embedding_str, "docs",
                visibility_where, [], SIMILARITY_THRESHOLD_DOCS, SEMANTIC_LIMIT
            )
            doc_chunks = rerank_rows(doc_chunks, question)[:top_k]

        # ── 3. Tektonika corpus — hybrid retrieval ────────────────────────────
        if corpus in ("tektonika", "mixed"):
            semantic_rows = query_semantic(
                cur, embedding_str, "tektonika",
                visibility_where, [], SIMILARITY_THRESHOLD_TEKTONIKA, SEMANTIC_LIMIT
            )
            strong_terms, generic_terms = extract_terms(question)
            variants = build_keyword_variants(strong_terms if strong_terms else generic_terms)
            keyword_rows = query_keyword(
                cur, embedding_str, "tektonika", variants, KEYWORD_LIMIT, user_type
            )
            tektonika_chunks = rerank_rows(semantic_rows + keyword_rows, question)[:top_k]

        # ── 4. Gallery corpus ─────────────────────────────────────────────────
        if corpus in ("gallery", "mixed"):
            gallery_chunks = query_semantic(
                cur, embedding_str, "gallery",
                visibility_where, [], SIMILARITY_THRESHOLD_GALLERY, SEMANTIC_LIMIT
            )
            gallery_chunks = rerank_rows(gallery_chunks, question)[:top_k]
            print(f"GALLERY CHUNKS: {len(gallery_chunks)}")

        cur.close()
        conn.close()

        # ── Združi glede na corpus in intent ──────────────────────────────────
        if corpus == "docs":
            ordered_rows = page_chunks + doc_chunks
        elif corpus == "tektonika":
            ordered_rows = tektonika_chunks
        elif corpus == "gallery":
            ordered_rows = gallery_chunks
        else:  # mixed
            if intent == "search":
                ordered_rows = tektonika_chunks + page_chunks + doc_chunks
            elif intent == "gallery":
                ordered_rows = gallery_chunks + page_chunks + doc_chunks
            elif intent == "navigation":
                ordered_rows = page_chunks + doc_chunks + tektonika_chunks
            else:
                ordered_rows = page_chunks + doc_chunks + gallery_chunks + tektonika_chunks

        # Dedupe
        seen = set()
        combined = []
        for row in ordered_rows:
            key = (row[1], row[0])
            if key not in seen:
                seen.add(key)
                combined.append(row)

        filtered = combined

        print(
            f"RAG kontekst ({len(filtered)} kosov, "
            f"docs_thr={SIMILARITY_THRESHOLD_DOCS}, "
            f"tek_thr={SIMILARITY_THRESHOLD_TEKTONIKA}, "
            f"gallery_thr={SIMILARITY_THRESHOLD_GALLERY}, "
            f"model={EMBED_MODEL}, intent={intent}, corpus={corpus})"
        )
        for chunk, source, distance, visibility, metadata in filtered[:5]:
            print(f"  [{distance:.3f}] {source[:80]} ({visibility})")

        if not filtered:
            print("  ⚠️ Ni relevantnih zadetkov!")
            return ""

        context_rows = []
        for chunk, source, distance, visibility, metadata in filtered[:top_k]:
            metadata = metadata or {}
            metadata_line = " | ".join(
                f"{key.upper()}: {metadata[key]}"
                for key in ("id", "naziv", "pot", "url")
                if metadata.get(key)
            )
            context_rows.append(
                f"SOURCE: {source}\n"
                f"VISIBILITY: {visibility}\n"
                f"METADATA: {metadata_line}\n"
                f"VECTOR_DISTANCE: {distance:.4f}\n"
                f"CONTENT:\n{chunk}"
            )
        return "\n\n---\n\n".join(context_rows)

    except Exception as e:
        import traceback
        print(f"RAG napaka: {e}")
        print(traceback.format_exc())
        return ""
