import requests
import json
import time
import os
import warnings
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

warnings.filterwarnings('ignore')

BASE_URL = "https://vac.sjas.gov.si"
ROOT_ID = 1000001
DELAY = float(os.getenv("VAC_CRAWL_DELAY", "0.05"))
MAX_RETRIES = int(os.getenv("VAC_MAX_RETRIES", "1"))
REQUEST_TIMEOUT = int(os.getenv("VAC_REQUEST_TIMEOUT", "15"))
VERIFY_TLS = os.getenv("VAC_VERIFY_TLS", "false").lower() == "true"
FETCH_DETAILS = True

# ✅ Vsak arhiv dobi svojo mapo
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "tektonika_arhivi"
os.makedirs(OUTPUT_DIR, exist_ok=True)
COOKIE_FILE = OUTPUT_DIR.parent / ".vac-cookie"


def load_vac_cookie() -> str:
    """Load the authenticated VAC cookie from the environment or local file."""
    configured_cookie = os.getenv("VAC_COOKIE", "").strip()
    if configured_cookie:
        return configured_cookie
    if COOKIE_FILE.exists():
        return COOKIE_FILE.read_text(encoding="utf-8").strip()
    return ""


def normalize_vac_cookie(value: str) -> str:
    """Accept either a complete Cookie header or only the JSESSIONID value."""
    value = value.strip()
    if not value:
        return ""
    if "=" in value:
        return value
    return f"vac.cookies.allowed=true; JSESSIONID={value}"


VAC_COOKIE = normalize_vac_cookie(load_vac_cookie())


def make_session():
    """Vsak thread dobi svojo session — brez logina."""
    s = requests.Session()
    if VAC_COOKIE:
        s.headers["Cookie"] = VAC_COOKIE
    return s


def _request(session, url: str, stats: dict, kind: str):
    last_error = "unknown error"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, verify=VERIFY_TLS, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp
            last_error = f"HTTP {resp.status_code}"
        except Exception as exc:
            last_error = str(exc)
        if attempt < MAX_RETRIES:
            time.sleep(DELAY * attempt)

    stats["errors"] += 1
    stats["failures"].append({"kind": kind, "url": url, "error": last_error})
    return None


def fetch_children(session, node_id: int, page: int, stats: dict) -> list | None:
    url = f"{BASE_URL}/vac/search/archivePlanSearchAjax?id={node_id}&page={page}"
    resp = _request(session, url, stats, "children")
    if resp is None:
        return None
    try:
        return resp.json()
    except ValueError as exc:
        stats["errors"] += 1
        stats["failures"].append({"kind": "children_json", "url": url, "error": str(exc)})
        return None


def fetch_details(session, node_id, text: str, stats: dict) -> dict | None:
    url = f"{BASE_URL}/vac/search/details?id={node_id}&text={quote(text)}"
    resp = _request(session, url, stats, "details")
    if resp is None:
        return None
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")

        # Odstrani sistemske elemente
        for tag in soup(["nav", "script", "style"]):
            tag.decompose()
        for tag in soup.select("#pageHeader, #pageFooter, .accessibility-toolbar, #menu, .leftmenu"):
            tag.decompose()

        details = {}

        # ✅ 1. Naslov strani
        title = soup.select_one("h3")
        if title:
            details["naziv"] = title.get_text(strip=True)

        # ✅ 2. Glavni podatki — Bootstrap row col-lg-2 / col-lg-10
        for row in soup.select("div.row"):
            label_el = row.select_one("div.col-lg-2 label, div.col-md-3 label")
            value_el = row.select_one("div.col-lg-10 label, div.col-md-9 label")

            if label_el and value_el:
                label = label_el.get_text(strip=True).rstrip(":")
                value = value_el.get_text(strip=True)

                skip = ["verzija", "datum:", "interni id", "vač1.", "copyright"]
                if any(kw in label.lower() for kw in skip):
                    continue
                if label and value and len(label) > 1 and len(value) > 1:
                    details[label] = value

        # ✅ 3. Skupinske oznake (titleBackground) — sekcijski naslovi
        for group in soup.select("label.titleBackground"):
            group_text = group.get_text(strip=True)
            if group_text and len(group_text) > 1:
                if "skupine" not in details:
                    details["skupine"] = []
                details["skupine"].append(group_text)

        # ✅ 4. Deskriptorji (gesla, osebe, kraji, pojmi)
        descriptors = []
        for desc in soup.select("a.form-control-label.inARow"):
            d = desc.get_text(strip=True)
            if d and len(d) > 1:
                descriptors.append(d)
        if descriptors:
            details["deskriptorji"] = descriptors

        # ✅ 5. Povezave na reference
        references = []
        for ref_row in soup.select("div.row"):
            ref_type = ref_row.select_one("label.form-control-label.inARow")
            ref_link = ref_row.select_one("a.form-control-label")
            if ref_type and ref_link:
                ref_text = ref_link.get_text(strip=True)
                ref_href = ref_link.get("href", "")
                if ref_text and "details" in ref_href:
                    references.append({
                        "tip": ref_type.get_text(strip=True),
                        "naziv": ref_text,
                        "url": ref_href
                    })
        if references:
            details["reference"] = references

        # ✅ 6. Datoteke / digitalizirano gradivo
        files = []
        for file_link in soup.select("a.form-control-label[href*='file']"):
            f = file_link.get_text(strip=True)
            href = file_link.get("href", "")
            if f:
                files.append({"naziv": f, "url": href})
        if files:
            details["datoteke"] = files

        # ✅ 7. Tektonična pot (breadcrumb iz archivePlanTreePathData)
        pot_elementi = []
        for ul in soup.select("#archivePlanTreePathData ul"):
            title_attr = ul.get("data-title", "")
            if title_attr:
                pot_elementi.append(title_attr)
        if pot_elementi:
            details["tektonicna_pot"] = " > ".join(pot_elementi)

        # ✅ 8. Število vsebnikov
        containers = soup.select_one("div.col-lg-10 label[th\\:text='${containers}']")
        if not containers:
            # Poišči po kontekstu
            for row in soup.select("div.row"):
                label_el = row.select_one("div.col-lg-2 label")
                value_el = row.select_one("div.col-lg-10 label")
                if label_el and value_el:
                    if "vsebnik" in label_el.get_text(strip=True).lower():
                        details["vsebniki"] = value_el.get_text(strip=True)

        return details
    except Exception as exc:
        stats["errors"] += 1
        stats["failures"].append({"kind": "details_parse", "url": url, "error": str(exc)})
        return None


def parse_node_id(raw_id) -> tuple:
    s = str(raw_id)
    if "++" in s:
        return s.split("++")[0], True, "next"
    elif "--" in s:
        return s.split("--")[0], True, "first"
    elif "+" in s:
        return s.split("+")[0], True, "last"
    elif "-" in s[1:]:
        return s.split("-")[0], True, "prev"
    return s, False, None


def scrape_node(session, node_id: int, depth: int, path: str,
                parent_id: str | None, nodes: list, stats: dict,
                lock: threading.Lock, prefix: str):
    """Rekurzivno scrapanje enega arhiva."""
    indent = "  " * depth
    page = 0

    while True:
        raw_list = fetch_children(session, node_id, page, stats)
        time.sleep(DELAY)

        if raw_list is None:
            stats["complete"] = False
            break
        if not raw_list:
            break

        stats["pages"] += 1

        has_next = False

        for raw in raw_list:
            raw_id = raw.get("id", "")
            clean_id, is_nav, nav_dir = parse_node_id(raw_id)

            if is_nav:
                if nav_dir in ("next", "last"):
                    has_next = True
                continue

            text = raw.get("text", "").strip()
            tip = raw.get("type", "")
            has_children = bool(raw.get("children"))
            current_path = f"{path} > {text}" if path else text

            node_data = {
                "id": clean_id,
                "naziv": text,
                "tip": tip,
                "pot": current_path,
                "parent_id": parent_id,
                "level": depth,
                "url": f"/vac/search/details?id={clean_id}&text={quote(text)}"
            }

            # ✅ Thread-safe dodajanje
            with lock:
                if clean_id in stats["_seen_ids"]:
                    stats["duplicates"] += 1
                    continue
                stats["_seen_ids"].add(clean_id)
                nodes.append(node_data)
                stats["nodes"] += 1
                count = stats["nodes"]

            print(f"[{prefix}]{indent}[{tip}] {text[:60]} (id:{clean_id})")

            # Checkpoint vsakih 50 nodov
            if count % 50 == 0:
                save_archive(prefix, nodes, stats)
                print(f"[{prefix}] 💾 {count} nodov")

            # ✅ Fetch details za VSE node-e (tudi vmesne)
            if FETCH_DETAILS:
                try:
                    details = fetch_details(session, int(clean_id), text, stats)
                    if details:
                        node_data["details"] = details
                        print(f"[{prefix[:15]}]{indent}  ✅ details: {len(details)} polj")
                    elif details is None:
                        node_data["details_error"] = True
                        stats["details_missing"] += 1
                    time.sleep(DELAY)
                except (ValueError, TypeError):
                    pass

            # Rekurzija za otroke
            if has_children:
                try:
                    scrape_node(session, int(clean_id), depth + 1,
                               current_path, clean_id, nodes, stats, lock, prefix)
                except (ValueError, TypeError):
                    pass

        if has_next:
            page += 1
            print(f"[{prefix}]{indent}  → Stran {page}...")
        else:
            break

    # Shrani po vsakem končanem nivoju
    save_archive(prefix, nodes, stats)


def save_archive(name: str, nodes: list, stats: dict):
    """Shrani JSON za en arhiv."""
    safe_name = name.replace(" ", "_").replace("/", "_").replace("[", "").replace("]", "")
    path = os.path.join(OUTPUT_DIR, f"{safe_name}.json")
    clean_stats = {key: value for key, value in stats.items() if not key.startswith("_")}
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"schema_version": 2, "arhiv": name, "stats": clean_stats, "nodes": nodes}, f,
                  ensure_ascii=False, indent=2)


def worker(arhiv_raw: dict):
    """En thread = en arhiv."""
    clean_id, is_nav, _ = parse_node_id(arhiv_raw.get("id", ""))
    if is_nav:
        return

    text = arhiv_raw.get("text", "").strip()
    # ✅ Polno ime za datoteko (ne skrajšano)
    prefix = text

    print(f"\n🚀 [{text}] Začenjam...")

    session = make_session()

    nodes = []
    stats = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": None,
        "complete": True,
        "nodes": 0,
        "pages": 0,
        "errors": 0,
        "details_missing": 0,
        "duplicates": 0,
        "failures": [],
        "_seen_ids": set(),
    }
    lock = threading.Lock()

    try:
        scrape_node(session, int(clean_id), depth=1, path=text,
                   parent_id=None, nodes=nodes, stats=stats, lock=lock, prefix=prefix)
    except (ValueError, TypeError) as e:
        print(f"❌ [{prefix}] Napaka: {e}")

    stats["finished_at"] = datetime.now(timezone.utc).isoformat()
    save_archive(text, nodes, stats)
    print(f"\n✅ [{prefix}] KONČANO! {stats['nodes']} nodov")


def scrape_tektonika_parallel():
    print("🔍 Pridobivam seznam arhivov...")

    # Ena začetna session za root
    root_session = make_session()

    root_stats = {"errors": 0, "failures": []}
    root_list = fetch_children(root_session, ROOT_ID, 0, root_stats)
    if not root_list:
        print("❌ Brez podatkov iz korenskega endpointa.")
        if root_stats.get("failures"):
            for failure in root_stats["failures"][:3]:
                print(f"   Napaka: {failure['kind']} | {failure['error']} | {failure['url']}")
        else:
            print(f"   Endpoint je vrnil prazen seznam. Preveri ROOT_ID={ROOT_ID} ali API odziv.")
        return

    # Filtriraj navigacijske node-e
    arhivi = []
    for raw in root_list:
        _, is_nav, _ = parse_node_id(raw.get("id", ""))
        if not is_nav:
            arhivi.append(raw)

    print(f"✅ Najdenih {len(arhivi)} arhivov\n")
    for a in arhivi:
        print(f"  → {a.get('text', '')} (id: {a.get('id', '')})")

    print(f"\n🚀 Zaganjam {len(arhivi)} vzporednih workerjev...\n")

    # ✅ En thread na arhiv
    threads = []
    for arhiv in arhivi:
        t = threading.Thread(target=worker, args=(arhiv,))
        t.daemon = True
        threads.append(t)
        t.start()
        time.sleep(0.5)  # Malo zamaknemo start da ne obremenimo strežnika naenkrat

    # Čakaj da vsi končajo
    for t in threads:
        t.join()

    with open(os.path.join(OUTPUT_DIR, "crawl_manifest.json"), "w", encoding="utf-8") as f:
        json.dump({
            "schema_version": 2,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "root_errors": root_stats,
            "archives": sorted(name for name in os.listdir(OUTPUT_DIR) if name.endswith(".json")),
        }, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"🎉 VSI ARHIVI KONČANI!")
    print(f"📁 JSON datoteke so v mapi: {OUTPUT_DIR}/")


if __name__ == "__main__":
    scrape_tektonika_parallel()
