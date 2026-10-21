// Shared page chrome and helpers. Every page sets <body data-root="." or ".."> and data-page.
const ROOT = document.body.dataset.root || ".";
const PAGES = [
  ["", "Overview"], ["readiness/", "Readiness"], ["opportunities/", "Use cases"],
  ["business-case/", "Business case"], ["roadmap/", "Roadmap"], ["pilot/", "Pilot"], ["deck/", "Board deck"],
];
const REPO = "https://github.com/phlppgdfry/enterprise-ai-transformation";

function chrome() {
  const here = document.body.dataset.page || "";
  const header = document.createElement("header");
  header.className = "top";
  header.innerHTML = `<div class="wrap">
    <a class="brand" href="${ROOT}/">Wendelkaai <span>· AI transformation</span></a>
    <nav class="links">${PAGES.map(([p, n]) =>
      `<a href="${ROOT}/${p}" class="${p === here ? "on" : ""}">${n}</a>`).join("")}</nav>
    <button class="theme" type="button" aria-label="Toggle colour theme">◐</button></div>`;
  document.body.prepend(header);
  const footer = document.createElement("footer");
  footer.innerHTML = `<div class="wrap"><span>Portfolio case. Wendelkaai Logistics and every person and figure in it are fictional; regulations, standards and methods are real.</span>
    <a href="${REPO}">Source, method and tests on GitHub</a></div>`;
  document.body.append(footer);
  header.querySelector(".theme").addEventListener("click", () => {
    const dark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch (e) { /* storage blocked: theme lasts for this page only */ }
  });
}
try { const t = localStorage.getItem("theme"); if (t) document.documentElement.dataset.theme = t; } catch (e) { /* ignore */ }
chrome();

async function loadJSON(name) {
  const res = await fetch(`${ROOT}/data/${name}.json`);
  if (!res.ok) throw new Error(`could not load ${name}.json`);
  return res.json();
}

const fmt = {
  eur: (x) => (x < 0 ? "-€" : "€") + Math.abs(Math.round(x)).toLocaleString("en-US"),
  keur: (x) => (x < 0 ? "-€" : "€") + Math.round(Math.abs(x) / 1000).toLocaleString("en-US") + "k",
  pct: (x, d = 1) => (100 * x).toFixed(d) + "%",
  months: (m) => (m == null ? "not within 3 years" : `${Math.round(m)} months`),
};

// One tooltip for the page. Charts call tip.show(evt, html) / tip.hide().
const tip = (() => {
  const el = document.createElement("div");
  el.className = "tip";
  document.body.append(el);
  return {
    show(evt, html) {
      el.innerHTML = html;
      el.style.opacity = 1;
      const pad = 14, w = el.offsetWidth, h = el.offsetHeight;
      let x = evt.clientX + pad, y = evt.clientY + pad;
      if (x + w > innerWidth - 8) x = evt.clientX - w - pad;
      if (y + h > innerHeight - 8) y = evt.clientY - h - pad;
      el.style.left = x + "px"; el.style.top = y + "px";
    },
    hide() { el.style.opacity = 0; },
  };
})();

function svg(tag, attrs = {}, parent) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  if (parent) parent.append(el);
  return el;
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// Guided tour: steps = [{sel, text}]. Starts when the URL has ?tour.
function tour(steps) {
  if (!new URLSearchParams(location.search).has("tour")) return;
  let i = 0, box = null, prev = null;
  const show = () => {
    prev?.classList.remove("tour-hl");
    const s = steps[i], target = document.querySelector(s.sel);
    s.before?.();
    box?.remove();
    box = document.createElement("div");
    box.className = "tour";
    box.innerHTML = `<div class="step">${i + 1} / ${steps.length}</div><div>${s.text}</div>
      <div class="row"><button class="btn" data-a="skip">Close</button>
      <button class="btn primary" data-a="next">${i === steps.length - 1 ? "Done" : "Next"}</button></div>`;
    document.body.append(box);
    if (target) {
      target.classList.add("tour-hl");
      target.scrollIntoView({ behavior: "smooth", block: "center" });
      prev = target;
      setTimeout(() => {
        const r = target.getBoundingClientRect();
        const top = r.bottom + 12 + box.offsetHeight < innerHeight ? r.bottom + 12 : Math.max(12, r.top - box.offsetHeight - 12);
        box.style.top = top + "px";
        box.style.left = Math.min(innerWidth - box.offsetWidth - 12, Math.max(12, r.left)) + "px";
      }, 350);
    }
    box.addEventListener("click", (e) => {
      const a = e.target.dataset.a;
      if (a === "next" && i < steps.length - 1) { i++; show(); }
      else if (a) { box.remove(); prev?.classList.remove("tour-hl"); }
    });
  };
  setTimeout(show, 600);
}
