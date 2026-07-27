import os
from functools import lru_cache

import torch
from sentence_transformers import SentenceTransformer

# Zahtevani embedding model iz PZI
EMBED_MODEL = r"C:\Endava\EndevLocal\vac\AI\models\paraphrase-multilingual-MiniLM-L12-v2-main"

# Ta model daje 384-dimenzionalne vektorje
EMBED_DIM = 384

# Če je CUDA na voljo, bo uporabil GPU (npr. RTX 4090)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Za začetek dobra vrednost; če zmanjka VRAM, daj 64
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "128"))


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    print(f"🔎 Nalagam embedding model: {EMBED_MODEL} | device={DEVICE}")
    model = SentenceTransformer(EMBED_MODEL, device=DEVICE)
    return model


def embed_text(text: str) -> list[float]:
    model = get_embedder()
    vector = model.encode(
        text if text and text.strip() else " ",
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return vector.tolist()


def embed_many(texts: list[str], batch_size: int | None = None) -> list[list[float]]:
    model = get_embedder()
    cleaned = [t if t and t.strip() else " " for t in texts]

    vectors = model.encode(
        cleaned,
        batch_size=batch_size or EMBED_BATCH_SIZE,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectors]


def vector_to_pg(embedding: list[float]) -> str:
    # Varno za INSERT v pgvector
    return "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"