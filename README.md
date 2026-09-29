# MMA Fight Predictor

A system for evaluating MMA matchups and predicting who wins, how, and why.
It combines ratings, attribute profiles, style-matchup patterns and a
trainable model, and can be backtested walk-forward to measure how accurate it
really is.

Pure Python 3.9+, no runtime dependencies (`pytest` for tests).

```bash
python -m mma_predictor predict "Fighter A" "Fighter B" --rounds 5 --odds -150 +130
```

> The bundled `data/sample/` dataset is **synthetic**: fictional fighters and
> simulated bouts, used for demos and tests. For real predictions, import real
> records (see [Getting real data](#getting-real-data)).

## What it looks at

Each fighter's profile is rebuilt from their fight history **as of the bout
date**, so predictions and backtests never see the future. Rate stats are
shrunk toward population averages, so a fighter with only a few bouts isn't
judged on a handful of minutes.

| Area | Attributes |
|---|---|
| Overall strength | MMA-tuned Elo (finishes and early stoppages count more than split decisions; newcomers converge fast; regional record seeds the starting rating), strength of schedule |
| Striking | Sig. strikes landed/absorbed per min, accuracy, defence, knockdowns scored/absorbed |
| Grappling | Takedowns per 15, TD accuracy, TD defence, submission attempts, control-time share |
| Durability | KO-loss rate, KO losses in last 3 bouts, knockdowns absorbed |
| Finishing | Share of wins/losses by KO/TKO, submission and decision |
| Physical | Age (prime/decline curve), reach, stance |
| Momentum | Recency-weighted form, streak, layoff length |
| Cardio | Win rate in bouts reaching round 3+, weighted more heavily for 5-rounders |

### Matchup features

Features are mostly **interactions**: what A does well against what B does
badly. For example:

- `wrestling_edge`: A's takedown rate scaled by how porous B's takedown defence is (and vice versa)
- `striking_exchange`: projected strikes landed per minute given each side's output and the other's defence
- `power_vs_chin`: knockdown power against the opponent's KO-loss history
- `submission_threat`, `control`, `cardio`, `age_curve`, `layoff`, `chin_damage`, `reach`, `stance`, `form`, `schedule_strength`, `elo`

Every feature flips sign when the corners are swapped, and the model has no
intercept, so P(A beats B) = 1 − P(B beats A) exactly.

### Model

A logistic model with hand-set prior weights encoding conventional MMA wisdom,
so it works before training. `train` fits the weights to data with a penalty
that pulls toward those priors rather than toward zero. On small datasets that
keeps it sensible; as data grows, the data takes over.

### Output

- Win probability and a confidence label
- Method breakdown: P(each fighter by KO/TKO, SUB, DEC), and P(goes the distance). This combines how the winner tends to win with how the loser tends to lose, adjusted for the specific matchup and for 5 rounds.
- Key factors ranked by their contribution to the log-odds
- Scouting profiles and style tags (wrestler, volume striker, power puncher, anti-wrestler…)
- Matchup pattern notes (wrestling path, power vs compromised chin, 5-round cardio gap, age cliff, ring rust, reach, southpaw vs orthodox, momentum, level of competition)
- With moneylines: no-vig market probability and the model's edge

## Commands

```bash
python -m mma_predictor predict  "A" "B" [--rounds 5] [--title] [--odds -150 +130] [--model M | --fit]
python -m mma_predictor card     --card data/sample/upcoming_card.csv [-v]
python -m mma_predictor profile  "Fighter"
python -m mma_predictor rankings --top 25
python -m mma_predictor train    --out models/model.json
python -m mma_predictor backtest
python -m mma_predictor import   sherdog  Israel-Adesanya-56374 --out data/sherdog --depth 1
python -m mma_predictor import   tapology israel-adesanya       --out data/tapology --depth 1
python -m mma_predictor merge    data/ufcstats data/sherdog data/tapology --out data/merged
```

Every command takes `--data DIR` (default `data/sample`). Names match partially and case-insensitively.

## Getting real data

### Sherdog / Tapology (full career records)

`import` crawls fighter pages starting from the seed fighters and follows
opponents `--depth` hops out. It records every **professional** bout,
including regional shows (amateur bouts are skipped), with the date, opponent,
result, method, round, time and event, plus DOB, height, reach and stance
where the page shows them.

- It's polite: it checks robots.txt, waits `--delay` seconds (default 3) between requests, and caches every page under `.cache/pages` so reruns don't refetch.
- A bout seen from both fighters' pages is written once.
- These sites don't publish per-bout striking/grappling numbers, so those features fall back to population averages for imported bouts. Elo, record, finishing tendencies, durability, form, age, reach and layoff are all fully informed.
- Check each site's terms of use before crawling, and keep crawls modest.
- The parsers were built against the sites' known markup and are covered by fixture tests. The live markup changes from time to time; if a parse comes back empty, update the selectors in `mma_predictor/sources/{sherdog,tapology}.py` and the matching fixture.

### Combining sources

`merge` unions datasets and matches the same bout across sources by fighter
names and a date within ±1 day. When both sources have a bout, the row with
per-corner stats wins and blank fields are filled in from the other. Put the
highest-priority dataset first. A typical setup: a UFC stats dataset for
strike and takedown numbers, plus Sherdog/Tapology for complete career
histories.

### CSV schema

`fighters.csv`: `name, dob, height_cm, reach_cm, stance, prior_wins, prior_losses`

`fights.csv`: `date, event, weight_class, fighter_a, fighter_b, winner, method, round, time, scheduled_rounds, title_fight`
plus optional per-corner stats `{a,b}_{sig_landed, sig_attempted, td_landed, td_attempted, sub_attempts, knockdowns, ctrl_seconds}`
and optional moneylines `a_odds, b_odds`. `winner` is a fighter name, `draw` or `nc`.

`card.csv`: `fighter_a, fighter_b, scheduled_rounds, title_fight, a_odds, b_odds, date`

## Backtest (synthetic sample)

```
model          n=735   acc= 64.6%  log-loss=0.6131  brier=0.2128
elo only       n=735   acc= 62.0%  log-loss=0.6494  brier=0.2290
model >=65%    n=381   acc= 76.1%
```

These numbers show the pipeline works; they say nothing about real-world
accuracy. Run `backtest` on real data to get that. For reference, closing
betting lines on real UFC fights typically pick the winner roughly 65–70% of
the time.

## Layout

```
mma_predictor/
  data.py        CSV loading, fight/fighter types, method & odds parsing
  ratings.py     MMA-tuned Elo
  history.py     point-in-time fighter snapshots with Bayesian shrinkage
  features.py    antisymmetric matchup features
  model.py       prior-anchored logistic model
  methods.py     KO/SUB/DEC prediction
  styles.py      style tags and matchup pattern notes
  predictor.py   high-level API + Prediction report
  backtest.py    walk-forward evaluation vs Elo and market baselines
  sources/       Sherdog & Tapology importers, dataset merge
scripts/generate_sample_data.py   synthetic demo data
```

```bash
pip install pytest && python -m pytest
```
