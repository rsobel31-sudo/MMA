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

### Ratings: Striking, Wrestling, Grappling

There is no single Elo. Each fighter has eleven sub-ratings (1500 = average),
mostly attack/defence pairs rated against each other:

| Category | Sub-ratings | Evidence per bout |
|---|---|---|
| Striking | striking offence vs striking defence; power vs chin | accuracy, share of significant strikes, knockdowns, KO/TKO wins |
| Wrestling | takedown offence vs takedown defence | takedowns landed per attempt |
| Grappling | top control vs escapes; ground and pound vs escapes; submission offence vs submission defence | control-time share, ground strikes per control minute, submission wins and attempts |

Category rating = mean of its sub-ratings. **Overall = 45% striking + 25%
wrestling + 30% grappling.** For each attack/defence pair:

```
expected = sigmoid(logit(base_rate) + ln(10)/400 * (attack - defence))
delta    = K_stat * weight * clip((observed - expected) / sd(base_rate), ±3)
attack  += delta;  defence -= delta
```

Every result also moves the overall by the classic Elo amount,
`K * margin * (result - 1 / (1 + 10^((overall_B - overall_A)/400)))`,
tilted toward the categories the bout was decided in (a KO toward
striking, a submission toward grappling, a decision by who won each domain on
the stats). See `mma_predictor/skills.py` for the full definition and
constants. The old single-number Elo (`ratings.py`) is kept only as a
backtest baseline.

**Strength of schedule is built into every update.** Each attack/defence
comparison is scored against what the opponent's ratings predicted, so
surviving 15 minutes with an elite submission grappler raises your submission
defence far more than surviving a weak one (see `tests/test_skills.py`). On
top of that:

- Career stats (strikes landed/absorbed, accuracy, defence, takedown %) are
  opponent-adjusted: each bout is judged against what that opponent usually
  allows or lands.
- A fighter first seen on a regional card starts below a UFC debutant
  (1400 regional, 1440 feeder such as LFA/DWCS, 1470 major such as Bellator/PFL/ONE, 1500 UFC),
  so a padded regional record counts for less.
- Not finishing someone costs the attacker only 40% as much as surviving earns
  the defender: a grappler who wins on control isn't punished for not getting
  the tap.

### Uncertainty, and why a weak schedule can't buy a top ranking

Each fighter also carries a rating uncertainty (Glicko RD). A new fighter
starts unproven (±250 in the UFC, more if they debuted regionally). Each bout
shrinks the uncertainty by how informative it was: `g(RD_opp)² · E · (1 − E)`.
Beating someone you were expected to beat 95% of the time barely counts.
Inactivity grows it back. Rankings use the **proven rating**,
`overall − 0.5 × (RD − 45)`. Stat evidence from bouts against opponents more
than 100 points below you is also discounted (to 35% at a 300-point gap).

**Tuning.** `python -m mma_predictor compare` measures how closely our order
matches the official UFC rankings (media panel or Meta) in each division.
Settings were kept only if they improved both that agreement and the
backtest's log-loss on real results: result K = 48 and a 0.5-sigma
uncertainty penalty. With full careers for every ranked fighter the
mean rank correlation is 0.79, and the model picks 68.4% of 1,501 UFC bouts
(79.8% when it's at least 65% confident).

### Analysis and highlights

```bash
python -m mma_predictor analyze --data data/sherdog
```

- **Regression**: logistic regression of UFC results on every factor
  (point-in-time), standardised, with standard errors and p-values.
- **Confidence vs results**: out-of-sample hit rate by the model's stated
  confidence. The raw model hedged toward 50/50 (its 70–85% picks won 80–86%),
  so exports fit a logit stretch on the out-of-sample predictions (≈1.14;
  fitted on either half of history it improves the other half).
- **Matchup patterns**: 17 readable situations (clear wrestling edge, big
  age gap, opponent off a KO loss, long layoff, veteran vs newcomer…). For
  each, the actual win rate of the side with the edge vs the model's
  pre-fight expectation; z ≥ 2 marks where the formula needs work.
- **Highlights on upcoming cards**: *Best bet* (high-certainty band with a
  strong historical hit rate, backed by a pattern, nothing against it),
  *High certainty*, *Upset watch* (the underdog has an edge the model has
  underrated, or a strong edge against a shaky pick), *Toss-up*.
- **Prediction log** (`data/predictions/log.json`): every export records
  the pick for each scheduled bout, keeps the first one frozen, and grades it
  once the result is in the data. The Insights tab shows the scorecard.

### Recency

Fighter tendencies (strike and takedown rates, accuracy and defence, finish
habits, late-round record) weight bouts from the last 18 months fully; older
bouts fade, halving every two years beyond that. Records and damage totals
(KO losses, knockdowns absorbed) stay cumulative. Ratings move faster while
uncertain (K × (RD/110)², clamped 0.8–1.6), so a new fighter or one returning
from a layoff is judged mostly on their latest results. Together these raised
agreement with the official rankings from 0.78 to 0.82 and slightly improved
the backtest log-loss.

### Scouting: background and fight commentary

`data/scouting/backgrounds.json` records martial-arts pedigree (discipline,
level, detail, source). It becomes a prior on the matching sub-ratings that fades
as MMA evidence builds (`boost × 10 / (10 + bouts)`). A world-champion
BJJ black belt keeps elite grappling ratings even with few MMA submissions.

`data/scouting/fight_notes.json` holds judged performances ("won the
grappling", "even on the feet") from −2 to +2 per domain. They count as
evidence, again against expectation: holding even with an elite grappler is a
big positive. In the web interface, the **Judge** button on each recent fight
records your own judgments; they feed the ratings when the data is rebuilt.

### Wear and tear

Age alone treats every 34-year-old the same. The wear index adds mileage (pro
fights, cage time) and damage (KO/TKO losses, knockdowns and significant
strikes absorbed), and weighs it more heavily past 30:
`wear × (1 + max(0, age − 30) / 8)`.

Without per-bout stats (Sherdog/Tapology records), only finishes and results
inform the categories: control, escapes and ground and pound move together
and takedown offence/defence can't be told apart. UFCStats data fills these in.

### Other attributes

| Area | Attributes |
|---|---|
| Overall strength | Category ratings above, strength of schedule (average opponent overall rating) |
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

## Web interface: MMA Fight Lab

`app/` is a single page for working with the data and applying what you know:

- **Matchup:** pick red and blue corners, 3 or 5 rounds, optional moneylines. You get win probability, method of victory, the factors driving the pick and matchup patterns.
- **Tale of the tape:** every attribute is editable. Type over a number (takedown defence, strikes absorbed, KO-loss rate, age, reach…) and the prediction updates instantly. Edited values turn amber and can be reset one at a time. You can also nudge a fighter's Elo and keep a scouting note.
- **Your read on this fight:** a slider that shifts the odds toward either corner for things the numbers can't see (weight cut, injury, short notice), with a note.
- **Model weights:** change how much each factor counts.
- **Fighters:** a sortable, filterable table, or a breakout by division (men's and women's) ranked by any rating.
- **Fighter profiles:** click any fighter name anywhere to open a written bio, ratings against the division median, researched credentials, full fight history (with a Judge button per bout) and your own dated notes.
- **Upcoming cards:** every scheduled UFC event (from Wikipedia) with a pick, win probability and likely finish for each bout, plus your saved matchups.
- **My adjustments:** review and export everything you've changed.

```bash
python -m mma_predictor export --data data/sherdog --events UFC   # builds app/data.json
python -m mma_predictor serve                                      # http://127.0.0.1:8765
```

The page runs the same model as the Python code; `app/engine.js` is a port, and
`tests/test_engine_parity.py` keeps the two in agreement. Adjustments are saved
in the page's database when it's published as a claude.ai artifact, or in the
browser when served locally. Copy them from **My adjustments** into
`data/adjustments.json` and pass `--adjustments data/adjustments.json` to
`predict` or `card` to apply them in the Python tools too.

## Commands

```bash
python -m mma_predictor predict  "A" "B" [--rounds 5] [--title] [--odds -150 +130] [--model M | --fit]
python -m mma_predictor card     --card data/sample/upcoming_card.csv [-v]
python -m mma_predictor profile  "Fighter"
python -m mma_predictor rankings --top 25
python -m mma_predictor train    --out models/model.json
python -m mma_predictor backtest
python -m mma_predictor import   sherdog  --ufc-events 60 --depth 0 --out data/sherdog   # every fighter from the last 60 UFC events
python -m mma_predictor import   sherdog  Israel-Adesanya-56374 --out data/sherdog --depth 1
python -m mma_predictor import   ufcstats --out data/ufcstats [--ufc-events N]              # per-bout strike/takedown stats
python -m mma_predictor import   tapology israel-adesanya       --out data/tapology --depth 1
python -m mma_predictor merge    data/ufcstats data/sherdog data/tapology --out data/merged
python -m mma_predictor rebuild  --data data/sherdog        # rebuild from every cached Sherdog page
python -m mma_predictor enrich   --data data/sherdog        # UFC division + gender (Wikipedia roster)
python -m mma_predictor upcoming                            # scheduled UFC cards -> data/upcoming.json
python -m mma_predictor compare  --data data/sherdog        # our order vs official UFC rankings
python scripts/crawl_ranked.py                              # careers of every ranked fighter + their UFC opponents
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

### Division and gender (Wikipedia UFC roster)

```bash
python -m mma_predictor enrich --data data/sherdog
```

This reads Wikipedia's [List of current UFC fighters](https://en.wikipedia.org/wiki/List_of_current_UFC_fighters),
which lists every current UFC fighter by division, men's and women's
separately, and sets their division and gender. Names are matched regardless
of accents, order or middle names ("Ian Garry" = "Ian Machado Garry").
Everyone else gets a gender from the nearest known fighters in the fight
graph, because men and women don't fight each other. Divisions only women
contest (strawweight) and those only men contest (lightweight and up) are
extra anchors.

Tapology's robots.txt disallows Anthropic's crawlers, so Claude doesn't fetch
from it. The Tapology importer is there for you to run yourself, subject to
Tapology's terms.

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
  adjustments.py your manual edits, applied on top of the data
  export.py      snapshot export for the web interface
  sources/       Sherdog, Tapology & UFCStats importers, dataset merge
app/             MMA Fight Lab web interface (index.html, engine.js, data.json)
scripts/generate_sample_data.py   synthetic demo data
```

```bash
pip install pytest && python -m pytest
```
