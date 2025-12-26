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

const bestCarousel = document.getElementById("bestCarousel");
const bestPrev = document.getElementById("bestPrev");
const bestNext = document.getElementById("bestNext");
const bestDots = document.getElementById("bestDots");
const bestPagination = document.getElementById("bestPagination");
const bestCount = document.getElementById("bestCount");
const upcomingCarousel = document.getElementById("upcomingCarousel");
const upcomingPrev = document.getElementById("upcomingPrev");
const upcomingNext = document.getElementById("upcomingNext");
const upcomingDots = document.getElementById("upcomingDots");
const upcomingCount = document.getElementById("upcomingCount");
const newCarousel = document.getElementById("newCarousel");
const newPrev = document.getElementById("newPrev");
const newNext = document.getElementById("newNext");
const newDots = document.getElementById("newDots");
const newPagination = document.getElementById("newPagination");
const newCount = document.getElementById("newCount");
const catalogGrid = document.getElementById("catalogGrid");
const catalogPagination = document.getElementById("catalogPagination");
const catalogCount = document.getElementById("catalogCount");

// Carousel state
let upcomingCarouselPage = 0;
let newCarouselPage = 0;
let bestCarouselPage = 0;
const cardsPerPage = 6;
const recentList = document.getElementById("recentList");
const recentMoreBtn = document.getElementById("recentMoreBtn");
const notice = document.getElementById("notice");

const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");

const tabs = Array.from(document.querySelectorAll(".tab"));

let allMovies = [];
let bestIndia = [];

// === STATE: Navigation (tab/category selection) ===
let activeIndustry = "all"; // all | bollywood | telugu | tamil | malayalam

// === STATE: Search (filtering within navigation) ===
let activeQuery = "";

// === STATE: Pagination (resets on navigation or search change) ===
// Each section maintains its own independent pagination
let bestPage = 1;
let newPage = 1;
let catalogPage = 1;
const bestPageSize = 9;
const newPageSize = 9;
const catalogPageSize = 9;

// === STATE: Pagination preservation (for search clear) ===
// Saves pagination state before search to restore when search is cleared
let savedPagination = null;

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
  const twelveMonthsBack = monthsAgo(12);

  return list.map(m => {
    const rd = parseReleaseDate(m.releaseDate);
    let bucket = "catalog";

    if (Number.isFinite(rd)) {
      if (rd > today) bucket = "upcoming";
      else if (rd >= twelveMonthsBack && rd <= today) bucket = "new";
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
  if (v.includes("hotstar") || v.includes("jiohotstar")) return "jiohotstar";
  if (v.includes("prime")) return "prime";
  if (v.includes("hulu")) return "hulu";
  if (v.includes("zee5")) return "zee5";
  if (v.includes("sonyliv") || v.includes("sony")) return "sonyliv";
  if (v.includes("manorama")) return "manorama";
  if (v.includes("sunnxt") || v.includes("sun nxt")) return "sunnxt";
  if (v.includes("aha")) return "aha";
  if (v.includes("zeestudios")) return "zeestudios";
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

function getPrimaryOtt(m) {
  // Handle primaryOtt field first
  if (m.primaryOtt) {
    return m.primaryOtt;
  }
  
  // Handle ottList (usually a JSON array like ["Netflix", "Prime Video"])
  if (m.ottList) {
    try {
      let ottArray = m.ottList;
      if (typeof ottArray === 'string') {
        ottArray = JSON.parse(ottArray);
      }
      if (Array.isArray(ottArray) && ottArray.length > 0) {
        return ottArray[0];
      }
    } catch (e) {
      // If not JSON, treat as string
      if (typeof m.ottList === 'string') {
        return m.ottList;
      }
    }
  }
  
  // Fallback to ott field
  return m.ott || "";
}

function posterHtml(m) {
  const poster = getPoster(m);
  const primaryOtt = getPrimaryOtt(m);
  const provider = normalizeProvider(primaryOtt);
  const yt = m.youtubeId || "";

  return `
    <div class="card-media" data-ott="${provider}" data-youtube-id="${yt}" data-poster="${poster}">
      <img src="${poster}" alt="${m.title || ""}" loading="lazy" />
    </div>
  `;
}

function cardHtml(m, yearOnly = false) {
  const g = Array.isArray(m.genres) ? m.genres : (Array.isArray(m.genre) ? m.genre : []);
  const watchLink = buildOttUrl(m);
  const releaseLabel = yearOnly ? (m.releaseDate ? m.releaseDate.split('-')[0] : '') : dateOnly(m.releaseDate);
  const actors = Array.isArray(m.actors) && m.actors.length ? m.actors.slice(0, 3).join(", ") : "";

  return `
    <div class="card">
      ${posterHtml(m)}
      <div class="card-body">
        <h4 class="card-title">${m.title || ""}</h4>
        ${actors ? `<div class="card-cast">Cast: ${actors}</div>` : ""}
        <div class="badges">
          ${releaseLabel ? badge(releaseLabel) : ""}
          ${m.language ? badge(m.language) : ""}
          ${ottBadges(m)}
          ${g.length ? badge(g.slice(0, 3).join(", ")) : ""}
          ${(m.rating !== null && m.rating !== undefined) ? badge(`★ ${m.rating}/10`, "star") : ""}
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
  ].join(" ").toLowerCase();
  return hay.includes(q);
}

// === DATA COMPLETENESS FILTER ===
// Hide movies with no OTT or no rating
function isDataComplete(m) {
  // Must have OTT information (not "all" or empty)
  const hasOtt = m.ott && norm(m.ott) && norm(m.ott) !== "all";
  // Must have a rating (not null, undefined, or NaN - but 0 is valid)
  const hasRating = m.rating !== null && m.rating !== undefined && !Number.isNaN(m.rating);
  return hasOtt && hasRating;
}

// === SECTION-SCOPED FILTERING ===
// Each section filters its OWN data independently
// Search does NOT move results between sections
// Results stay in their original section (upcoming → Upcoming OTT, new → New Releases, etc.)

function getUpcomingFiltered() {
  return sortByDateThenLanguage(
    allMovies
      .filter(m => m._bucket === "upcoming")  // Section boundary: only upcoming movies
      .filter(m => isDataComplete(m))  // Data completeness filter
      .filter(m => matchesIndustry(m, activeIndustry))  // Navigation filter
      .filter(m => matchesQuery(m, norm(activeQuery))),  // Search filter
    "asc"
  ).slice(0, 50);
}

function getNewFiltered() {
  return sortByDateThenLanguage(
    allMovies
      .filter(m => m._bucket === "new")  // Section boundary: only new releases
      .filter(m => isDataComplete(m))  // Data completeness filter
      .filter(m => matchesIndustry(m, activeIndustry))  // Navigation filter
      .filter(m => matchesQuery(m, norm(activeQuery))),  // Search filter
    "desc"
  ).slice(0, 50);
  console.log(new Date().toString());
  console.log("new/upcoming/catalog", getNewFiltered().length, getUpcomingFiltered().length, getCatalogFiltered().length);

}

function getCatalogFiltered() {
  return sortByDateThenLanguage(
    allMovies
      .filter(m => m._bucket === "catalog")  // Section boundary: only catalog items
      .filter(m => isDataComplete(m))  // Data completeness filter
      .filter(m => matchesIndustry(m, activeIndustry))  // Navigation filter
      .filter(m => matchesQuery(m, norm(activeQuery))),  // Search filter
    "desc"
  ).slice(0, 50);
}

function getBestFiltered() {
  const today = startOfToday();
  return sortByDateThenLanguage(
    bestIndia  // Section boundary: only Best Rated dataset
      .filter(m => isDataComplete(m))  // Data completeness filter
      .filter(m => matchesIndustry(m, activeIndustry))  // Navigation filter
      .filter(m => matchesQuery(m, norm(activeQuery)))  // Search filter
      .filter(m => {
        const releaseTime = parseReleaseDate(m.releaseDate);
        return !isNaN(releaseTime) && releaseTime <= today;  // Exclude future releases
      }),
    "desc"
  ).slice(0, 50);
}

function getRecentMergedFiltered() {
  const filtered = allMovies
    .filter(m => isDataComplete(m))
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
  const list = getBestFiltered();  // Filtered within Best Rated section only
  const totalCarouselPages = Math.ceil(list.length / cardsPerPage);
  
  if (bestCarouselPage >= totalCarouselPages) {
    bestCarouselPage = Math.max(0, totalCarouselPages - 1);
  }

  if (bestCount) {
    bestCount.textContent = list.length ? `${list.length} titles` : "";
  }

  if (!list.length) {
    bestCarousel.innerHTML = `<div class="muted">No Best Rated match your filters.</div>`;
    bestDots.innerHTML = "";
    bestPrev.style.display = "none";
    bestNext.style.display = "none";
    bestPagination.innerHTML = "";
    return;
  }

  // Render carousel cards
  bestCarousel.innerHTML = list.map(m => cardHtml(m, true)).join("");

  // Render dots
  bestDots.innerHTML = "";
  for (let i = 0; i < totalCarouselPages; i++) {
    const dot = document.createElement("button");
    dot.className = `carousel-dot ${i === bestCarouselPage ? "active" : ""}`;
    dot.onclick = () => {
      bestCarouselPage = i;
      scrollBestCarousel();
    };
    bestDots.appendChild(dot);
  }

  // Show/hide arrows
  bestPrev.style.display = totalCarouselPages > 1 ? "flex" : "none";
  bestNext.style.display = totalCarouselPages > 1 ? "flex" : "none";

  // Pagination for load more (show page numbers below dots)
  bestPagination.innerHTML = "";
  const totalPages = Math.max(1, Math.ceil(list.length / bestPageSize));
  if (totalPages > 1) {
    for (let p = 1; p <= totalPages; p++) {
      const btn = document.createElement("button");
      btn.textContent = p;
      if (p === bestPage) btn.classList.add("active");
      btn.onclick = () => { bestPage = p; renderAll(); };
      bestPagination.appendChild(btn);
    }
  }

  scrollBestCarousel();
}

function scrollBestCarousel() {
  const cards = bestCarousel.querySelectorAll(".card");
  if (!cards.length) return;

  const cardWidth = cards[0].offsetWidth;
  const gap = 12;
  const scrollAmount = (cardWidth + gap) * cardsPerPage;
  const scrollPosition = bestCarouselPage * scrollAmount;

  bestCarousel.scrollTo({
    left: scrollPosition,
    behavior: "smooth"
  });

  // Update dots
  document.querySelectorAll("#bestDots .carousel-dot").forEach((dot, i) => {
    dot.classList.toggle("active", i === bestCarouselPage);
  });
}

function renderUpcoming() {
  const list = getUpcomingFiltered();  // Show all upcoming movies
  
  if (upcomingCount) {
    upcomingCount.textContent = list.length > 0 ? `${list.length} movies` : "";
  }
  
  if (!list.length) {
    upcomingCarousel.innerHTML = `<div class="muted">No upcoming matches.</div>`;
    upcomingDots.innerHTML = "";
    upcomingPrev.style.display = "none";
    upcomingNext.style.display = "none";
    return;
  }
  
  // Render carousel cards
  upcomingCarousel.innerHTML = list.map(m => cardHtml(m, false)).join("");
  
  // Reset carousel page if needed
  const totalPages = Math.ceil(list.length / cardsPerPage);
  if (upcomingCarouselPage >= totalPages) {
    upcomingCarouselPage = 0;
  }
  
  // Render dots
  upcomingDots.innerHTML = "";
  for (let i = 0; i < totalPages; i++) {
    const dot = document.createElement("button");
    dot.className = `carousel-dot ${i === upcomingCarouselPage ? "active" : ""}`;
    dot.onclick = () => {
      upcomingCarouselPage = i;
      scrollUpcomingCarousel();
    };
    upcomingDots.appendChild(dot);
  }
  
  // Show/hide arrows
  upcomingPrev.style.display = totalPages > 1 ? "flex" : "none";
  upcomingNext.style.display = totalPages > 1 ? "flex" : "none";
  
  scrollUpcomingCarousel();
}

function scrollUpcomingCarousel() {
  const cards = upcomingCarousel.querySelectorAll(".card");
  if (!cards.length) return;
  
  const cardWidth = cards[0].offsetWidth;
  const gap = 12;
  const scrollAmount = (cardWidth + gap) * cardsPerPage;
  const scrollPosition = upcomingCarouselPage * scrollAmount;
  
  upcomingCarousel.scrollTo({
    left: scrollPosition,
    behavior: "smooth"
  });
  
  // Update dots
  document.querySelectorAll("#upcomingDots .carousel-dot").forEach((dot, i) => {
    dot.classList.toggle("active", i === upcomingCarouselPage);
  });
}

function setupUpcomingCarousel() {
  upcomingPrev.onclick = () => {
    const totalPages = upcomingDots.querySelectorAll(".carousel-dot").length;
    upcomingCarouselPage = Math.max(0, upcomingCarouselPage - 1);
    scrollUpcomingCarousel();
  };
  
  upcomingNext.onclick = () => {
    const totalPages = upcomingDots.querySelectorAll(".carousel-dot").length;
    upcomingCarouselPage = Math.min(totalPages - 1, upcomingCarouselPage + 1);
    scrollUpcomingCarousel();
  };
}

function renderNew() {
  const list = getNewFiltered();
  const totalCarouselPages = Math.ceil(list.length / cardsPerPage);
  
  if (newCarouselPage >= totalCarouselPages) {
    newCarouselPage = Math.max(0, totalCarouselPages - 1);
  }

  newCount.textContent = list.length ? `${list.length} titles` : "";

  if (!list.length) {
    newCarousel.innerHTML = `<div class="muted">No new releases match your filters.</div>`;
    newDots.innerHTML = "";
    newPrev.style.display = "none";
    newNext.style.display = "none";
    newPagination.innerHTML = "";
    return;
  }

  // Render carousel cards
  newCarousel.innerHTML = list.map(m => cardHtml(m, false)).join("");

  // Render dots
  newDots.innerHTML = "";
  for (let i = 0; i < totalCarouselPages; i++) {
    const dot = document.createElement("button");
    dot.className = `carousel-dot ${i === newCarouselPage ? "active" : ""}`;
    dot.onclick = () => {
      newCarouselPage = i;
      scrollNewCarousel();
    };
    newDots.appendChild(dot);
  }

  // Show/hide arrows
  newPrev.style.display = totalCarouselPages > 1 ? "flex" : "none";
  newNext.style.display = totalCarouselPages > 1 ? "flex" : "none";

  // Pagination for load more (show page numbers below dots)
  newPagination.innerHTML = "";
  const totalPages = Math.max(1, Math.ceil(list.length / newPageSize));
  if (totalPages > 1) {
    for (let p = 1; p <= totalPages; p++) {
      const btn = document.createElement("button");
      btn.textContent = p;
      if (p === newPage) btn.classList.add("active");
      btn.onclick = () => { newPage = p; renderAll(); };
      newPagination.appendChild(btn);
    }
  }

  scrollNewCarousel();
}

function scrollNewCarousel() {
  const cards = newCarousel.querySelectorAll(".card");
  if (!cards.length) return;

  const cardWidth = cards[0].offsetWidth;
  const gap = 12;
  const scrollAmount = (cardWidth + gap) * cardsPerPage;
  const scrollPosition = newCarouselPage * scrollAmount;

  newCarousel.scrollTo({
    left: scrollPosition,
    behavior: "smooth"
  });

  // Update dots
  document.querySelectorAll("#newDots .carousel-dot").forEach((dot, i) => {
    dot.classList.toggle("active", i === newCarouselPage);
  });
}

function renderCatalog() {
  if (!catalogGrid || !catalogPagination) return;

  const list = getCatalogFiltered();  // Filtered within Catalog section only
  const totalPages = Math.max(1, Math.ceil(list.length / catalogPageSize));
  if (catalogPage > totalPages) catalogPage = totalPages;

  const start = (catalogPage - 1) * catalogPageSize;
  const pageItems = list.slice(start, start + catalogPageSize);

  if (catalogCount) {
    catalogCount.textContent = list.length ? `${list.length} titles` : "";
  }

  // Shows "No results" WITHIN this section, doesn't move user elsewhere
  catalogGrid.innerHTML = pageItems.length
    ? pageItems.map(m => cardHtml(m, false)).join("")
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
  if (!recentList || !recentMoreBtn) return;
  
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


function setupUpcomingCarousel() {
  upcomingPrev.onclick = () => {
    const totalPages = upcomingDots.querySelectorAll(".carousel-dot").length;
    upcomingCarouselPage = Math.max(0, upcomingCarouselPage - 1);
    scrollUpcomingCarousel();
  };
  
  upcomingNext.onclick = () => {
    const totalPages = upcomingDots.querySelectorAll(".carousel-dot").length;
    upcomingCarouselPage = Math.min(totalPages - 1, upcomingCarouselPage + 1);
    scrollUpcomingCarousel();
  };
}

function setupNewCarousel() {
  newPrev.onclick = () => {
    const totalPages = newDots.querySelectorAll(".carousel-dot").length;
    newCarouselPage = Math.max(0, newCarouselPage - 1);
    scrollNewCarousel();
  };
  
  newNext.onclick = () => {
    const totalPages = newDots.querySelectorAll(".carousel-dot").length;
    newCarouselPage = Math.min(totalPages - 1, newCarouselPage + 1);
    scrollNewCarousel();
  };
}

function setupBestCarousel() {
  bestPrev.onclick = () => {
    const totalPages = bestDots.querySelectorAll(".carousel-dot").length;
    bestCarouselPage = Math.max(0, bestCarouselPage - 1);
    scrollBestCarousel();
  };
  
  bestNext.onclick = () => {
    const totalPages = bestDots.querySelectorAll(".carousel-dot").length;
    bestCarouselPage = Math.min(totalPages - 1, bestCarouselPage + 1);
    scrollBestCarousel();
  };
}

// Tabs - changes navigation state only, preserves search state
tabs.forEach(t => {
  t.addEventListener("click", () => {
    tabs.forEach(x => x.classList.remove("active"));
    t.classList.add("active");

    // Update navigation state (tab/category)
    activeIndustry = t.dataset.industry;
    
    // Reset pagination for new tab
    bestPage = 1;
    newPage = 1;
    catalogPage = 1;
    
    // Clear saved pagination state (different tab context)
    savedPagination = null;
    
    // activeQuery is NOT modified - search persists across tab changes
    // Results will be filtered by BOTH activeIndustry AND activeQuery
    renderAll();
  });
});

// Search - changes search state only, preserves navigation state
function runSearch() {
  const newQuery = searchInput.value.trim();
  const previousQuery = activeQuery;
  
  // If starting a new search (was empty, now has query), save current pagination
  if (!previousQuery && newQuery) {
    savedPagination = {
      bestPage,
      newPage,
      catalogPage
    };
  }
  
  // If clearing search (had query, now empty), restore previous pagination
  if (previousQuery && !newQuery && savedPagination) {
    bestPage = savedPagination.bestPage;
    newPage = savedPagination.newPage;
    catalogPage = savedPagination.catalogPage;
    savedPagination = null;
  } 
  // If entering/modifying search query, reset to page 1
  else if (newQuery) {
    bestPage = 1;
    newPage = 1;
    catalogPage = 1;
  }
  
  // Update search state (query filter)
  activeQuery = newQuery;
  
  // activeIndustry is NOT modified - navigation (tab selection) persists
  // Results will be filtered by BOTH activeIndustry AND activeQuery
  // User stays on the same tab, sees filtered results within that tab
  // Pagination context remains section-scoped (bestPage for Best, newPage for New, etc.)
  renderAll();
}
searchBtn.addEventListener("click", runSearch);
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") runSearch();
});

// Recent load more
if (recentMoreBtn) {
  recentMoreBtn.addEventListener("click", () => renderRecent(false));
}

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

    setupUpcomingCarousel();
    setupNewCarousel();
    setupBestCarousel();
    renderAll();
  } catch (err) {
    console.error(err);
    showNotice(err.message || "Failed to load data files.");
    upcomingCarousel.innerHTML = "";
    newCarousel.innerHTML = "";
    if (catalogGrid) catalogGrid.innerHTML = "";
    bestCarousel.innerHTML = "";
    recentList.innerHTML = "";
  }
})();
