import json
import re
import ollama

from model_config import ROUTER_MODEL
from prompts import ROUTER_PROMPT

VALID_INTENTS = {"faq", "navigation", "search", "gallery", "out_of_scope"}
VALID_CORPORA = {"docs", "tektonika", "gallery", "mixed", "none"}


def _fallback_route(message: str, current_page: str | None = None) -> dict:
    text = f"{current_page or ''} {message}".lower()

    gallery_keywords = [
        "razstava", "razstave", "virtualna razstava", "virtualne razstave", "razstavi", "virtualni", "virtualna",
        "virtualno razstavo",
    ]

    search_keywords = [
        "iščem", "najdi", "poišči", "signatura", "fond", "serija",
        "deskriptor", "gradivo", "dokument", "poročila", "letnica",
        "194", "191", "tekst", "tektonika"
    ]
    nav_keywords = [
        "kako", "kje kliknem", "kje najdem", "registr", "prijav",
        "naroč", "uporabim", "odprem", "iskanje po", "vnos"
    ]

    if any(k in text for k in gallery_keywords):
        return {
            "intent": "gallery",
            "corpus": "gallery",
            "should_use_rag": True,
            "should_offer_links": True,
        }

    if any(k in text for k in search_keywords) or "iskanje" in text:
        return {
            "intent": "search",
            "corpus": "tektonika",
            "should_use_rag": True,
            "should_offer_links": True,
        }

    if any(k in text for k in nav_keywords):
        return {
            "intent": "navigation",
            "corpus": "docs",
            "should_use_rag": True,
            "should_offer_links": False,
        }

    return {
        "intent": "faq",
        "corpus": "docs",
        "should_use_rag": True,
        "should_offer_links": False,
    }


def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("JSON ni bil vrnjen")
    return json.loads(match.group(0))


def _normalize_route(route: dict, message: str, current_page: str | None) -> dict:
    fallback = _fallback_route(message, current_page)

    intent = route.get("intent", fallback["intent"])
    corpus = route.get("corpus", fallback["corpus"])
    should_use_rag = route.get("should_use_rag", fallback["should_use_rag"])
    should_offer_links = route.get("should_offer_links", fallback["should_offer_links"])

    if intent not in VALID_INTENTS:
        intent = fallback["intent"]

    if intent == "gallery":
        corpus = "gallery"
        should_use_rag = True

    if corpus not in VALID_CORPORA:
        corpus = fallback["corpus"]

    msg = message.lower()

    if intent in {"faq", "navigation", "search", "gallery"}:
        should_use_rag = True

    if intent == "out_of_scope":
        should_use_rag = False
        corpus = "none"

    # Virtualne razstave → gallery corpus
    if "razstav" in msg:
        corpus = "gallery"
        intent = "gallery"

    # Arhivsko gradivo → tektonika
    archive_search_words = [
        "iščem", "iscem", "najdi", "poišči", "poisci", "gradivo",
        "signatura", "fond", "serija", "deskriptor", "letnica",
        "arhiv", "gradiva", "poročila"
    ]

    if intent == "search" and "razstav" not in msg:
        if any(w in msg for w in archive_search_words):
            if corpus == "docs":
                corpus = "tektonika"
        if corpus == "none":
            corpus = "tektonika"

    return {
        "intent": intent,
        "corpus": corpus,
        "should_use_rag": bool(should_use_rag),
        "should_offer_links": bool(should_offer_links),
    }


def classify_intent(message: str, current_page: str | None = None) -> dict:
    try:
        response = ollama.chat(
            model=ROUTER_MODEL,
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {
                    "role": "user",
                    "content": f"Vprašanje: {message}\nTrenutna stran: {current_page or '-'}"
                }
            ]
        )
        content = response["message"]["content"]
        raw_route = _extract_json(content)
        print(f"RAW ROUTER: {raw_route}")

        route = _normalize_route(raw_route, message, current_page)
        print(f"🧭 ROUTER: {route}")
        return route

    except Exception as e:
        print(f"⚠️ Router fallback zaradi napake: {e}")
        route = _fallback_route(message, current_page)
        print(f"🧭 ROUTER FALLBACK: {route}")
        return route
