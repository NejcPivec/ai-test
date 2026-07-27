"""Optional multilingual cross-encoder reranking for retrieved chunks."""

from functools import lru_cache

from model_config import RERANK_MODEL



@lru_cache(maxsize=1)
def get_reranker():
    from sentence_transformers import CrossEncoder

    print(f"Loading reranker: {RERANK_MODEL}")
    return CrossEncoder(RERANK_MODEL)


def rerank(rows: list[tuple], question: str, limit: int) -> list[tuple]:
    if len(rows) <= 1:
        return rows[:limit]

    try:
        model = get_reranker()
        pairs = [(question, row[0]) for row in rows]
        scores = model.predict(pairs, show_progress_bar=False)
        ranked = sorted(zip(scores, rows), key=lambda item: float(item[0]), reverse=True)
        return [row for _, row in ranked[:limit]]
    except Exception as exc:
        print(f"Reranker unavailable; keeping lexical/vector order: {exc}")
        return rows[:limit]
