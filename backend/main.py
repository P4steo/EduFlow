import time
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE = "https://harmonogramy.dsw.edu.pl"
TOK_ID = "1199"

URL_PAGE = f"{BASE}/Plany/PlanyTokow/{TOK_ID}"
URL_GRID = f"{BASE}/Plany/PlanyTokowGridCustom/{TOK_ID}"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def fetch_html():
    """Pobiera HTML z DSW z retry."""
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

    for _ in range(3):
        r = s.post(URL_GRID, data=payload)
        r.raise_for_status()
        html = r.text

        if "<td" in html.lower():
            return html

        time.sleep(1)

    return None


def extract_text(cell):
    """Czyści komórkę z linków <a> i zwraca sam tekst."""
    if cell is None:
        return ""
    return cell.get_text(strip=True)


def extract_group_code(full_group_name: str) -> str:
    """Wyciąga Ćw1N / Ćw2N / WykN z pełnej nazwy grupy."""
    if not full_group_name:
        return ""
    parts = full_group_name.split()
    return parts[-1] if parts else ""


def parse_plan(html):
    if not html:
        return {"error": "Brak danych z DSW. Spróbuj ponownie."}

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "gridViewPlanyTokow_DXMainTable"})
    if not table:
        return {"error": "Brak tabeli w danych z DSW."}

    rows = table.find_all("tr")

    parsed = []
    current_date = None

    for row in rows:
        classes = row.get("class", [])

        # 🟦 1. Wiersz grupujący → zawiera datę
        if "dxgvGroupRow_iOS" in classes:
            text = row.get_text(" ", strip=True)
            # Format: "Data Zajęć: 2025.10.25 sobota"
            if "Data Zajęć:" in text:
                current_date = text.split("Data Zajęć:")[-1].strip()
            continue

        # 🟦 2. Wiersz danych
        if "dxgvDataRow_iOS" in classes:
            cells = row.find_all("td")

            # ignorujemy wiersze bez danych
            if len(cells) < 10:
                continue

            # struktura dynamiczna:
            # 0 = indent
            # 1 = od
            # 2 = do
            # 3 = liczba godzin
            # 4 = grupa
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

    if not parsed:
        return {"error": "Brak danych po przetworzeniu. Spróbuj ponownie."}

    return parsed


@app.get("/plan")
def get_plan():
    html = fetch_html()
    return parse_plan(html)
