import re

STOP_WORDS = {
    "se", "za", "na", "in", "je", "ki", "so", "bi", "da", "mi",
    "me", "si", "ga", "jo", "to", "ta", "te", "ti", "po", "iz",
    "od", "do", "pri", "ali", "kot", "sem", "kaj", "kar", "kje",
    "kako", "kdaj", "kdo", "imam", "imaš", "ima", "zanimam",
    "zanima", "gradivo", "arhiv", "arhivsko", "dokument", "iščem",
    "iscem", "najdi", "poišči", "poisci", "mi", "kašno", "kakšno",
    "prosim", "lahko", "rad", "rada"
}

GENERIC_TERMS = {
    "slovenija", "slovenije", "slovenski", "slovenska", "slovensko",
    "slovenskih", "slovenskem", "slovenskim", "slovenskega",
    "jugoslavija", "jugoslavije", "jugoslovanski", "jugoslovanska",
    "arhiv", "arhivsko", "fond", "zbirka", "gradivo", "dokumenti"
}


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-zA-ZčšžČŠŽ0-9\s]", " ", text)
    return " ".join(text.split())


def parse_chunk(chunk: str) -> dict:
    data = {}
    for line in chunk.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            continue

        if key in data:
            data[key] += " " + value
        else:
            data[key] = value

    return data


def extract_terms(question: str) -> tuple[list[str], list[str]]:
    words = normalize_text(question).split()
    words = [w for w in words if w not in STOP_WORDS and len(w) > 3]

    strong_terms = [w for w in words if w not in GENERIC_TERMS]
    generic_terms = [w for w in words if w in GENERIC_TERMS]

    return strong_terms[:6], generic_terms[:6]


def term_matches(term: str, text: str) -> bool:
    if term in text:
        return True

    # blag prefix fallback
    if len(term) >= 6 and term[:6] in text:
        return True

    # zelo grob fallback za sklanjanje
    if len(term) >= 5:
        root = term[:5]
        if root in text:
            return True

    return False


def searchable_text(data: dict) -> str:
    text = " ".join([
        data.get("Naziv", ""),
        data.get("Signatura PE", ""),
        data.get("Naslov PE", ""),
        data.get("Vsebina PE", ""),
        data.get("Historiat", ""),
        data.get("Historiat PE", ""),
        data.get("Deskriptorji", ""),
        data.get("Pot", ""),
        data.get("tektonicna_pot", ""),
    ])
    return normalize_text(text)


def item_scores(data: dict, strong_terms: list[str], generic_terms: list[str]) -> tuple[int, int]:
    text = searchable_text(data)

    strong_score = 0
    for term in strong_terms:
        if term_matches(term, text):
            strong_score += 1

    generic_score = 0
    for term in generic_terms:
        if term_matches(term, text):
            generic_score += 1

    return strong_score, generic_score


def short_text(value: str, max_len: int = 220) -> str:
    if not value:
        return ""
    value = " ".join(value.split())
    if len(value) <= max_len:
        return value
    return value[:max_len].rstrip() + "..."


def best_description(data: dict) -> str:
    for key in ("Vsebina PE", "Naslov PE", "Historiat PE", "Historiat", "Deskriptorji", "Pot", "tektonicna_pot"):
        if data.get(key):
            return short_text(data[key])
    return ""


def format_tektonika_answer(question: str, context: str, max_items: int = 3) -> str:
    fallback = (
        "Za iskano gradivo trenutno nisem našel dovolj relevantnih zadetkov v VAČ. "
        "Poskusi z bolj natančnim pojmom, letnico, krajem ali signaturo."
    )

    if not context or not context.strip():
        return fallback

    strong_terms, generic_terms = extract_terms(question)
    blocks = [b.strip() for b in context.split("\n\n---\n\n") if b.strip()]

    candidates = []
    for block in blocks:
        data = parse_chunk(block)

        naziv = data.get("Naziv", "").strip()
        signatura = data.get("Signatura PE", "").strip()
        if not naziv and not signatura:
            continue

        strong_score, generic_score = item_scores(data, strong_terms, generic_terms)

        # Ključno pravilo:
        # če ima vprašanje močne termine (npr. čebelarstvo, železnice),
        # zahtevamo vsaj 1 tak termin v zadetku
        if strong_terms and strong_score == 0:
            continue

        candidates.append((strong_score, generic_score, data))

    if not candidates:
        return fallback

    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)

    lines = ["Našel sem naslednje relevantne zadetke:"]
    for strong_score, generic_score, data in candidates[:max_items]:
        title = (
            data.get("Naziv")
            or data.get("Naslov PE")
            or data.get("Signatura PE")
            or "Neimenovan zadetek"
        )
        lines.append(f"- {title}")

        if data.get("Signatura PE"):
            lines.append(f"  Signatura: {data['Signatura PE']}")

        opis = best_description(data)
        if opis:
            lines.append(f"  Kratek opis: {opis}")

        if data.get("URL"):
            lines.append(f"  Povezava: 🔗 [Odpri v VAČ]({data['URL']})")

    return "\n".join(lines)