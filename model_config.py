import os

ANSWER_MODEL = os.getenv("ANSWER_MODEL", "gemma3:12b")
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "phi4-mini")
RERANK_MODEL = os.getenv(
    "RERANK_MODEL",
    "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
)

# Guard model bomo vključili v naslednjem koraku
GUARD_MODEL = os.getenv("GUARD_MODEL", "granite3-guardian:2b-q8_0")

# PZI-aligned embeddings
EMBED_MODEL_NAME = os.getenv(
    "EMBED_MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Ta model je običajno 384-dim; če uporabiš drug model, popravi tudi to vrednost
EMBED_DIM = int(os.getenv("EMBED_DIM", "384"))

# Začetne vrednosti - kasneje jih boš stestiral in prilagodil
SIMILARITY_THRESHOLD_DOCS = float(os.getenv("SIMILARITY_THRESHOLD_DOCS", "0.75"))
SIMILARITY_THRESHOLD_ARCHIVE = float(os.getenv("SIMILARITY_THRESHOLD_ARCHIVE", "0.80"))
