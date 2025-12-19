// Home page: Upcoming OTT + New Releases + Catalog + Recent/Updated + Tabs + Search

const FILE_UPCOMING_OTT = "data/upcoming-ott.json";
const FILE_NEW_OTT = "data/ott-releases.json";
const FILE_BEST_INDIA = "data/best-india.json";
const PLACEHOLDER_POSTER = "images/placeholder.jpg";

// Language sort order (lower number = higher priority)
const LANGUAGE_ORDER = {
  hindi: 1,
  telugu: 2,
  tamil: 3,
  malayalam: 4
};

const bestGrid = document.getElementById("bestGrid");
const bestPagination = document.getElementById("bestPagination");
const bestCount = document.getElementById("bestCount");
const upcomingGrid = document.getElementById("upcomingGrid");
const newGrid = document.getElementById("newGrid");
const newPagination = document.getElementById("newPagination");
const newCount = document.getElementById("newCount");
const catalogGrid = document.getElementById("catalogGrid");
const catalogPagination = document.getElementById("catalogPagination");
const catalogCount = document.getElementById("catalogCount");
const recentList = document.getElementById("recentList");
const recentMoreBtn = document.getElementById("recentMoreBtn");
const notice = document.getElementById("notice");

const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");

const tabs = Array.from(document.querySelectorAll(".tab"));

let allMovies = [];
let bestIndia = [];

let activeIndustry = "all"; // all | bollywood | telugu | tamil | malayalam
let activeQuery = "";
let bestPage = 1;
let newPage = 1;
let catalogPage = 1;
const bestPageSize = 9;
const newPageSize = 9;
const catalogPageSize = 9;

let recentShown = 0;
const recentBatch = 12;

const cache = {};

function norm(v) {
  return (v ?? "").toString().trim().toLowerCase();
}

function langRank(lang) {
  return LANGUAGE_ORDER[norm(lang)] ?? 999;
}

function dateOnly(d) {
  const s = (d ?? "").toString().trim();
  return s.includes(" ") ? s.split(" ")[0] : s;
}

function parseReleaseDate(raw) {
  if (!raw) return NaN;
  const datePart = String(raw).trim().split(" ")[0];
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(datePart);
  if (!match) return NaN;

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const dt = new Date(year, month - 1, day);
  if (dt.getFullYear() !== year || dt.getMonth() !== month - 1 || dt.getDate() !== day) {
    return NaN;
  }
  dt.setHours(0, 0, 0, 0);
  return dt.getTime();
}

function startOfToday() {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return now.getTime();
}

function monthsAgo(n) {
  const dt = new Date();
  dt.setMonth(dt.getMonth() - n);
  dt.setHours(0, 0, 0, 0);
  return dt.getTime();
}

function addComputedFields(list) {
  const today = startOfToday();
  const sixMonthsBack = monthsAgo(6);

  return list.map(m => {
    const rd = parseReleaseDate(m.releaseDate);
    let bucket = "catalog";

    if (Number.isFinite(rd)) {
      if (rd > today) bucket = "upcoming";
      else if (rd >= sixMonthsBack && rd <= today) bucket = "new";
    }

    return {
      ...m,
      _releaseDateValue: rd,
      _bucket: bucket
    };
  });
}

function sortByDateThenLanguage(arr, direction) {
  const fallback = direction === "asc" ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY;
  return [...arr].sort((a, b) => {
    const da = Number.isFinite(a._releaseDateValue) ? a._releaseDateValue : fallback;
    const db = Number.isFinite(b._releaseDateValue) ? b._releaseDateValue : fallback;
    if (da !== db) return direction === "asc" ? da - db : db - da;
    return langRank(a.language) - langRank(b.language);
  });
}

function normalizeProvider(raw) {
  const v = norm(raw);
  if (!v) return "";
  if (v.includes("netflix")) return "netflix";
  if (v.includes("hotstar")) return "hotstar";
  if (v.includes("prime")) return "prime";
  if (v.includes("hulu")) return "hulu";
  if (v.includes("zee")) return "zee5";
  if (v.includes("sonyliv") || v.includes("sony")) return "sonyliv";
  return v;
}

function buildOttUrl(movie) {
  const provider = normalizeProvider(movie.ott);

  if (provider === "netflix" && movie.netflixTitleId) {
    return `https://www.netflix.com/title/${movie.netflixTitleId}`;
  }

  if (provider === "hotstar" && movie.hotstar) {
    const { market, type, slug, id } = movie.hotstar;
    if (market && type && slug && id) {
      return `https://www.hotstar.com/${market}/${type}/${slug}/${id}`;
    }
  }

  if (provider === "zee5" && movie.zee5) {
    const { market, type, slug, id } = movie.zee5;
    if (market && type && slug && id) {
      return `https://www.zee5.com/${market}/${type}/${slug}/${id}`;
    }
  }

  if (provider === "prime" && movie.watchUrl) {
    return movie.watchUrl;
  }

  return movie.watchUrl || movie.watchLink || "";
}

function badge(label, cls = "") {
  return `<span class="badge ${cls}">${label}</span>`;
}

function ottBadges(m) {
  const list = Array.isArray(m.ottList) && m.ottList.length ? m.ottList : (m.ott ? [m.ott] : []);
  if (!list.length) return "";

  const labels = {
    netflix: "Netflix",
    prime: "Prime",
    hotstar: "Hotstar",
    zee5: "Zee5"
  };

  return list.map(item => {
    const key = normalizeProvider(item);
    const label = labels[key] || item;
    return badge(label);
  }).join("");
}

function getPoster(m) {
  return m.posterUrl || m.poster || PLACEHOLDER_POSTER;
}

function posterHtml(m) {
  const poster = getPoster(m);
  const provider = normalizeProvider(m.ott);
  const yt = m.youtubeId || "";

  return `
    <div class="card-media" data-ott="${provider}" data-youtube-id="${yt}" data-poster="${poster}">
      <img src="${poster}" alt="${m.title || ""}" loading="lazy" />
    </div>
  `;
}

function cardHtml(m) {
  const g = Array.isArray(m.genres) ? m.genres : (Array.isArray(m.genre) ? m.genre : []);
  const watchLink = buildOttUrl(m);
  const releaseLabel = dateOnly(m.releaseDate);

  return `
    <div class="card">
      ${posterHtml(m)}
      <div class="card-body">
        <h4 class="card-title">${m.title || ""}</h4>
        <div class="badges">
          ${releaseLabel ? badge(releaseLabel) : ""}
          ${m.language ? badge(m.language) : ""}
          ${ottBadges(m)}
          ${g.length ? badge(g.slice(0, 3).join(", ")) : ""}
          ${(m.rating !== null && m.rating !== undefined) ? badge(`⭐ ${m.rating}`, "star") : ""}
        </div>
        ${watchLink ? `<a class="watch-btn" href="${watchLink}" target="_blank" rel="noopener">Watch Now</a>` : ""}
        <div class="card-desc">${m.description || ""}</div>
      </div>
    </div>
  `;
}

// Industry mapping rules:
// - Prefer movie.industry if present
// - Else use language
// - Bollywood ≈ Hindi (as a practical default)
function matchesIndustry(m, industry) {
  if (!industry || industry === "all") return true;

  const ind = norm(m.industry);
  const lang = norm(m.language);

  if (ind) return ind === industry;

  if (industry === "bollywood") return lang === "hindi" || lang === "bollywood";
  return lang === industry;
}

function matchesQuery(m, q) {
  if (!q) return true;
  const hay = [
    m.title,
    m.description,
    ...(Array.isArray(m.genre) ? m.genre : []),
    ...(Array.isArray(m.genres) ? m.genres : []),
    m.language,
    m.region,
    ...(Array.isArray(m.ottList) ? m.ottList : []),
    m.ott
  ].map(norm).join(" ");
  return hay.includes(q);
}

function getUpcomingFiltered() {
  return sortByDateThenLanguage(
    allMovies
      .filter(m => m._bucket === "upcoming")
      .filter(m => matchesIndustry(m, activeIndustry))
      .filter(m => matchesQuery(m, norm(activeQuery))),
    "asc"
  ).slice(0, 50);
}

function getNewFiltered() {
  return sortByDateThenLanguage(
    allMovies
      .filter(m => m._bucket === "new")
      .filter(m => matchesIndustry(m, activeIndustry))
      .filter(m => matchesQuery(m, norm(activeQuery))),
    "desc"
  ).slice(0, 50);
  console.log(new Date().toString());
  console.log("new/upcoming/catalog", getNewFiltered().length, getUpcomingFiltered().length, getCatalogFiltered().length);

}

function getCatalogFiltered() {
  return sortByDateThenLanguage(
    allMovies
      .filter(m => m._bucket === "catalog")
      .filter(m => matchesIndustry(m, activeIndustry))
      .filter(m => matchesQuery(m, norm(activeQuery))),
    "desc"
  ).slice(0, 50);
}

function getBestFiltered() {
  return sortByDateThenLanguage(
    bestIndia
      .filter(m => matchesIndustry(m, activeIndustry))
      .filter(m => matchesQuery(m, norm(activeQuery))),
    "desc"
  ).slice(0, 50);
}

function getRecentMergedFiltered() {
  const filtered = allMovies
    .filter(m => matchesIndustry(m, activeIndustry))
    .filter(m => matchesQuery(m, norm(activeQuery)));

  return sortByDateThenLanguage(filtered, "desc").slice(0, 50);
}

function showNotice(msg) {
  notice.textContent = msg || "";
}

async function loadJson(path) {
  if (cache[path]) return cache[path];
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path} (${res.status})`);
  const data = await res.json();
  cache[path] = Array.isArray(data) ? data : [];
  return cache[path];
}

function renderBest() {
  if (!bestGrid || !bestPagination) return;

  const list = getBestFiltered();
  const totalPages = Math.max(1, Math.ceil(list.length / bestPageSize));
  if (bestPage > totalPages) bestPage = totalPages;

  const start = (bestPage - 1) * bestPageSize;
  const pageItems = list.slice(start, start + bestPageSize);

  if (bestCount) {
    bestCount.textContent = list.length ? `${list.length} titles` : "";
  }

  bestGrid.innerHTML = pageItems.length
    ? pageItems.map(cardHtml).join("")
    : `<div class="muted">No best picks match your filters.</div>`;

  bestPagination.innerHTML = "";
  for (let p = 1; p <= totalPages; p++) {
    const btn = document.createElement("button");
    btn.textContent = p;
    if (p === bestPage) btn.classList.add("active");
    btn.onclick = () => { bestPage = p; renderAll(); };
    bestPagination.appendChild(btn);
  }
}

function renderUpcoming() {
  const list = getUpcomingFiltered().slice(0, 4);
  upcomingGrid.innerHTML = list.length
    ? list.map(cardHtml).join("")
    : `<div class="muted">No upcoming matches.</div>`;
}

function renderNew() {
  const list = getNewFiltered();
  const totalPages = Math.max(1, Math.ceil(list.length / newPageSize));
  if (newPage > totalPages) newPage = totalPages;

  const start = (newPage - 1) * newPageSize;
  const pageItems = list.slice(start, start + newPageSize);

  newCount.textContent = list.length ? `${list.length} titles` : "";

  newGrid.innerHTML = pageItems.length
    ? pageItems.map(cardHtml).join("")
    : `<div class="muted">No new releases match your filters.</div>`;

  newPagination.innerHTML = "";
  for (let p = 1; p <= totalPages; p++) {
    const btn = document.createElement("button");
    btn.textContent = p;
    if (p === newPage) btn.classList.add("active");
    btn.onclick = () => { newPage = p; renderAll(); };
    newPagination.appendChild(btn);
  }
}

function renderCatalog() {
  if (!catalogGrid || !catalogPagination) return;

  const list = getCatalogFiltered();
  const totalPages = Math.max(1, Math.ceil(list.length / catalogPageSize));
  if (catalogPage > totalPages) catalogPage = totalPages;

  const start = (catalogPage - 1) * catalogPageSize;
  const pageItems = list.slice(start, start + catalogPageSize);

  if (catalogCount) {
    catalogCount.textContent = list.length ? `${list.length} titles` : "";
  }

  catalogGrid.innerHTML = pageItems.length
    ? pageItems.map(cardHtml).join("")
    : `<div class="muted">No catalog titles match your filters.</div>`;

  catalogPagination.innerHTML = "";
  for (let p = 1; p <= totalPages; p++) {
    const btn = document.createElement("button");
    btn.textContent = p;
    if (p === catalogPage) btn.classList.add("active");
    btn.onclick = () => { catalogPage = p; renderAll(); };
    catalogPagination.appendChild(btn);
  }
}

function renderRecent(reset = false) {
  const list = getRecentMergedFiltered();

  if (reset) {
    recentShown = 0;
    recentList.innerHTML = "";
  }

  const next = list.slice(recentShown, recentShown + recentBatch);
  recentShown += next.length;

  if (!next.length && reset) {
    recentList.innerHTML = `<div class="muted">No recent items.</div>`;
  } else {
    recentList.insertAdjacentHTML("beforeend", next.map(m => {
      const g = Array.isArray(m.genres) ? m.genres : (Array.isArray(m.genre) ? m.genre : []);
      const releaseLabel = dateOnly(m.releaseDate);
      return `
        <div class="recent-item">
          <div class="recent-title">${m.title || ""}</div>
          <div class="recent-meta">
            ${releaseLabel ? `<span>${releaseLabel}</span>` : ""}
            ${m.language ? `<span>${m.language}</span>` : ""}
            ${m.ott ? `<span>${m.ott}</span>` : ""}
            ${g.length ? `<span>${g[0]}</span>` : ""}
          </div>
        </div>
      `;
    }).join(""));
  }

  recentMoreBtn.style.display = (recentShown >= list.length) ? "none" : "inline-block";
}

function renderAll() {
  if (activeQuery) {
    showNotice(`Search: "${activeQuery}" (industry: ${activeIndustry.toUpperCase()})`);
  } else {
    showNotice("");
  }

  renderBest();
  renderUpcoming();
  renderNew();
  renderCatalog();
  renderRecent(true);
}


// Tabs
tabs.forEach(t => {
  t.addEventListener("click", () => {
    tabs.forEach(x => x.classList.remove("active"));
    t.classList.add("active");

    activeIndustry = t.dataset.industry;
    bestPage = 1;
    newPage = 1;
    catalogPage = 1;
    renderAll();
  });
});

// Search
function runSearch() {
  activeQuery = searchInput.value.trim();
  bestPage = 1;
  newPage = 1;
  catalogPage = 1;
  renderAll();
}
searchBtn.addEventListener("click", runSearch);
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") runSearch();
});

// Recent load more
recentMoreBtn.addEventListener("click", () => renderRecent(false));

// Init
(async function init() {
  try {
    const [upcomingOtt, newOtt, bestList] = await Promise.all([
      loadJson(FILE_UPCOMING_OTT),
      loadJson(FILE_NEW_OTT),
      loadJson(FILE_BEST_INDIA)
    ]);

    bestIndia = addComputedFields(bestList);
    allMovies = addComputedFields([...upcomingOtt, ...newOtt, ...bestList]);

    renderAll();
  } catch (err) {
    console.error(err);
    showNotice(err.message || "Failed to load data files.");
    upcomingGrid.innerHTML = "";
    newGrid.innerHTML = "";
    if (catalogGrid) catalogGrid.innerHTML = "";
    if (bestGrid) bestGrid.innerHTML = "";
    recentList.innerHTML = "";
  }
})();
