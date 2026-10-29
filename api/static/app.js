// Shared by every page: the header and bottom navigation, and small formatting helpers. No diagnosis logic lives here.
const CLASS_LONG_NAMES = {
  CBB: "Cassava bacterial blight", CBSD: "Cassava brown streak disease", CGM: "Cassava green mite",
  CMD: "Cassava mosaic disease", healthy: "Healthy leaf",
};
// Short names for the follow-up questions, so the officer sees "White flies: Yes" rather than a bare "Yes".
const QUESTION_SHORT_NAMES = { leaf_age: "Leaf", whiteflies: "White flies", other_signs: "Other signs", cuttings_source: "Cuttings from" };
const SEASONS = { A: "Sep – Feb", B: "Mar – Jun", C: "Jul – Aug" };

function percent(value) { return `${Math.round(value * 100)}%`; }

function escapeHtml(text) {
  return String(text ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function renderHeader(title, { back = false } = {}) {
  const backButton = back
    ? `<a href="/" class="w-11 h-11 flex items-center justify-center text-primary -ml-2 rounded-full active:bg-surface-container" aria-label="Back"><span class="material-symbols-outlined text-[24px]">arrow_back</span></a>`
    : "";
  document.getElementById("app-header").innerHTML = `
    <header class="fixed top-0 w-full z-50 bg-surface/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
      <div class="h-16 px-margin-mobile max-w-3xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-space-sm">
          ${backButton}
          <span class="w-9 h-9 rounded-lg bg-primary flex items-center justify-center"><span class="material-symbols-outlined text-on-primary text-[20px]">eco</span></span>
          <div class="flex flex-col leading-tight">
            <span class="font-headline-sm text-headline-sm text-primary">CassaCheck</span>
            <span class="font-label-sm text-label-sm text-on-surface-variant">${escapeHtml(title)}</span>
          </div>
        </div>
      </div>
    </header>`;
}

function renderBottomNav(active) {
  const item = (href, icon, label, key) => `
    <a href="${href}" class="flex flex-col items-center justify-center gap-0.5 flex-1 h-full ${active === key ? "text-primary" : "text-on-surface-variant"}">
      <span class="material-symbols-outlined text-[22px]" style="font-variation-settings:'FILL' ${active === key ? 1 : 0}">${icon}</span>
      <span class="font-label-sm text-label-sm">${label}</span>
    </a>`;
  document.getElementById("app-nav").innerHTML = `
    <nav class="fixed bottom-0 w-full z-50 bg-surface-container-lowest border-t border-outline-variant/40">
      <div class="h-16 max-w-3xl mx-auto flex">
        ${item("/", "photo_camera", "Diagnose", "diagnose")}
        ${item("/how-it-works", "menu_book", "How it works", "how")}
        ${item("/officer", "assignment", "Officer view", "officer")}
      </div>
    </nav>`;
}
