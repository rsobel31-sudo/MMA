"""The web interface's JS engine must agree with the Python predictor."""

import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

from mma_predictor.adjustments import Adjustments
from mma_predictor.data import load_dataset
from mma_predictor.export import export
from mma_predictor.history import FightHistory
from mma_predictor.predictor import FightPredictor

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")

JS = r"""
const E = require(process.argv[2]);
const input = JSON.parse(require("fs").readFileSync(0, "utf8"));
const eng = E.makeEngine(input.data);
const byName = Object.fromEntries(input.data.fighters.map((f) => [f.name, f]));
const adj = input.adjustments;
const weights = Object.assign({}, input.data.weights, adj.weights || {});
const out = input.pairs.map(([a, b, rounds]) => {
  const fa = eng.applyAdjustment(byName[a], (adj.fighters || {})[a]);
  const fb = eng.applyAdjustment(byName[b], (adj.fighters || {})[b]);
  let manual = 0;
  for (const m of adj.matchups || []) {
    if (m.a === a && m.b === b) manual += m.logit;
    else if (m.a === b && m.b === a) manual -= m.logit;
  }
  const edit = eng.intangiblesEditLogit(byName[a], fa, byName[b], fb);
  const r = eng.predict(fa, fb, { rounds, weights, manual, intangiblesEdit: edit });
  return { p: r.p, methods: r.methods, x: r.x, n_insights: r.insights.length };
});
process.stdout.write(JSON.stringify(out));
"""


@pytest.mark.skipif(NODE is None, reason="node not installed")
@pytest.mark.parametrize("with_adjustments", [False, True])
def test_js_engine_matches_python(tmp_path, with_adjustments):
    bios, fights = load_dataset(ROOT / "data" / "sample")
    h = FightHistory(bios, fights)
    data = export(h, min_fights=1, active_years=100)
    names = [f["name"] for f in data["fighters"]][:16]
    pairs = [(names[i], names[i + 1], 5 if i % 3 == 0 else 3) for i in range(0, 15)]
    adj = {}
    if with_adjustments:
        adj = {
            "fighters": {
                names[0]: {"elo": 60, "overrides": {"td_def": 0.9, "slpm": 6.1, "streak": 3, "r_td_def": 1700, "sig_diff5": -2}, "note": "x"},
                names[3]: {"elo": 0, "overrides": {"r_sub_off": 1400, "r_power": 1650, "i_athleticism": 1780, "i_killer_instinct": 1300, "sig_diff5": 3.5, "slpm": 5.2}, "note": ""},
            },
            "weights": {"wrestling_edge": 0.8, "overall": 0.9, "grappling_rating": 0.6, "intangibles_rating": 0.7},
            "matchups": [{"a": names[2], "b": names[1], "logit": 0.4, "note": ""}],
        }
    predictor = FightPredictor(h, adjustments=Adjustments.from_dict(adj))
    script = tmp_path / "run.js"
    script.write_text(JS)
    res = subprocess.run(
        [NODE, str(script), str(ROOT / "app" / "engine.js")],
        input=json.dumps({"data": data, "pairs": pairs, "adjustments": adj}),
        capture_output=True, text=True, check=True,
    )
    js = json.loads(res.stdout)
    # Export rounds values to 5 decimals, so allow a small tolerance.
    for (a, b, rounds), r in zip(pairs, js):
        py = predictor.predict(a, b, scheduled_rounds=rounds)
        assert math.isclose(r["p"], py.prob_a, abs_tol=2e-4), (a, b)
        for k, v in py.features.items():
            assert math.isclose(r["x"][k], v, abs_tol=2e-3), (a, b, k)
        for m in ("KO/TKO", "SUB", "DEC"):
            assert math.isclose(r["methods"]["a"][m], py.methods[(a, m)], abs_tol=2e-4)
            assert math.isclose(r["methods"]["b"][m], py.methods[(b, m)], abs_tol=2e-4)
        py_patterns = [n for n in py.insights if not n.startswith("Your ")]
        assert r["n_insights"] == len(py_patterns), (a, b)
