// Browser twin of engine/business_case.py and engine/portfolio.py.
// scripts/check_js.js runs these against the Python results in CI, so the
// sliders on the site and the numbers in the documents cannot drift apart.

function computeCase(v, horizon = 3, docDeskFte = 11) {
  const review = Math.max(0, 1 - v.stp_rate - v.manual_rate);
  const minutesAfter = v.stp_rate * v.stp_minutes + review * v.review_minutes + v.manual_rate * v.manual_minutes;
  const saved = v.manual_minutes - minutesAfter;
  const errorAfter = v.pilot_escape_rate + review * v.human_error_rate * v.review_error_factor + v.manual_rate * v.human_error_rate;
  const modelCostDoc = (v.tokens_in * v.price_in_usd_per_mtok + v.tokens_out * v.price_out_usd_per_mtok) / 1e6 * v.eur_per_usd;
  const years = [];
  for (let t = 1; t <= horizon; t++) {
    const volume = v.documents_per_month * 12 * (1 + v.volume_growth) ** (t - 1);
    const ramp = t === 1 ? v.ramp_year1 : 1;
    const hours = volume * saved / 60 * ramp;
    const fteFreed = hours / v.fte_hours;
    const hiresAvoided = docDeskFte * ((1 + v.volume_growth) ** t - 1) + v.attrition_fte * t;
    const cashFte = Math.min(fteFreed, hiresAvoided);
    const errorsAvoided = volume * (v.human_error_rate - errorAfter) * ramp;
    const modelCost = volume * modelCostDoc;
    years.push({
      year: t, documents: Math.round(volume), hours_freed: Math.round(hours), fte_freed: fteFreed, cash_fte: cashFte,
      errors_avoided: Math.round(errorsAvoided), capacity_value: Math.round(hours * v.hourly_cost),
      cash_labour_value: Math.round(cashFte * v.fte_cost), error_value: Math.round(errorsAvoided * v.error_cost),
      model_cost: Math.round(modelCost), run_cost: Math.round(v.run_cost + modelCost),
    });
  }
  const out = { review_rate: review, minutes_after: minutesAfter, saved_minutes_per_document: saved,
    error_rate_after: errorAfter, model_cost_per_document_eur: modelCostDoc, one_off: v.one_off_cost, years };
  for (const [view, labour] of [["capacity", "capacity_value"], ["cash", "cash_labour_value"]]) {
    const nets = years.map((y) => y[labour] + y.error_value - y.run_cost);
    const npv = -v.one_off_cost + nets.reduce((s, n, i) => s + n / (1 + v.discount_rate) ** (i + 1), 0);
    out[view] = { net_per_year: nets, npv: Math.round(npv),
      roi: (nets.reduce((a, b) => a + b, 0) - v.one_off_cost) / v.one_off_cost,
      payback_months: payback(nets, v.one_off_cost) };
  }
  return out;
}

function payback(nets, oneOff) {
  let cum = 0;
  for (let i = 0; i < nets.length; i++) {
    const monthly = nets[i] / 12;
    if (monthly <= 0) continue;
    if (cum + nets[i] >= oneOff) return Math.round((i * 12 + (oneOff - cum) / monthly) * 10) / 10;
    cum += nets[i];
  }
  return null;
}

function rankPortfolio(portfolio, weights) {
  const crit = portfolio.criteria, scale = portfolio.value_scale_eur;
  weights = weights || Object.fromEntries(Object.entries(crit).map(([g, s]) => [g, s.weight]));
  const wsum = Object.values(weights).reduce((a, b) => a + b, 0);
  const rows = portfolio.use_cases.map((uc) => {
    const s = { ...uc.scores, annual_value: 1 + 4 * Math.min(uc.annual_value_eur, scale) / scale };
    const parts = {};
    for (const [g, spec] of Object.entries(crit)) parts[g] = Object.entries(spec.sub).reduce((a, [k, w]) => a + s[k] * w, 0);
    const total = Object.keys(parts).reduce((a, g) => a + parts[g] * weights[g], 0) / wsum;
    return { id: uc.id, name: uc.name, value: parts.value, feasibility: parts.feasibility, risk: parts.risk,
      score: total, parked: uc.scores.regulatory === 1 };
  });
  const ranked = rows.filter((r) => !r.parked).sort((a, b) => b.score - a.score);
  ranked.forEach((r, i) => { r.rank = i + 1; });
  return rows.sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99));
}

if (typeof module !== "undefined") module.exports = { computeCase, rankPortfolio, payback };
