// CI check: the browser model (site/assets/model.js) reproduces the Python model
// (engine/) on the published data. Run: node scripts/check_js.js
const fs = require("fs");
const path = require("path");
const { computeCase, rankPortfolio } = require("../site/assets/model.js");

const root = path.join(__dirname, "..");
const model = JSON.parse(fs.readFileSync(path.join(root, "site/data/model.json"), "utf8"));
const bc = model.business_case;
const base = Object.fromEntries(Object.entries(bc.values).map(([k, v]) => [k, v.base]));
const js = computeCase(base, 3, bc.doc_desk_fte);

const failures = [];
const near = (a, b, tol, what) => { if (Math.abs(a - b) > tol) failures.push(`${what}: js ${a} vs python ${b}`); };
for (const view of ["cash", "capacity"]) {
  near(js[view].npv, bc.base[view].npv, 2, `${view} NPV`);
  near(js[view].payback_months ?? -1, bc.base[view].payback_months ?? -1, 0.11, `${view} payback`);
  js[view].net_per_year.forEach((n, i) => near(n, bc.base[view].net_per_year[i], 2, `${view} net year ${i + 1}`));
}
const ranked = rankPortfolio(model.portfolio).map((r) => r.id);
const expected = model.portfolio.ranking.map((r) => r.id);
if (ranked.join() !== expected.join()) failures.push(`ranking: js ${ranked} vs python ${expected}`);

if (failures.length) {
  console.error("Browser model drifted from the Python model:\n  " + failures.join("\n  "));
  process.exit(1);
}
console.log(`browser model matches Python: NPV cash ${js.cash.npv}, ranking ${ranked.slice(0, 3).join(", ")}...`);
