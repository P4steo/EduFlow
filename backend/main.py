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

    # 🔁 3 próby pobrania danych
    for attempt in range(3):
        r = s.post(URL_GRID, data=payload)
        r.raise_for_status()
        html = r.text

        # jeśli tabela zawiera <td> → OK
        if "<td" in html.lower():
            return html

        # jeśli nie → poczekaj i spróbuj ponownie
        time.sleep(1)

    # po 3 próbach nadal pusto
    return None


def extract_group_code(godziny: str) -> str:
    parts = godziny.split()
    return parts[-1] if parts else ""


def parse_plan(html):
    if not html:
        return {"error": "Brak danych z DSW. Spróbuj ponownie za chwilę."}

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "gridViewPlanyTokow_DXMainTable"})
    if not table:
        return {"error": "Brak tabeli w danych z DSW."}

    rows = table.find_all("tr")
    parsed = []

    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]

        # pomiń nagłówki i błędne wiersze
        if len(cols) != 11:
            continue

        header_keywords = ["data", "godz", "grupa", "zajęcia", "forma", "sala", "prowadzący", "uwagi"]
        if any(cols[i].lower() in header_keywords for i in range(len(cols))):
            continue

        godziny = cols[4]
        group_code = extract_group_code(godziny)

        parsed.append({
            "data": cols[1],
            "od": cols[2],
            "do": cols[3],
            "group_code": group_code,
            "przedmiot": cols[5],
            "typ": cols[6],
            "sala": cols[7],
            "prowadzacy": cols[8],
            "zaliczenie": cols[9],
            "uwagi": cols[10],
        })

    if not parsed:
        return {"error": "Brak danych po przetworzeniu. Spróbuj ponownie."}

    return parsed


@app.get("/plan")
def get_plan():
    html = fetch_html()
    return parse_plan(html)
