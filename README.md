# 🚀 EduFlow – Twój inteligentny harmonogram zjazdów DSW

![GitHub Pages](https://img.shields.io/badge/Deploy-GitHub%20Pages-0a84ff?style=for-the-badge)
![API Status](https://img.shields.io/badge/API-Online-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-BSD-blue?style=for-the-badge)
![Made with JS](https://img.shields.io/badge/Made%20with-JavaScript-f7df1e?style=for-the-badge)
![Mobile Friendly](https://img.shields.io/badge/Mobile-Friendly-brightgreen?style=for-the-badge)

EduFlow automatycznie pobiera, przetwarza i prezentuje plan zjazdów DSW w nowoczesnej, przejrzystej formie.  
Zero PDF‑ów, zero chaosu — tylko szybki dostęp do tego, co naprawdę ważne.

---

## 🔗 Linki

👉 **Aplikacja online:** https://p4steo.github.io/EduFlow/  
👉 **API:** https://eduflow-qivy.onrender.com/plan  

---

## ⭐ Najważniejsze funkcje

- 📅 Automatyczne wykrywanie najbliższego zjazdu  
- 🔁 Obliczanie następnego zjazdu  
- 🗂 Filtrowanie po grupach i wykładach wspólnych  
- 🎴 Widok kart z przejrzystym grupowaniem po dniach  
- 📱 Dedykowany tryb mobilny z wysuwanym panelem filtrów  
- 🌫 Rozmycie tła (blur overlay) podczas otwartego sidebaru  
- ⚠️ Oznaczanie zajęć odwołanych  
- 🔄 Ręczne odświeżanie danych  
- 🕒 Informacja o ostatniej aktualizacji  
- 💾 Cache danych (localStorage) z automatycznym wygaszaniem  
- 📡 Tryb offline z fallbackiem do `data.json`  
- 🎨 Podświetlanie aktualnie trwających zajęć  
- 🔍 Zaawansowane filtrowanie zakresu dat (najbliższy, następny, cały semestr, własny zakres)

---

## 🧰 Technologie

**Frontend:**  
- HTML  
- CSS  
- JavaScript (vanilla)

**Backend:**  
- FastAPI  
- Python  
- BeautifulSoup4  
- Requests  

---

## 🧱 Architektura

### Backend
- Pobiera oficjalny harmonogram DSW  
- Parsuje PDF/HTML do strukturyzowanego JSON  
- Zwraca dane w formacie przyjaznym frontendowi  
- Cache po stronie serwera, aby odciążyć źródło  

### Frontend
- Pobiera dane z API z retry + fallback  
- Przechowuje dane w localStorage (6h TTL)  
- Renderuje widok kart  
- Obsługuje tryb offline  
- Dynamicznie filtruje i grupuje dane  
- Wykrywa najbliższy i następny weekend zjazdowy  
- Zapewnia pełny tryb mobilny z rozmyciem tła i blokadą scrolla  

---

## 📱 Tryb mobilny

- Wysuwany sidebar z filtrami  
- Rozmycie tła (backdrop blur)  
- Blokada scrolla podczas otwartego menu  
- Automatyczne zamykanie sidebaru po kliknięciu poza nim  
- Pełna obsługa selectów i inputów bez przypadkowego zamykania menu  

---

## 🧪 Funkcje UI

### Widok kart
- Grupowanie po dacie  
- Sortowanie po godzinach  
- Kolorowe oznaczenia grup  
- Podświetlanie aktualnych zajęć  
- Oznaczanie odwołanych zajęć  
- Przejrzyste separatory dni  

---

## 🛠 Build & Deployment

- Frontend hostowany na GitHub Pages  
- Backend hostowany na Render.com  
- Automatyczne odświeżanie Service Workera  
- Cache busting przez query param `?_=timestamp`  

---

## 🧹 Roadmap

- 🔔 Powiadomienia o zmianach w planie  
- 📆 Eksport do kalendarza (ICS)  
- 🌓 Tryb jasny / ciemny  
- 🔍 Wyszukiwanie po przedmiotach i prowadzących  
- 🧪 Testy jednostkowe i e2e  

---

## 📜 Changelog

Pełna historia zmian znajduje się tutaj:  
👉 **CHANGELOG.md**

---

## 📜 Licencja

Projekt dostępny na licencji **BSD**.
