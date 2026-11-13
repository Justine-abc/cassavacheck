// Shared by every page (loaded after i18n.js): the header and bottom navigation, and small formatting helpers. No diagnosis logic lives here.
const CLASS_LONG_NAMES = {
  CBB: "Cassava bacterial blight", CBSD: "Cassava brown streak disease", CGM: "Cassava green mite",
  CMD: "Cassava mosaic disease", healthy: "Healthy leaf",
};
// Short names for the follow-up questions, so the officer sees "White flies: Yes" rather than a bare "Yes".
const QUESTION_SHORT_NAMES = { leaf_age: "Leaf", whiteflies: "White flies", other_signs: "Other signs", cuttings_source: "Cuttings from" };
const SEASONS = { A: "Sep – Feb", B: "Mar – Jun", C: "Jul – Aug" };

// Disease name in the chosen language. In Kinyarwanda the English code stays beside the name, so an officer and a
// farmer can always match it to the fact sheet.
function diseaseName(code) {
  return LANG === "rw" ? `${T(CLASS_LONG_NAMES[code])}${code === "healthy" ? "" : ` (${code})`}` : CLASS_LONG_NAMES[code];
}

// One labelled example photo per condition, so a farmer can compare their leaf with a known case. Shown only;
// nothing is tuned on them. CBB, CGM and CMD come from the CCMT set from Ghana, which has no brown streak class;
// the CBSD photo is from Wikimedia Commons. Sources and licences: README, "Added after the report was submitted".
const CCMT_CREDIT = "Example photo: CCMT dataset, Ghana (Mensah et al., 2023), CC BY 4.0";
const EXAMPLE_PHOTOS = {
  CBB: { src: "/static/examples/CBB.jpg", credit: CCMT_CREDIT },
  CBSD: { src: "/static/examples/CBSD.jpg", credit: "Example photo: P. Abidrabo, Kasese, Uganda, 2013, Wikimedia Commons, CC BY-SA 3.0, cropped" },
  CGM: { src: "/static/examples/CGM.jpg", credit: CCMT_CREDIT },
  CMD: { src: "/static/examples/CMD.jpg", credit: CCMT_CREDIT },
};

function percent(value) { return `${Math.round(value * 100)}%`; }

// Staggered entrance for the direct children of a container (styles in app.css).
function reveal(container) {
  container.classList.add("reveal");
  [...container.children].forEach((child, index) => child.style.setProperty("--i", index));
}

// Bars are drawn empty with data-width, then filled on the next frame so the width change animates.
// Bars inside a closed <details> wait until it is opened.
function fillBars(root = document) {
  requestAnimationFrame(() => requestAnimationFrame(() =>
    root.querySelectorAll(".bar-fill[data-width]").forEach((bar) => {
      if (!bar.closest("details:not([open])")) bar.style.width = bar.dataset.width;
    })));
}

// Confidence against the decision line: the core idea of the app in one picture.
function confidenceMeter(confidence, threshold) {
  const answered = confidence >= threshold;
  const line = Math.round(threshold * 100);
  return `
    <div class="flex flex-col gap-1" aria-label="${T("Confidence")} ${percent(confidence)}, ${T("Decision line")} ${percent(threshold)}">
      <div class="relative h-4 bg-surface-container-high rounded-full">
        <div class="bar-fill h-4 rounded-full ${answered ? "bg-primary" : "bg-secondary"}" data-width="${Math.max(1, confidence * 100)}%"></div>
        <div class="absolute -top-1.5 -bottom-1.5 w-0.5 bg-on-surface" style="left:${line}%"></div>
      </div>
      <div class="relative h-9 font-label-sm text-label-sm text-on-surface-variant">
        <span class="absolute left-0 top-0.5">0%</span>
        <span class="absolute top-0.5 -translate-x-1/2 text-center leading-tight text-on-surface" style="left:${line}%">${T("Decision line")}<br/>${percent(threshold)}</span>
        <span class="absolute right-0 top-0.5">100%</span>
      </div>
      <p class="font-body-sm text-body-sm text-on-surface-variant">${answered
        ? T("Above the line, CassaCheck names a condition.")
        : T("Below the line, CassaCheck does not guess: it says not sure.")}</p>
    </div>`;
}

function escapeHtml(text) {
  return String(text ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function renderHeader(title, { back = false, hideLanguageSwitch = false } = {}) {
  const backButton = back
    ? `<a href="/" class="w-11 h-11 flex items-center justify-center text-primary -ml-2 rounded-full active:bg-surface-container" aria-label="${T("Back")}"><span class="material-symbols-outlined text-[24px]">arrow_back</span></a>`
    : "";
  document.getElementById("app-header").innerHTML = `
    <header class="fixed top-0 w-full z-50 bg-surface/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
      <div class="h-16 px-margin-mobile lg:px-8 max-w-6xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-space-sm">
          ${backButton}
          <span class="w-9 h-9 rounded-lg bg-primary flex items-center justify-center"><span class="material-symbols-outlined text-on-primary text-[20px]">eco</span></span>
          <div class="flex flex-col leading-tight">
            <span class="font-headline-sm text-headline-sm text-primary">CassaCheck</span>
            <span class="font-label-sm text-label-sm text-on-surface-variant">${escapeHtml(title)}</span>
          </div>
        </div>
        <div class="flex items-center gap-1 lg:gap-3">
          <nav id="top-nav" class="hidden lg:flex items-center gap-1" aria-label="${T("Main menu")}"></nav>
          ${hideLanguageSwitch ? "" : `
          <a href="/officer" class="press h-10 px-2 lg:px-3 rounded-lg flex items-center gap-1 text-on-surface-variant hover:bg-surface-container-high font-label-md text-label-md" aria-label="${T("Extension officer sign-in")}">
            <span class="material-symbols-outlined text-[20px]">badge</span><span class="hidden lg:inline">${T("Officer sign-in")}</span></a>
          ${languageSwitch()}`}
        </div>
      </div>
    </header>`;
  wireLanguageSwitch();
}

// The farmer's four places. On a phone they sit in a bar at the bottom, where the thumb reaches; on a laptop or a
// projector they move into the header. The officer view is not one of them: officers use the sign-in link in the header.
const NAV_ITEMS = [
  { href: "/", icon: "photo_camera", label: "Diagnose", key: "diagnose" },
  { href: "/my-case", icon: "inbox", label: "My case", key: "my-case" },
  { href: "/how-it-works", icon: "menu_book", label: "How it works", key: "how" },
  { href: "/diseases", icon: "coronavirus", label: "Diseases", key: "diseases" },
];

function renderBottomNav(active) {
  const items = active === "officer" ? [...NAV_ITEMS, { href: "/officer", icon: "assignment", label: "Officer view", key: "officer" }] : NAV_ITEMS;
  const fill = (key) => `style="font-variation-settings:'FILL' ${active === key ? 1 : 0}"`;
  document.getElementById("app-nav").innerHTML = `
    <nav class="lg:hidden fixed bottom-0 w-full z-50 bg-surface-container-lowest border-t border-outline-variant/40" aria-label="${T("Main menu")}">
      <div class="h-16 max-w-3xl mx-auto flex">
        ${items.map((item) => `
          <a href="${item.href}" class="flex flex-col items-center justify-center gap-0.5 flex-1 h-full ${active === item.key ? "text-primary" : "text-on-surface-variant"}"${active === item.key ? ' aria-current="page"' : ""}>
            <span class="material-symbols-outlined text-[22px]" ${fill(item.key)}>${item.icon}</span>
            <span class="font-label-sm text-label-sm">${item.key === "officer" ? item.label : T(item.label)}</span>
          </a>`).join("")}
      </div>
    </nav>`;
  const top = document.getElementById("top-nav");
  if (top) top.innerHTML = items.map((item) => `
    <a href="${item.href}" class="h-10 px-3 rounded-lg flex items-center gap-1.5 font-label-lg text-label-lg ${active === item.key ? "bg-primary-fixed text-on-primary-fixed" : "text-on-surface-variant hover:bg-surface-container-high"}"${active === item.key ? ' aria-current="page"' : ""}>
      <span class="material-symbols-outlined text-[20px]" ${fill(item.key)}>${item.icon}</span>${item.key === "officer" ? item.label : T(item.label)}</a>`).join("");
}

// Cases this phone has sent, so "My case" can list them without retyping. Kept only in this browser; the server
// still checks the code on every request. Storage can be blocked (private mode), so every access is guarded.
const CASES_KEY = "cassacheck-my-cases";
function rememberedCases() {
  try { return JSON.parse(localStorage.getItem(CASES_KEY) || "[]"); } catch { return []; }
}
function rememberCase(caseNumber, checkCode) {
  try {
    const cases = rememberedCases().filter((c) => c.case_number !== caseNumber);
    cases.unshift({ case_number: caseNumber, check_code: checkCode, sent_at: new Date().toISOString() });
    localStorage.setItem(CASES_KEY, JSON.stringify(cases.slice(0, 10)));
  } catch { /* the farmer still has the number and code on screen */ }
}
function forgetCase(caseNumber) {
  try { localStorage.setItem(CASES_KEY, JSON.stringify(rememberedCases().filter((c) => c.case_number !== caseNumber))); } catch {}
}
