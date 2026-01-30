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
    allow_origins=[
        "https://p4steo.github.io",
        "https://p4steo.github.io/EduFlow",
        "https://eduflow.com",
        "https://www.eduflow.com"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


def fetch_html():
    s = requests.Session()

    s.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    s.get(URL_PAGE)

    s.headers.update({
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "text/html, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": BASE,
        "Referer": URL_PAGE,
    })

    payload = {
        "DXCallbackName": "gridViewPlanyTokow",
        "__DXCallbackArgument": "c0:KV|2;[];GB|35;14|CUSTOMCALLBACK15|[object Object];",
        "gridViewPlanyTokow": (
            '{"customOperationState":"","keys":[],"callbackState":"","groupLevelState":{},'
            '"selection":"","toolbar":null}'
        ),
        "gridViewPlanyTokow$custwindowState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "DXMVCEditorsValues": "{}",
        "parametry": "2025-9-6;2026-2-8;3;1199",
        "id": TOK_ID,
    }

    r = s.post(URL_GRID, data=payload)
    r.raise_for_status()
    return r.text


def extract_group_code(godziny: str) -> str:
    # np. "MK: PGiA 2st 1sem Ćw2N" → "Ćw2N"
    parts = godziny.split()
    if not parts:
        return ""
    last = parts[-1]
    return last  # Ćw1N / Ćw2N / WykN itd.


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
            "godziny": godziny,
            "group_code": group_code,  # Ćw1N / Ćw2N / WykN
            "grupa": cols[5],
            "zajecia": cols[6],
            "forma": cols[7],
            "sala": cols[8],
            "prowadzacy": cols[9],
            "uwagi": cols[10],
        })

    return parsed


@app.get("/")
def root():
    return {"status": "ok", "message": "EduFlow backend running"}


@app.get("/plan")
def get_plan():
    html = fetch_html()
    return parse_plan(html)
