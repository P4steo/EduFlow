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

    r = s.post(URL_GRID, data=payload)
    r.raise_for_status()
    return r.text

def extract_group_code(godziny: str) -> str:
    parts = godziny.split()
    return parts[-1] if parts else ""

def parse_plan(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "gridViewPlanyTokow_DXMainTable"})
    if not table:
        return []

    rows = table.find_all("tr")
    parsed = []

    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 11:
            continue

        godziny = cols[4]
        group_code = extract_group_code(godziny)

        parsed.append({
            "data": cols[1],
            "od": cols[2],
            "do": cols[3],
            "group_code": group_code,      # Ćw1N / Ćw2N / WykN
            "przedmiot": cols[5],          # nazwa przedmiotu
            "typ": cols[6],                # Cw / Wyk
            "sala": cols[7],               # sala
            "prowadzacy": cols[8],         # prowadzący
            "zaliczenie": cols[9],         # egzamin / zaliczenie
            "uwagi": cols[10],             # uwagi
        })

    return parsed

@app.get("/plan")
def get_plan():
    html = fetch_html()
    return parse_plan(html)
