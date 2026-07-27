"""Download VAC virtual exhibitions into a stable Markdown knowledge source."""

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE_URL = os.getenv("VAC_VIRTUAL_TOUR_URL", "http://localhost:8443/vac/virtualTourView")
MAX_ID = int(os.getenv("VAC_VIRTUAL_TOUR_MAX_ID", "7"))
BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = BASE_DIR / "docs/virtualne-razstave.md"
MANIFEST_FILE = BASE_DIR / "docs/virtualne-razstave.manifest.json"
DELAY = float(os.getenv("VAC_CRAWL_DELAY", "1.0"))
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30
VERIFY_TLS = os.getenv("VAC_VERIFY_TLS", "false").lower() == "true"

session = requests.Session()
session.headers.update({
    "User-Agent": "VAC-RAG-virtual-tour-crawler/2.0",
    "Accept-Language": "sl-SI,sl;q=0.9",
})


def fetch_tour(tour_id: int, stats: dict) -> dict | None:
    url = f"{BASE_URL}?archiveTourId={tour_id}"
    last_error = "unknown error"
    response = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT, verify=VERIFY_TLS)
            if response.status_code == 200:
                break
            last_error = f"HTTP {response.status_code}"
        except Exception as exc:
            last_error = str(exc)
        if attempt < MAX_RETRIES:
            time.sleep(DELAY * attempt)

    if response is None or response.status_code != 200:
        stats["errors"] += 1
        stats["failures"].append({"id": tour_id, "url": url, "error": last_error})
        print(f"ID {tour_id} failed: {last_error}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    title_el = soup.select_one("h1#exhibitionTitle")
    title = title_el.get_text(strip=True) if title_el else f"Virtualna razstava {tour_id}"

    menu_items = []
    for link in soup.select(".exhibition-link"):
        name = link.get_text(strip=True)
        archive_id = link.get("data-archive-id", "")
        if name:
            menu_items.append({"id": archive_id, "name": name})

    exhibition_data = {}
    patterns = [
        r"var\s+exhibitionData\s*=\s*/\*\[\[.*?\]\]\*/\s*({.*?});",
        r"var\s+exhibitionData\s*=\s*({.*?});",
    ]
    for pattern in patterns:
        match = re.search(pattern, response.text, re.DOTALL)
        if not match:
            continue
        try:
            exhibition_data = json.loads(match.group(1))
            break
        except json.JSONDecodeError as exc:
            stats["parse_errors"] += 1
            stats["failures"].append({"id": tour_id, "url": url, "error": str(exc)})

    sections = []
    for section in exhibition_data.get("sections", []):
        items = []
        for item in section.get("items", []):
            content_type = item.get("contentType", "")
            if content_type == "text":
                text = BeautifulSoup(item.get("html", ""), "html.parser").get_text(" ", strip=True)
                if text:
                    items.append(text)
            elif content_type == "image" and item.get("altText"):
                items.append(f"[Slika: {item['altText']}]")
            elif content_type == "gallery":
                items.extend(
                    f"[Slika: {image['altText']}]"
                    for image in item.get("gallery", [])
                    if image.get("altText")
                )
            elif content_type == "video":
                items.append("[Video posnetek]")
        if items:
            sections.append(" ".join(items))

    no_exhibition = bool(soup.select_one("[th\\:if*='noExhibition'], .alert-info"))
    if no_exhibition or (not sections and title == "Virtualne razstave"):
        return None

    stats["successful"] += 1
    return {
        "id": tour_id,
        "url": url,
        "title": title,
        "menu_items": menu_items,
        "sections": sections,
        "section_count": len(sections),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


def build_markdown(tours: list[dict]) -> str:
    lines = [
        "---", "vloga: vsi", "stran: /vac/virtualTourView", "---", "",
        "## Virtualne razstave VAČ", "",
        "VAČ ponuja virtualne razstave arhivskega gradiva.", "",
        "### Seznam razstav", "",
    ]
    for tour in tours:
        lines.append(f"- [{tour['title']}]({tour['url']})")
    lines.append("")
    for tour in tours:
        lines.extend([f"## {tour['title']}", "", f"Spletna povezava: {tour['url']}", ""])
        for section in tour["sections"]:
            lines.extend([section, ""])
    return "\n".join(lines)


def main():
    stats = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": None,
        "requested": MAX_ID,
        "successful": 0,
        "errors": 0,
        "parse_errors": 0,
        "failures": [],
    }
    tours = []
    for tour_id in range(1, MAX_ID + 1):
        print(f"[{tour_id}/{MAX_ID}] downloading exhibition")
        tour = fetch_tour(tour_id, stats)
        if tour:
            tours.append(tour)
        time.sleep(DELAY)

    if not tours:
        stats["finished_at"] = datetime.now(timezone.utc).isoformat()
        MANIFEST_FILE.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        raise RuntimeError("No virtual exhibitions were downloaded")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(build_markdown(tours), encoding="utf-8")
    stats["finished_at"] = datetime.now(timezone.utc).isoformat()
    stats["complete"] = stats["errors"] == 0 and stats["parse_errors"] == 0
    stats["tours"] = [{"id": tour["id"], "title": tour["title"], "sections": tour["section_count"]} for tour in tours]
    MANIFEST_FILE.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {OUTPUT_FILE} ({len(tours)} exhibitions)")


if __name__ == "__main__":
    main()
