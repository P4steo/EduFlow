# **EduFlow – Interaktywny harmonogram zjazdów DSW** 

---

## 🔰 Badges

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Frontend](https://img.shields.io/badge/frontend-HTML%2FCSS%2FJS-blue)
![Backend](https://img.shields.io/badge/backend-FastAPI-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Responsive](https://img.shields.io/badge/mobile-friendly-orange)
![Data](https://img.shields.io/badge/data-auto--updated-lightgrey)

---


## 🎓 EduFlow – Interaktywny harmonogram zjazdów DSW

EduFlow to responsywna aplikacja webowa, która pobiera i prezentuje plan zjazdów dla studentów DSW w czytelnej formie kart lub tabeli.  
Projekt automatycznie analizuje dane z oficjalnego harmonogramu i grupuje je według dni oraz grup.

🔗 **Live demo:** https://p4steo.github.io/EduFlow/ 
🔗 **API backend:** https://eduflow-qivy.onrender.com/plan

---

## ✨ Funkcje

- 📅 Automatyczne wykrywanie **najbliższego zjazdu** (sobota + niedziela)
- 🔁 **Następny zjazd** obliczany jako +7 dni
- 🗂 Filtrowanie po grupach (Ćw1N, Ćw2N, WykN itd.)
- 🗓 Zakresy dat: cały semestr, najbliższy, następny, własny
- 🧭 Dwa widoki: **karty** oraz **tabela**
- 🔄 Przycisk **„Załaduj ponownie dane”**
- ⚠️ Oznaczanie zajęć odwołanych
- 📱 Pełna responsywność + mobilne menu (hamburger)
- 🕒 Status ostatniej aktualizacji danych
- 🧹 Grupowanie zajęć według dni

---

## 🛠 Technologie

### Frontend
- HTML5  
- CSS3 (w tym mobile mode)  
- JavaScript (ES6+)  
- DataTables  

### Backend
- Python  
- FastAPI  
- BeautifulSoup4  
- Requests  
- Cache z TTL + fallback  


