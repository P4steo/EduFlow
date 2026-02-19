import time
import re
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

BASE = "https://harmonogramy.dsw.edu.pl"

TOKS = {
    "1337": "Animacja 3D",
    "1336": "Game Art i Concept Design",
    "1335": "Game Design",
    "1199": "Poprzedni tok (legacy)"
}

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
    s.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": URL_PAGE,
    })

    # wejście na stronę, żeby ustawić cookies
    s.get(URL_PAGE)

    # próba wyciągnięcia zakresu semestru z cookies
    cookies = s.cookies.get_dict()
    if "RadioList_TerminT" in cookies:
        raw = cookies["RadioList_TerminT"]
        parts = raw.split("\\")
        try:
            start = parts[0].replace(",", "-")
            end = parts[1].replace(",", "-")
            mode = parts[2]
        except Exception:
            start = "2026-2-2"
            end = "2026-9-30"
            mode = "3"
    else:
        start = "2026-2-2"
        end = "2026-9-30"
        mode = "3"

    payload = {
        "DXCallbackName": "gridViewPlanyTokow",
        "__DXCallbackArgument": "c0:KV|2;[];GB|35;14|CUSTOMCALLBACK15|[object Object];",
        "gridViewPlanyTokow": '{"customOperationState":"","keys":[],"callbackState":"","groupLevelState":{},"selection":"","toolbar":null}',
        "gridViewPlanyTokow$custwindowState": '{"windowsState":"0:0:-1:0:0:0:-10000:-10000:1:0:0:0"}',
        "DXMVCEditorsValues": "{}",
        "parametry": f"{start};{end};{mode};{tok}",
        "id": tok,
    }

    for _ in range(3):
        r = s.post(URL_GRID, data=payload)
        r.raise_for_status()
        html = r.text
        if "<td" in html.lower():
            return html
        time.sleep(1)

    return None


def detect_group_column(html):
    """
    Endpoint diagnostyczny – wykrywa potencjalne kolumny grupy
    na podstawie pierwszego wiersza danych.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "gridViewPlanyTokow_DXMainTable"})
    if not table:
        return {"error": "Brak tabeli"}

    rows = table.find_all("tr")

    first_data_row = None
    for row in rows:
        if "dxgvDataRow_iOS" in row.get("class", []):
            first_data_row = row
            break

    if not first_data_row:
        return {"error": "Brak wiersza danych"}

    cells = first_data_row.find_all("td")
    cell_texts = [c.get_text(strip=True) for c in cells]

    patterns = {
        "cw": re.compile(r"Ćw(\d+)N", re.IGNORECASE),
        "wyk": re.compile(r"WykN", re.IGNORECASE),
        "num": re.compile(r"\b(\d+)\b")
    }

    detected = []

    for i, text in enumerate(cell_texts):
        for name, regex in patterns.items():
            m = regex.search(text)
            if m:
                detected.append({
                    "column_index": i,
                    "raw_text": text,
                    "pattern": name,
                    "match": m.group(0)
                })

    return {
        "cells": cell_texts,
        "detected": detected
    }


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

    cw_pattern = re.compile(r"Ćw(\d+)N", re.IGNORECASE)

    # 1. wykrywanie kolumny grupy na podstawie pierwszego wiersza
    first_data_row = None
    for row in rows:
        if "dxgvDataRow_iOS" in row.get("class", []):
            first_data_row = row
            break

    group_col_index = None
    if first_data_row:
        cells = first_data_row.find_all("td")
        for i, c in enumerate(cells):
            text = c.get_text(strip=True)
            if cw_pattern.search(text):
                group_col_index = i
                break

    if group_col_index is None:
        group_col_index = -1  # szukamy w całym wierszu

    # 2. parsowanie wszystkich wierszy
    for row in rows:
        classes = row.get("class", [])

        # wiersz z datą
        if "dxgvGroupRow_iOS" in classes:
            text = row.get_text(" ", strip=True)
            if "Data Zajęć:" in text:
                current_date = text.split("Data Zajęć:")[-1].strip()
            continue

        # wiersz danych
        if "dxgvDataRow_iOS" in classes:
            cells = row.find_all("td")
            if len(cells) < 10:
                continue

            # 3. wyciąganie numeru grupy tylko z Ćw\d+N
            group_code = ""

            if group_col_index >= 0:
                text = cells[group_col_index].get_text(strip=True)
                m = cw_pattern.search(text)
                if m:
                    group_code = m.group(1)
            else:
                for c in cells:
                    text = c.get_text(strip=True)
                    m = cw_pattern.search(text)
                    if m:
                        group_code = m.group(1)
                        break

            parsed.append({
                "data": cells[0].get_text(strip=True) if current_date is None else current_date,
                "od": cells[1].get_text(strip=True),
                "do": cells[2].get_text(strip=True),
                "godziny": cells[3].get_text(strip=True),
                "group_code": group_code,  # "" dla wykładów
                "przedmiot": cells[5].get_text(strip=True),
                "typ": cells[6].get_text(strip=True),
                "sala": cells[7].get_text(strip=True),
                "prowadzacy": cells[8].get_text(strip=True),
                "zaliczenie": cells[9].get_text(strip=True),
                "uwagi": cells[10].get_text(strip=True) if len(cells) > 10 else "",
            })

    return parsed if parsed else None


@app.get("/plan")
def get_plan(request: Request):
    tok = request.query_params.get("tok", "1337")

    if tok not in TOKS:
        return {"error": f"Nieznany tok: {tok}"}

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


@app.get("/debug-group")
def debug_group(request: Request):
    tok = request.query_params.get("tok", "1337")

    html = fetch_html(tok)
    if not html:
        return {"error": "Brak HTML z DSW"}

    info = detect_group_column(html)
    return info
