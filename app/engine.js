/* MMA predictor engine: a port of mma_predictor/{features,methods,styles}.py
 * and adjustments.apply. Keep in sync; tests/test_engine_parity.py checks it.
 * Works in the browser (window.MMAEngine) and in Node (module.exports). */
(function (root) {
  "use strict";
  const BUCKETS = ["KO/TKO", "SUB", "DEC"];
  const INT_FIELDS = new Set(["recent_ko_losses", "streak", "layoff_days"]);

  const clip = (x, lo = -3, hi = 3) => Math.max(lo, Math.min(hi, x));
  const sigmoid = (z) => (z >= 0 ? 1 / (1 + Math.exp(-z)) : Math.exp(z) / (1 + Math.exp(z)));
  const totalFights = (s) => s.wins + s.losses + s.prior_wins + s.prior_losses;

  function agePenalty(age) {
    if (age === null || age === undefined) return 0;
    let p = Math.pow(Math.max(0, age - 32), 1.5) / 10;
    if (age < 24) p += (24 - age) * 0.05;
    return p;
  }
  function layoffPenalty(days) {
    if (days === null || days === undefined) return 0;
    return Math.min(2.5, Math.max(0, days - 400) / 365);
  }
  function makeEngine(data) {
    const P = data.priors;
    const koShare = P.method_share["KO/TKO"];
    const subShare = P.method_share["SUB"];
    const landsOn = (a, d) => a.slpm * ((1 - d.str_def) / (1 - P.str_def));
    const takedownsOn = (a, d) => a.td_per15 * ((1 - d.td_def) / (1 - P.td_def));
    const chin = (s) => (s.ko_loss_rate / (0.5 * koShare)) * (1 + (0.5 * s.kd_absorbed_per15) / P.kd_per15) / 1.5;

    function stance(a, b) {
      const sa = (a.stance || "").toLowerCase(), sb = (b.stance || "").toLowerCase();
      if (sa === "southpaw" && sb === "orthodox") return 1;
      if (sb === "southpaw" && sa === "orthodox") return -1;
      return 0;
    }

    function features(a, b, rounds) {
      const five = rounds >= 5;
      const reach = a.reach_cm != null && b.reach_cm != null ? (a.reach_cm - b.reach_cm) / 10 : 0;
      const subA = a.sub_per15 * (b.sub_loss_rate / (0.5 * subShare));
      const subB = b.sub_per15 * (a.sub_loss_rate / (0.5 * subShare));
      return {
        elo: clip((a.elo - b.elo) / 400),
        striking_exchange: clip((landsOn(a, b) - landsOn(b, a)) / 3),
        striking_defense: clip((a.str_def - b.str_def) * 10),
        power_vs_chin: clip(2 * (a.kd_per15 * chin(b) - b.kd_per15 * chin(a))),
        wrestling_edge: clip((takedownsOn(a, b) - takedownsOn(b, a)) / 2),
        control: clip(((a.ctrl_share - a.ctrl_against_share) - (b.ctrl_share - b.ctrl_against_share)) * 3),
        submission_threat: clip((subA - subB) / 1.5),
        reach: clip(reach, -2, 2),
        age_curve: clip(agePenalty(b.age) - agePenalty(a.age)),
        experience: clip(Math.log1p(totalFights(a)) - Math.log1p(totalFights(b))),
        form: a.form - b.form,
        layoff: layoffPenalty(b.layoff_days) - layoffPenalty(a.layoff_days),
        chin_damage: b.recent_ko_losses - a.recent_ko_losses,
        cardio: (a.late_win_rate - b.late_win_rate) * (five ? 2 : 1),
        schedule_strength: clip((a.sos - b.sos) / 200),
        stance: stance(a, b),
      };
    }

    function damp(r) {
      return Math.sqrt(Math.max(0.5, Math.min(2, r)));
    }
    function methodDistribution(w, l, rounds) {
      const pop = P.method_share;
      const raw = {};
      for (const m of BUCKETS) raw[m] = (w.win_methods[m] * l.loss_methods[m]) / pop[m];
      raw["KO/TKO"] *= damp((w.kd_per15 / P.kd_per15) * chin(l));
      raw["SUB"] *= damp((w.sub_per15 / P.sub_per15) * (l.sub_loss_rate / (0.5 * subShare)));
      if (rounds >= 5) {
        raw["KO/TKO"] *= 1.15;
        raw["SUB"] *= 1.15;
        raw["DEC"] *= 0.85;
      }
      const t = raw["KO/TKO"] + raw["SUB"] + raw["DEC"];
      const out = {};
      for (const m of BUCKETS) out[m] = raw[m] / t;
      return out;
    }

    function classify(s) {
      const wrestling = s.td_per15 / P.td_per15 + s.ctrl_share / P.ctrl_share;
      const grappling = s.sub_per15 / P.sub_per15;
      const striking = s.slpm / P.slpm;
      const power = s.kd_per15 / P.kd_per15;
      const tags = [];
      if (wrestling >= 3) tags.push("wrestler");
      if (grappling >= 2) tags.push("submission grappler");
      if (striking >= 1.25) tags.push("volume striker");
      if (power >= 1.8) tags.push("power puncher");
      if (s.str_def >= P.str_def + 0.05 && s.sapm <= P.sapm * 0.8) tags.push("defensive/technical");
      if (s.td_def >= 0.78 && striking >= 1) tags.push("anti-wrestler");
      if (!tags.length) tags.push("well-rounded");
      return tags;
    }

    const pct = (x) => Math.round(x * 100) + "%";
    function oneWay(x, y, rounds) {
      const out = [];
      const tds = takedownsOn(x, y);
      if (x.td_per15 >= 2 && y.td_def <= 0.6)
        out.push(`Wrestling path: ${x.name} averages ${x.td_per15.toFixed(1)} TD/15 and ${y.name} defends only ${pct(y.td_def)}, which projects ~${tds.toFixed(1)} takedowns per 15 min.`);
      if (x.td_per15 >= 2 && y.td_def >= 0.8)
        out.push(`${y.name}'s ${pct(y.td_def)} takedown defence neutralises much of ${x.name}'s wrestling.`);
      if (x.kd_per15 >= 0.5 && (y.recent_ko_losses >= 1 || y.ko_loss_rate >= 0.25))
        out.push(`Power vs chin: ${x.name} scores ${x.kd_per15.toFixed(2)} knockdowns/15 and ${y.name} has ${y.recent_ko_losses} KO loss(es) in the last 3 (${pct(y.ko_loss_rate)} of bouts lost by KO).`);
      if (x.sub_per15 >= 1 && y.sub_loss_rate >= 0.12)
        out.push(`Submission threat: ${x.name} attempts ${x.sub_per15.toFixed(1)} subs/15 and ${y.name} has been tapped before.`);
      const lx = landsOn(x, y), ly = landsOn(y, x);
      if (lx - ly >= 1.5)
        out.push(`Striking volume: projected ${lx.toFixed(1)} vs ${ly.toFixed(1)} significant strikes per minute in ${x.name}'s favour.`);
      if (rounds >= 5 && x.late_win_rate - y.late_win_rate >= 0.15)
        out.push(`Five rounds favour ${x.name}: ${pct(x.late_win_rate)} win rate in fights reaching round 3+ vs ${pct(y.late_win_rate)}.`);
      if (x.age != null && y.age != null && y.age >= 35 && y.age - x.age >= 5)
        out.push(`Age: ${y.name} is ${Math.round(y.age)} facing a ${Math.round(x.age)}-year-old; decline risk is real past 35.`);
      if (y.layoff_days != null && y.layoff_days >= 500) out.push(`Ring rust: ${y.name} has been out ${Math.floor(y.layoff_days / 30)} months.`);
      if (x.reach_cm && y.reach_cm && x.reach_cm - y.reach_cm >= 10)
        out.push(`Reach: ${x.name} has a ${Math.round(x.reach_cm - y.reach_cm)}cm reach advantage.`);
      if ((x.stance || "").toLowerCase() === "southpaw" && (y.stance || "").toLowerCase() === "orthodox")
        out.push(`Stance: southpaw ${x.name} vs orthodox ${y.name} (open-stance exchanges).`);
      if (x.streak >= 4) out.push(`Momentum: ${x.name} is on a ${x.streak}-fight win streak.`);
      if (x.sos - y.sos >= 100)
        out.push(`Competition level: ${x.name}'s opponents averaged ${Math.round(x.sos)} Elo vs ${Math.round(y.sos)} for ${y.name}'s.`);
      return out;
    }
    function insights(a, b, rounds) {
      const notes = oneWay(a, b, rounds).concat(oneWay(b, a, rounds));
      const few = [a, b].filter((s) => s.fights < 3).map((s) => s.name);
      if (few.length) notes.push(`Limited data on ${few.join(", ")} (<3 bouts in dataset); profile leans on population averages.`);
      return notes;
    }

    /** Apply a fighter adjustment {elo, overrides} like Adjustments.apply. */
    function applyAdjustment(s, adj) {
      if (!adj) return s;
      const out = Object.assign({}, s, { elo: s.elo + (Number(adj.elo) || 0) });
      for (const [k, v] of Object.entries(adj.overrides || {})) {
        if (v === null || v === undefined || v === "" || Number.isNaN(Number(v))) continue;
        out[k] = INT_FIELDS.has(k) ? Math.round(Number(v)) : Number(v);
      }
      return out;
    }

    /** Full prediction. weights: effective feature weights; manual: extra log-odds toward a. */
    function predict(a, b, opts) {
      const rounds = opts.rounds || 3;
      const x = features(a, b, rounds);
      const contrib = {};
      let logit = 0;
      for (const k of data.features) {
        contrib[k] = (opts.weights[k] || 0) * x[k];
        logit += contrib[k];
      }
      const manual = opts.manual || 0;
      const p = sigmoid(logit + manual);
      const da = methodDistribution(a, b, rounds), db = methodDistribution(b, a, rounds);
      const methods = { a: {}, b: {} };
      for (const m of BUCKETS) {
        methods.a[m] = p * da[m];
        methods.b[m] = (1 - p) * db[m];
      }
      const factors = Object.entries(contrib);
      if (manual) factors.push(["manual", manual]);
      factors.sort((u, v) => Math.abs(v[1]) - Math.abs(u[1]));
      return { p, x, methods, factors, insights: insights(a, b, rounds), logit: logit + manual };
    }

    return { features, methodDistribution, classify, insights, predict, applyAdjustment, landsOn, takedownsOn, chin };
  }

  function devig(oddsA, oddsB) {
    const imp = (o) => (o < 0 ? -o / (-o + 100) : 100 / (o + 100));
    const pa = imp(oddsA), pb = imp(oddsB);
    return pa / (pa + pb);
  }

  const api = { makeEngine, sigmoid, devig, agePenalty, layoffPenalty, BUCKETS };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.MMAEngine = api;
})(typeof window !== "undefined" ? window : globalThis);
