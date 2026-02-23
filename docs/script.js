const _URL = "https://eduflow-qivy.onrender.com/plan";

let fullData = [];
let filteredData = [];
let table = null;

let currentView = "cards";
let currentDateMode = "nearest";
let currentTok = "1337";
let currentGroup = "all";

let lastTimestamp = null;

/* KROPKA — FUNKCJE STANÓW */
function setDotLoading() {
  const dot = document.querySelector(".logo-dot");
  dot.classList.remove("loaded", "error", "idle");
  dot.classList.add("loading");
}

function setDotLoaded() {
  const dot = document.querySelector(".logo-dot");
  dot.classList.remove("loading", "error", "idle");
  dot.classList.add("loaded");

  setTimeout(() => {
    dot.classList.remove("loaded");
    dot.classList.add("idle");
  }, 3000);
}

function setDotError() {
  const dot = document.querySelector(".logo-dot");
  dot.classList.remove("loading", "loaded", "idle");
  dot.classList.add("error");
}

/* FETCH + RETRY */
async function fetchPlanWithRetry(retries = 5, delay = 1500) {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(`${_URL}?tok=${currentTok}&_=${Date.now()}`);
      const json = await res.json();

      if (json && json.data && Array.isArray(json.data)) {
        lastTimestamp = json.timestamp;
        return json.data;
      }
    } catch (e) {}

    await new Promise(resolve => setTimeout(resolve, delay));
  }
  return null;
}
async function loadData() {
  const cacheKey = "cachedPlan";
  const cacheTimeKey = "cachedPlanTimestamp";
  const maxAge = 1000 * 60 * 60 * 6;

  const cached = localStorage.getItem(cacheKey);
  const cachedTime = localStorage.getItem(cacheTimeKey);

  // OFFLINE → użyj cache lub data.json
  if (!navigator.onLine) {
    if (cached) {
      lastTimestamp = cachedTime / 1000;
      return JSON.parse(cached);
    }
    const local = await fetch("data.json");
    return await local.json();
  }

  // CACHE WAŻNY
  if (cached && cachedTime && Date.now() - cachedTime < maxAge) {
    lastTimestamp = cachedTime / 1000;
    return JSON.parse(cached);
  }

  // API
  const apiData = await fetchPlanWithRetry();

  if (apiData) {
    const now = Date.now();
    localStorage.setItem(cacheKey, JSON.stringify(apiData));
    localStorage.setItem(cacheTimeKey, now);
    lastTimestamp = now / 1000;
    return apiData;
  }

  // API padło → użyj cache
  if (cached) {
    lastTimestamp = cachedTime / 1000;
    return JSON.parse(cached);
  }

  // Ostateczny fallback
  const local = await fetch("data.json");
  return await local.json();
}


/* WEEKEND HELPERS */
function nextWeekendDate(fromDate = new Date()) {
  const d = new Date(fromDate);
  while (true) {
    const day = d.getDay();
    if (day === 6 || day === 0) return d;
    d.setDate(d.getDate() + 1);
  }
}

function findNearestWeekendRange() {
  let d = new Date();

  for (let i = 0; i < 60; i++) {
    const saturday = nextWeekendDate(d);
    const sunday = new Date(saturday);

    if (saturday.getDay() === 6) {
      sunday.setDate(saturday.getDate() + 1);
    } else {
      saturday.setDate(saturday.getDate() - 1);
    }

    const satStr = saturday.toISOString().split("T")[0].replace(/-/g, ".");
    const sunStr = sunday.toISOString().split("T")[0].replace(/-/g, ".");

    const hasSat = fullData.some(item => item.data && item.data.includes(satStr));
    const hasSun = fullData.some(item => item.data && item.data.includes(sunStr));

    if (hasSat || hasSun) {
      return { sat: satStr, sun: sunStr };
    }

    d.setDate(saturday.getDate() + 2);
  }

  return null;
}

function findNextWeekendRange(currentRange) {
  console.group("findNextWeekendRange() START");

  // 1. Pobieramy wszystkie daty i obcinamy dzień tygodnia
  const rawDates = fullData.map(ev => ev.data);
  console.log("rawDates:", rawDates);

  const cleanedDates = rawDates
    .map(str => {
      if (typeof str !== "string") return null;
      return str.split(" ")[0]; // bierzemy tylko YYYY.MM.DD
    })
    .filter(Boolean);

  console.log("cleanedDates:", cleanedDates);

  // 2. Filtrujemy poprawny format
  const uniqueDates = [...new Set(
    cleanedDates.filter(str => /^\d{4}\.\d{2}\.\d{2}$/.test(str))
  )];

  console.log("uniqueDates:", uniqueDates);

  // 3. Zamieniamy na Date
  const sorted = uniqueDates
    .map(str => {
      const [yy, mm, dd] = str.split(".").map(Number);
      const dt = new Date(yy, mm - 1, dd);
      if (isNaN(dt.getTime())) {
        console.error("❌ Invalid Date:", str);
        return null;
      }
      return dt;
    })
    .filter(Boolean)
    .sort((a, b) => a - b);

  console.log("sorted dates:", sorted);

  if (sorted.length === 0) {
    console.error("❌ No valid dates — cannot continue");
    console.groupEnd();
    return null;
  }

  // 4. Jeśli currentRange jest niepoprawny → pierwszy weekend
  if (!currentRange || !currentRange.sat || !currentRange.sun) {
    console.warn("⚠ currentRange invalid — using FIRST weekend");

    const first = sorted[0];
    const firstSun = new Date(first);
    firstSun.setDate(first.getDate() + 1);

    const result = {
      sat: first.toISOString().split("T")[0].replace(/-/g, "."),
      sun: firstSun.toISOString().split("T")[0].replace(/-/g, ".")
    };

    console.log("Returning FIRST weekend:", result);
    console.groupEnd();
    return result;
  }

  // 5. Normalne działanie
  const [y, m, d] = currentRange.sun.split(".").map(Number);
  const currentSun = new Date(y, m - 1, d);

  console.log("currentSun:", currentSun);

  let nextDate = sorted.find(dt => dt > currentSun);

  if (!nextDate) {
    console.warn("⚠ No next weekend — using LAST weekend");
    nextDate = sorted[sorted.length - 1];
  }

  const nextSun = new Date(nextDate);
  nextSun.setDate(nextDate.getDate() + 1);

  const result = {
    sat: nextDate.toISOString().split("T")[0].replace(/-/g, "."),
    sun: nextSun.toISOString().split("T")[0].replace(/-/g, ".")
  };

  console.log("Returning NEXT weekend:", result);
  console.groupEnd();
  return result;
}

/* FILTERING */
function filterByDateMode() {
  if (currentDateMode === "all") {
    document.getElementById("currentRangeLabel").textContent = "Cały semestr";
    return fullData.slice();
  }

  const nearest = findNearestWeekendRange();
  if (!nearest) {
    document.getElementById("currentRangeLabel").textContent = "Brak zjazdów w danych";
    return [];
  }

  if (currentDateMode === "nearest") {
    document.getElementById("currentRangeLabel").textContent =
      `Najbliższy zjazd: ${nearest.sat} – ${nearest.sun}`;

    return fullData.filter(item =>
      item.data && (item.data.includes(nearest.sat) || item.data.includes(nearest.sun))
    );
  }

  if (currentDateMode === "next") {
    const next = findNextWeekendRange(nearest);

    document.getElementById("currentRangeLabel").textContent =
      `Następny zjazd: ${next.sat} – ${next.sun}`;

    return fullData.filter(item =>
      item.data && (item.data.includes(next.sat) || item.data.includes(next.sun))
    );
  }

  return fullData.slice();
}

function filterByCustomDates(start, end) {
  const s = new Date(start);
  const e = new Date(end);

  const result = fullData.filter(item => {
    if (!item.data) return false;
    const d = new Date(item.data.replace(/\./g, "-"));
    return d >= s && d <= e;
  });

  document.getElementById("currentRangeLabel").textContent = `Zakres: ${start} – ${end}`;
  return result;
}

function applyGroupFilter(base) {
  if (currentGroup === "all") return base;

  return base.filter(item => {
    const group = item.group_code || "";
    const typ = (item.typ || "").toLowerCase();

    const isMyGroup = group === currentGroup;
    const isLecture = typ.includes("wyk");
    const isCommon = !group;

    return isMyGroup || isLecture || isCommon;
  });
}

/* GROUP FILTER UI */
function updateGroupFilter() {
  const select = document.getElementById("groupSelect");
  const groups = new Set();

  fullData.forEach(item => {
    if (item.group_code) groups.add(item.group_code);
  });

  const sorted = [...groups].sort((a, b) => a.localeCompare(b, "pl"));

  select.innerHTML = `<option value="all">Wszystkie</option>`;
  sorted.forEach(g => {
    select.innerHTML += `<option value="${g}">Grupa ${g}</option>`;
  });
}

/* RENDERING */
function updateNoDataMessage() {
  const msg = document.getElementById("noDataMessage");
  if (!filteredData || filteredData.length === 0) {
    msg.style.display = "block";
    msg.textContent = "Brak zajęć w wybranym zakresie.";
  } else {
    msg.style.display = "none";
  }
}

function applyAllFilters() {
  let base;

  if (currentDateMode === "custom") {
    const s = document.getElementById("startDate").value;
    const e = document.getElementById("endDate").value;
    if (s && e) {
      base = filterByCustomDates(s, e);
    } else {
      base = fullData.slice();
    }
  } else {
    base = filterByDateMode();
  }

  base = applyGroupFilter(base);

  filteredData = base;
  updateNoDataMessage();
  render();
}

function render() {
  if (currentView === "cards") {
    document.getElementById("cardsContainer").style.display = "flex";
    document.getElementById("tableContainer").style.display = "none";
    renderCards();
  } else {
    document.getElementById("cardsContainer").style.display = "none";
    document.getElementById("tableContainer").style.display = "block";
    renderTable();
  }
}

function groupByDate(data) {
  const map = {};
  data.forEach(item => {
    if (!map[item.data]) map[item.data] = [];
    map[item.data].push(item);
  });
  return Object.entries(map).sort((a, b) => new Date(a[0]) - new Date(b[0]));
}

function renderCards() {
  const container = document.getElementById("cardsContainer");
  container.innerHTML = "";

  const byDate = groupByDate(filteredData);

  byDate.forEach(([dateStr, items], i) => {
    if (i > 0) {
      const sep = document.createElement("hr");
      sep.style.margin = "10px 0";
      sep.style.borderColor = "rgba(31,41,55,0.7)";
      container.appendChild(sep);
    }

    const dayBlock = document.createElement("div");
    dayBlock.className = "day-block";

    const title = document.createElement("div");
    title.className = "day-title";
    title.textContent = dateStr;
    dayBlock.appendChild(title);

    items.sort((a, b) => {
      const t1 = new Date(`2000-01-01T${a.od}:00`);
      const t2 = new Date(`2000-01-01T${b.od}:00`);
      const diff = t1 - t2;
      if (diff !== 0) return diff;

      return (a.group_code || "").localeCompare(b.group_code || "");
    });

    items.forEach(item => {
      const card = document.createElement("div");
      card.className = "card";

      if (item.group_code) {
        card.classList.add(`group-${item.group_code}`);
      }

      const uwagiLower = ((item.uwagi || "") + " " + (item.zaliczenie || "")).toLowerCase();
      if (uwagiLower.includes("odwołane")) {
        card.classList.add("cancelled");
      }

      const top = document.createElement("div");
      top.className = "card-top";

      const time = document.createElement("div");
      time.className = "time";
      time.textContent = `${item.od}–${item.do}`;
      top.appendChild(time);

      card.appendChild(top);

      const main = document.createElement("div");
      main.className = "card-main";
      main.textContent = item.przedmiot || "Zajęcia";
      card.appendChild(main);

      const meta = document.createElement("div");
      meta.className = "card-meta";

      if (!item.group_code) {
        meta.innerHTML += `<span>Wykład</span>`;
      } else {
        meta.innerHTML += `<span>Grupa ${item.group_code}</span>`;
      }

      if (item.sala) meta.innerHTML += `<span>${item.sala}</span>`;
      if (item.prowadzacy) meta.innerHTML += `<span>${item.prowadzacy}</span>`;

      card.appendChild(meta);

      const uwagiParts = [];
      if (item.zaliczenie) uwagiParts.push(item.zaliczenie);
      if (item.uwagi && item.uwagi.toLowerCase() !== "brak") uwagiParts.push(item.uwagi);
      const uwagiDisplay = uwagiParts.join(", ");

      if (uwagiDisplay) {
        const uw = document.createElement("div");
        uw.className = "card-uwagi";
        uw.textContent = uwagiDisplay;
        card.appendChild(uw);
      }

      dayBlock.appendChild(card);
    });

    container.appendChild(dayBlock);
  });
}

function renderTable() {
  const rows = filteredData
    .sort((a, b) => {
      const d1 = new Date(a.data.replace(/\./g, "-"));
      const d2 = new Date(b.data.replace(/\./g, "-"));
      const diffDate = d1 - d2;
      if (diffDate !== 0) return diffDate;

      const t1 = new Date(`2000-01-01T${a.od}:00`);
      const t2 = new Date(`2000-01-01T${b.od}:00`);
      const diffTime = t1 - t2;
      if (diffTime !== 0) return diffTime;

      return (a.group_code || "").localeCompare(b.group_code || "");
    })
    .map(item => {
      const uwagiParts = [];
      if (item.zaliczenie) uwagiParts.push(item.zaliczenie);
      if (item.uwagi && item.uwagi.toLowerCase() !== "brak") uwagiParts.push(item.uwagi);
      const uwagiDisplay = uwagiParts.join(", ");

      return [
        item.data,
        item.od,
        item.do,
        item.group_code ? `Grupa ${item.group_code}` : "Wykład",
        item.przedmiot,
        item.sala,
        item.prowadzacy,
        uwagiDisplay
      ];
    });

  if (!table) {
    table = $('#planTable').DataTable({
      data: rows,
      columns: [
        { title: "Data" },
        { title: "Od" },
        { title: "Do" },
        { title: "Grupa / Wykład" },
        { title: "Zajęcia" },
        { title: "Sala" },
        { title: "Prowadzący" },
        { title: "Uwagi" }
      ],
      pageLength: 50,
      language: {
        url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/pl.json"
      },
      createdRow: function (row, data) {
        const uwagi = (data[7] || "").toLowerCase();
        if (uwagi.includes("odwołane")) {
          row.classList.add("cancelled");
        }
      }
    });
  } else {
    table.clear();
    table.rows.add(rows);
    table.draw();
  }
}
/* INIT */
async function init() {
  setDotLoading();
  document.getElementById("noDataMessage").textContent = "Ładowanie danych…";
  document.getElementById("noDataMessage").style.display = "block";

  const data = await loadData();

  if (!data) {
    document.getElementById("noDataMessage").textContent =
      "Brak danych z serwera. Spróbuj ponownie.";
    setDotError();
    return;
  }

  fullData = data;

  document.getElementById("statusBox").textContent =
    "Dane zaktualizowano: " +
    new Date(lastTimestamp * 1000).toLocaleString("pl-PL");

  document.getElementById("noDataMessage").style.display = "none";

  updateGroupFilter();
  applyAllFilters();
  setDotLoaded();
}

/* EVENTS */
document.getElementById("specSelect").addEventListener("change", e => {
  currentTok = e.target.value;
  init();
});

document.getElementById("groupSelect").addEventListener("change", e => {
  currentGroup = e.target.value;
  applyAllFilters();
});

document.querySelectorAll(".date-mode-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".date-mode-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentDateMode = btn.dataset.mode;
    document.getElementById("customDates").style.display =
      currentDateMode === "custom" ? "flex" : "none";
    applyAllFilters();
  });
});

document.getElementById("applyCustomDates").addEventListener("click", () => {
  currentDateMode = "custom";
  applyAllFilters();
});

document.getElementById("viewCards").addEventListener("click", () => {
  currentView = "cards";
  document.getElementById("viewCards").classList.add("active");
  document.getElementById("viewTable").classList.remove("active");
  render();
});

document.getElementById("reloadBtn").addEventListener("click", async () => {
  setDotLoading();
  document.getElementById("statusBox").textContent = "Odświeżanie…";
  document.getElementById("noDataMessage").style.display = "block";
  document.getElementById("noDataMessage").textContent = "Ładowanie danych…";

  const data = await fetchPlanWithRetry();

  if (!data) {
    document.getElementById("noDataMessage").textContent =
      "Brak danych z serwera. Spróbuj ponownie.";
    setDotError();

    fullData = [];
    updateGroupFilter();
    applyAllFilters();
    return;
  }

  fullData = data;

  localStorage.setItem("cachedPlan", JSON.stringify(data));
  localStorage.setItem("cachedPlanTimestamp", Date.now());
  lastTimestamp = Date.now() / 1000;

  document.getElementById("statusBox").textContent =
    "Dane zaktualizowano: " +
    new Date(lastTimestamp * 1000).toLocaleString("pl-PL");

  updateGroupFilter();
  applyAllFilters();
  setDotLoaded();
});


/* MOBILE MENU */
const mobileBtn = document.getElementById("mobileMenuBtn");
const sidebar = document.querySelector(".sidebar");

function toggleSidebar() {
  if (window.innerWidth > 768) return; // tylko mobile

  const isOpen = sidebar.classList.toggle("open");

  document.querySelector(".app").classList.toggle("sidebar-open", isOpen);
  document.body.classList.toggle("sidebar-open", isOpen);
  mobileBtn.classList.toggle("active", isOpen);
}

mobileBtn.addEventListener("click", toggleSidebar);

function updateMobileMode() {
  if (window.innerWidth <= 768) {
    mobileBtn.style.display = "block";
  } else {
    mobileBtn.style.display = "none";
    sidebar.classList.remove("open");
    document.querySelector(".app").classList.remove("sidebar-open");
    document.body.classList.remove("sidebar-open");
    mobileBtn.classList.remove("active");
  }
}

document.addEventListener("click", (e) => {
  if (window.innerWidth > 768) return;

  if (!sidebar.contains(e.target) && e.target !== mobileBtn) {
    sidebar.classList.remove("open");
    document.querySelector(".app").classList.remove("sidebar-open");
    document.body.classList.remove("sidebar-open");
    mobileBtn.classList.remove("active");
  }
});

window.addEventListener("resize", updateMobileMode);
updateMobileMode();

/* START */
init();

// ===============================
// BANER – aktualizacja aplikacji (UI)
// ===============================
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("./sw.js")
      .then(reg => {
        reg.addEventListener("updatefound", () => {
          const newWorker = reg.installing;
          if (!newWorker) return;

          newWorker.addEventListener("statechange", () => {
            if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
              document.getElementById("iosUpdateBanner").classList.add("show");
            }
          });
        });
      });
  });
}

// kliknięcie w "Odśwież"
window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("iosRefreshBtn").addEventListener("click", () => {
    document.getElementById("iosUpdateBanner").classList.remove("show");
    window.location.reload();
  });
});

