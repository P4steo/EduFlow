import time
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

BASE = "https://harmonogramy.dsw.edu.pl"

# Lista dostępnych specjalizacji
TOKS = {
    "1337": "Animacja 3D",
    "1336": "Game Art i Concept Design",
    "1335": "Game Design"
}

# CACHE per‑TOK
CACHE = {
    tok: {
        "data": None,
        "timestamp": 0,
        "ttl": 300
    }
    for tok in TOKS
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def fetch_html(tok: str):
    URL_PAGE = f"{BASE}/Plany/PlanyTokow/{tok}"
    URL_GRID = f"{BASE}/Plany/PlanyTokowGridCustom/{tok}"

    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    s.get(URL_PAGE)

    payload = {
        "DXCallbackName": "gridViewPlanyTokow",
        "__DXCallbackArgument": "c0:KV|2;[];GB|35;14|CUSTOMCALLBACK15|[object Object];",
        "gridViewPlanyTokow": '{"customOperationState":"","keys":[],"callbackState":"","groupLevelState":{},"selection":"","toolbar":null}',
        "gridViewPlanyTokow$custwindowState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "DXMVCEditorsValues": "{}",
        "parametry": "2025-9-6;2026-2-8;3;1199",
        "id": tok,
    }

    for attempt in range(3):
        r = s.post(URL_GRID, data=payload)
        r.raise_for_status()
        html = r.text

        if "<td" in html.lower():
            return html

        time.sleep(1)

    return None


def extract_text(cell):
    return cell.get_text(strip=True) if cell else ""


def extract_group_code(full_group_name: str) -> str:
    if not full_group_name:
        return ""
    parts = full_group_name.split()
    return parts[-1] if parts else ""


def parse_plan(html):
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "gridViewPlanyTokow_DXMainTable"})
    if not table:
        return None

    rows = table.find_all("tr")
    parsed = []
    current_date = None

    for row in rows:
        classes = row.get("class", [])

        if "dxgvGroupRow_iOS" in classes:
            text = row.get_text(" ", strip=True)
            if "Data Zajęć:" in text:
                current_date = text.split("Data Zajęć:")[-1].strip()
            continue

        if "dxgvDataRow_iOS" in classes:
            cells = row.find_all("td")
            if len(cells) < 10:
                continue

            parsed.append({
                "data": extract_text(cells[1]),
                "od": extract_text(cells[1]),
                "do": extract_text(cells[2]),
                "godziny": extract_text(cells[3]),
                "group_code": extract_group_code(extract_text(cells[4])),
                "przedmiot": extract_text(cells[5]),
                "typ": extract_text(cells[6]),
                "sala": extract_text(cells[7]),
                "prowadzacy": extract_text(cells[8]),
                "zaliczenie": extract_text(cells[9]),
                "uwagi": extract_text(cells[10]) if len(cells) > 10 else "",
                "data": current_date
            })

    return parsed if parsed else None


@app.get("/plan")
def get_plan(request: Request):
    tok = request.query_params.get("tok", "1337")

    if tok not in TOKS:
        return {"error": "Nieznany tok"}

    now = time.time()
    cache = CACHE[tok]

    if cache["data"] and now - cache["timestamp"] < cache["ttl"]:
        return {
            "timestamp": cache["timestamp"],
            "data": cache["data"]
        }

    html = fetch_html(tok)
    parsed = parse_plan(html)

    if parsed:
        cache["data"] = parsed
        cache["timestamp"] = now
        return {
            "timestamp": cache["timestamp"],
            "data": cache["data"]
        }

    if cache["data"]:
        return {
            "timestamp": cache["timestamp"],
            "data": cache["data"]
        }

    return {"error": "Brak danych z DSW"}
