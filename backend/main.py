import time
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE = "https://harmonogramy.dsw.edu.pl"
TOK_ID = "1199"

URL_PAGE = f"{BASE}/Plany/PlanyTokow/{TOK_ID}"
URL_GRID = f"{BASE}/Plany/PlanyTokowGridCustom/{TOK_ID}"

# -----------------------------
#   CACHE (pełny: TTL + fallback)
# -----------------------------
CACHE = {
    "data": None,          # ostatnie poprawne dane (lista zajęć)
    "timestamp": 0,        # czas zapisania (time.time())
    "ttl": 300             # 5 minut
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
#   Pobieranie HTML z retry
# -----------------------------
def fetch_html():
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
        "id": TOK_ID,
    }

    for attempt in range(3):
        r = s.post(URL_GRID, data=payload)
        r.raise_for_status()
        html = r.text

        if "<td" in html.lower():
            return html

        time.sleep(1)

    return None


# -----------------------------
#   Pomocnicze funkcje
# -----------------------------
def extract_text(cell):
    return cell.get_text(strip=True) if cell else ""


def extract_group_code(full_group_name: str) -> str:
    if not full_group_name:
        return ""
    parts = full_group_name.split()
    return parts[-1] if parts else ""


# -----------------------------
#   Parser odporny na zmiany
# -----------------------------
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

        # -----------------------------
        #   Wiersz grupujący (DATA)
        # -----------------------------
        if "dxgvGroupRow_iOS" in classes:
            text = row.get_text(" ", strip=True)
            # np. "Data Zajęć: 2025.10.25 sobota"
            if "Data Zajęć:" in text:
                current_date = text.split("Data Zajęć:")[-1].strip()
            continue

        # -----------------------------
        #   Wiersz danych
        # -----------------------------
        if "dxgvDataRow_iOS" in classes:
            cells = row.find_all("td")

            # minimalna liczba komórek, żeby mieć sensowne dane
            if len(cells) < 10:
                continue

            # struktura:
            # 0 = indent
            # 1 = od
            # 2 = do
            # 3 = liczba godzin
            # 4 = grupa (pełna nazwa)
            # 5 = przedmiot
            # 6 = forma
            # 7 = sala
            # 8 = prowadzący
            # 9 = forma zaliczenia
            # 10 = uwagi
            # 11 = adaptive button (opcjonalnie)

            od = extract_text(cells[1])
            do = extract_text(cells[2])
            godziny = extract_text(cells[3])
            grupa_full = extract_text(cells[4])
            przedmiot = extract_text(cells[5])
            forma = extract_text(cells[6])
            sala = extract_text(cells[7])
            prowadzacy = extract_text(cells[8])
            zaliczenie = extract_text(cells[9])
            uwagi = extract_text(cells[10]) if len(cells) > 10 else ""

            group_code = extract_group_code(grupa_full)

            parsed.append({
                "data": current_date,
                "od": od,
                "do": do,
                "godziny": godziny,
                "group_code": group_code,
                "przedmiot": przedmiot,
                "typ": forma,
                "sala": sala,
                "prowadzacy": prowadzacy,
                "zaliczenie": zaliczenie,
                "uwagi": uwagi,
            })

    return parsed if parsed else None


# -----------------------------
#   Główna logika z cache
# -----------------------------
@app.get("/plan")
def get_plan():
    now = time.time()

    # 1. Jeśli cache jest świeży → zwróć cache
    if CACHE["data"] and now - CACHE["timestamp"] < CACHE["ttl"]:
        return {
            "timestamp": CACHE["timestamp"],
            "data": CACHE["data"]
        }

    # 2. Pobierz nowe dane
    html = fetch_html()
    parsed = parse_plan(html)

    # 3. Jeśli nowe dane są OK → zapisz do cache
    if parsed:
        CACHE["data"] = parsed
        CACHE["timestamp"] = now
        return {
            "timestamp": CACHE["timestamp"],
            "data": CACHE["data"]
        }

    # 4. Jeśli nowe dane są puste → zwróć cache (fallback)
    if CACHE["data"]:
        return {
            "timestamp": CACHE["timestamp"],
            "data": CACHE["data"]
        }

    # 5. Jeśli nie ma nic → zwróć błąd
    return {"error": "Brak danych z DSW. Spróbuj ponownie."}
