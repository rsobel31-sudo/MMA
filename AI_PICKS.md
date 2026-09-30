# AI Picks playbook

Claude bets a $100 bankroll on UFC cards at FanDuel's prices. Picks go in every Friday before the card; results are graded on Sunday.
The ledger (`data/ai_picks/ledger.json`) is the record, and the web page (Fight Lab, **AI Picks** tab) reads a copy from the page database.

- Page: https://claude.ai/artifact/4kRut1VP9KGeCFqMd9fR2A
- Database collection: `ai_picks`. It holds one `summary` document and one document per week (`w1`, `w2`, ...), written with the ArtifactData tool.
- Branch: `claude/mma-fight-predictor-9sxxhl`

## The goal

**Maximize overall earnings: finish with the largest bankroll possible over the long run.** Every decision serves that.

- Growth compounds. The strategy that ends richest over many cards maximizes the bankroll's long-run growth rate, not one week's expected profit. Going all-in on the best-EV bet maximizes this week's expectation, but it almost surely busts over a season, and a bust bankroll earns nothing more.
- So size bets to the edge.
  - Kelly (the sheet's quarter-Kelly column is a guide) is the right frame for growth.
  - Use a fraction of it because our probabilities are estimates.
  - Stake more when the edge is solid and well understood, less when it rests on thin or unvalidated modelling (round props, small moneyline gaps).
- Passing is correct when nothing has a real edge; betting without an edge only lowers expected earnings. But don't pass out of caution when a genuine edge is there: unbet edges are lost earnings.
- Parlays multiply the bookmaker's margin. Use them only when every leg is independently +EV.
- Judge the strategy by bankroll growth and closing-line value over many cards, not by any single week's result.

## Rules of the game

- The bankroll starts at $100.00 with no top-ups. The minimum stake is $1.00. Below that with nothing pending, the bankroll is **bust**: no more bets, and an alert shows on the page.
- The book is FanDuel, as listed on BestFightOdds. A bet is recorded at the sheet's price only. `picks place` refuses markets that aren't on the sheet, stakes above the available bankroll, bets after the event starts, and cards more than 3 days out.
- Any bet type FanDuel offers on the sheet is allowed:
  - moneylines
  - method (KO/TKO, submission, decision) and inside the distance
  - round props, fight ends in round N, and starts round N
  - over/under rounds
  - parlays across different bouts (same-bout parlays are priced differently by FanDuel, so they're refused)
- Staking is fully discretionary: bet it all, bet nothing, anything in between. A pass is recorded too, with the reason.
- Grading needs two sources:
  - The Wikipedia event page and the fighter's Sherdog record must agree on winner, method, round and time before a bet settles.
  - Draws and no contests void (refund) moneylines. No contests void every prop.
  - A void leg drops out of a parlay.
  - A bout that never happened is void.

## Friday: settle, then pick

```bash
git fetch origin claude/mma-fight-predictor-9sxxhl && git checkout claude/mma-fight-predictor-9sxxhl && git pull origin claude/mma-fight-predictor-9sxxhl
pip install -e . >/dev/null 2>&1 || true
python -m mma_predictor picks settle          # grade anything still open (exit 3 = bust, 2 = still waiting on results)
python -m mma_predictor picks sheet --data data/verified
```

The sheet shows each bout (model vs FanDuel) and every market sorted by expected value. For each market it gives:

- `ours`: our probability
- `FD`: FanDuel's probability with the margin removed
- `EV`
- a quarter-Kelly stake guide

It's saved to `data/ai_picks/sheets/<date>-<event>.json`; market ids like `45058:ml:a` go in the bets file.

How to read it honestly:

- **Win probabilities**:
  - These are the model blended with FanDuel's own line: 0.38 model, 0.84 market, in log-odds.
  - The closing line beats the model on its own. The blend beats the line only slightly: log loss 0.595 vs 0.599 on 3,220 later bouts.
  - So a moneyline "edge" of a few points is mostly noise. Big gaps usually mean the model lacks something the market knows (injury, weight cut, a late replacement, a layoff). Check the news before trusting one.
- **Props**:
  - The finish model's decision rate is recalibrated (it finished too many fights). Tested on 2023+ bouts, the calibrated mean was 50.2% vs 49.6% actual.
  - Props are then shrunk halfway to FanDuel's price.
  - Round-by-round timing comes from league-wide finish times, not the fighters. Treat round props as long shots with thin edges.
- Positive EV on the sheet is necessary, not sufficient. Look for a reason the number is right.

Write the bets file, e.g. `data/ai_picks/bets/2026-10-03-ufc-332.json`:

```json
{
  "note": "The read on the card: what stands out, what to avoid, why this much (or nothing).",
  "picks": [
    {"legs": ["45058:ml:a"], "stake": 6, "reasoning": "Why this price is wrong."},
    {"legs": ["44794:ml:a", "45053:ml:a"], "stake": 2, "reasoning": "Parlay: why these belong together."}
  ]
}
```

Use `"picks": []` to pass, keeping the note. Then place the bets:

```bash
python -m mma_predictor picks place --sheet data/ai_picks/sheets/<file>.json --bets data/ai_picks/bets/<file>.json
```

## Publish to the page

```bash
python -m mma_predictor picks sync --out .cache/ai_picks_sync
```

This prints a batch of `set` writes, one per document. Before writing:

1. Read the `ai_picks` collection with ArtifactData `list` (url above) to get each existing document's `version`.
2. Send one ArtifactData `batch`: `set` each document from its `file_path`, with `if_version` for every document that already exists.
   - New documents (a new week) need no `if_version`.
3. Don't republish the page itself; the database write is enough.

## Commit

```bash
git add data/ai_picks && git commit -m "AI Picks: <event> (<n> bets, $<staked>)" && git push -u origin claude/mma-fight-predictor-9sxxhl
```

Committing before the fights is what timestamps the picks.

## Sunday: grade

Run `picks settle`, `picks sync`, the ArtifactData batch, and a commit ("AI Picks: settled <event>"). If results aren't in on both sources yet (exit code 2), leave the week open; Friday's run settles it.

## Bust

If `picks settle` or `picks status` exits 3:

1. Sync and write the database anyway. The page shows the out-of-money alert from `summary.bust`.
2. Send the user a push notification: "Fight Lab AI Picks: the bankroll is bust ($X left)."
3. Place no more bets.
