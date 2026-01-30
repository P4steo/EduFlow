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
            '{"customOperationState":"iwTcwXXoxNCDCiBzfj3X2QuDjD+ADs6tlFhX/P7bwZQFhL67iwavUFCMUwC4xIL87i5zDEQdaVzhrq48ee1ynlIDZodoNhIhVtLx3/kg5W40LJUeTpalJjmlG2x6VEBOhdHp50XtsPM1PtKWWYsyru0dlFbHI62t/PUcUzeanMkEaFLTQnP5uC0sWYtjCc7b7MAkJGnlmiuNSNuHbhgcKuarpTFkcUFkWs7KoJnR7HkeRzfMsMrZBv3Y1acMgEAi8Yww9UEtRRmVXqpNa7VdKgkvotGlJNMk7eskdGJh4oFpH2UE1+zAnlBpqIrkRffUsLDmqm+Tn/T1l0ecgRvLwM6Hjs1Zc2f2FN2ShjwH8A2+JvaqzE/UOY67s7SZofGrTrq4GaIheQIzE1+ZD8nl3mYHI4x9qDMhfiHRfGSj8lFt7y5xTfCSNHtL+IIRgFdg7uvWQLzU4TL3vnr6XqI5WANH47CWfDOf/fvQ54lIPT2ViDTJCsqoM1FGheL3+pGV3t3OOcExoRWP3H735AZHdOeyZWlJjnA90/AKd3jc7Uzer2sMzmOcCmjo4FP0N1E0Q+XvehBTVdE9y+qnMwZBDGw22pofiEEH1Qsh2JMtWXJ93AwLQBUL6Fiu/SIbS1P/kwjk3e+y6vol1DKqoRmHTH76mAkCzMVxzdtZeT9BOLM=",'
            '"keys":[],"callbackState":"zT85LZWjEyFRZDPQvzKVlX/7Er5lMQltZyp1z+AgQfWHmfP9HAEGHXFbSXLHHLvNvTGIzODD74yAci5gsfQ27aHPNnxnQ02s0pC/LPzMrzg202aP2UHrppLlyzw84sSaJDIbUEXYkBEMWcJqcO6eJlzk/zHlBj5seUWQR8me1JYIFMTbxKVyjqKYDUjgQAQKZ83FvgkpwuEslKDGMJzx2g84AofOSxo6UsNdW9Dj0pujp4jTBN7vlhyEgMrqFUS+dUiQX2ri2ex52uHea1nK6n0DrsMxqmUu6Jbp8IuR4nDI9AdSGXCvLF24QbLBlbXAw3987qXukW4dbCyVO3ZaHfIT65i44fdyP9IcoUu8EL0k0LYJl5rOJC2OwbJ7NWIRNk3BOLt1vwVuslsn9zJMBCIr8TJFhcHAeuakOESJ07meB5Gr7McFz66hnDBI/S48iZzIUxbSC47KYpx8oFMVojrWmT8tMiDGX23++MHYKSGFPObhN75zWn2HSvbjGg5aWFkIe135DhDDXZ4RrIo0u/bLGEzXggKmJC7REEG35C3xKxJEEj3L+GXP2+endHNG",'
            '"groupLevelState":{"0":[[0,0],[13,13],[25,25],[33,33],[40,40],[55,55],[76,76],[100,100],[117,117],[124,124],[131,131],[156,156],[175,175],[178,178],[187,187],[196,196],[215,215],[230,230],[254,254],[278,278],[281,281],[290,290],[306,306],[314,314]]},'
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

        parsed.append({
            "data": cols[1],
            "od": cols[2],
            "do": cols[3],
            "godziny": cols[4],
            "grupa": cols[5],
            "zajecia": cols[6],
            "forma": cols[7],
            "sala": cols[8],
            "prowadzacy": cols[9],
            "uwagi": cols[10],
        })

    return parsed


@app.get("/plan")
def get_plan():
    html = fetch_html()
    data = parse_plan(html)
    return data
