# Scouting playbook

Statistics miss the feel of a fight: rhythm, habits, how a fighter builds offence, what happens when they're hurt. Scouting fills that gap:

- **Reports** on how each fighter fights.
- **Reads**: a bounded judgement per bout that feeds the prediction.
- **A pundit ledger** that learns which analysts are worth listening to.

## Where things live

| What | File | Page database (`scouting` collection) |
|---|---|---|
| News index (metadata only: outlet, title, link, date, fighters) | `data/scouting/news.jsonl` | none |
| Fighter reports, in our own words with sources | `data/scouting/reports/<slug>.json` | `<slug>` (kind `report`) |
| Reads per bout, with pundit picks | `data/scouting/reads/<date>-<event>.json` | `read--<slugA>--<slugB>` (kind `read`) |
| Pundit ledger | `data/scouting/pundits.jsonl` | `scoreboard` |
| Per-event drafts (what was written and why) | `data/scouting/drafts/` | none |

Article text is cached in `.cache/` for reading and never committed.

## Sources

**Feeds (`scout news`):**

- MMA Fighting
- Sherdog
- Bloody Elbow
- Cageside Press
- MMA Mania
- BJPenn.com
- MMA Weekly
- LowKick MMA
- ESPN

**Archive search (`scout search`):**

- Cageside Press
- BJPenn.com
- LowKick MMA

**Read directly each fight week (the best style analysis):**

- UFC.com: *Fight By Fight Preview* and *Coach Conversation*.
- Sherdog: the prelims and main-card previews (one page per bout, each with a pick).
- MMA Mania: *Odds, full fight preview and prediction* for each bout.
- MMA Fighting: staff picks (usually posted Thursday or Friday).

**Web search** fills gaps. Treat search summaries as leads, not facts, and check them against the article or our records.

Two rules:

- **Verify.** Records, results and methods must match our verified fight data. If a claim comes from a single outlet, say so ("per MMA Mania"). When sources disagree, write down the disagreement rather than picking one.
- **Our own words.** Summarize and cite; short quotes only.

## Fight week

```bash
python -m mma_predictor scout news                 # latest headlines -> news index
python -m mma_predictor scout card                 # the next card, and which fighters lack a report
python -m mma_predictor scout search --card        # archive search for everyone on the card
python -m mma_predictor scout brief "Fighter Name" --fetch   # reading packet: numbers, recent fights, coverage
```

Then:

1. **Reports.** Write or refresh a report for every fighter on the card; `data/scouting/drafts/ufc332_reports.py` is the template. Each report has:
   - `summary`: two or three sentences.
   - `how_they_fight`: Striking, Grappling, Defense, Pace & cardio, Fight IQ.
   - `patterns`, `concerns`, `keys_to_beat`.
   - `news`, each item with a source link.
   - `sources`.
   - `depth`: thin, moderate or good.

   Focus on how they win: their setups, habits and rhythm, what breaks them, and how they respond to adversity.
2. **Reads.** One per bout; the template is `drafts/ufc332_reads.py`.
   - `favours`, plus `logit` from 0 to 0.8. This is how far to move the model for what it can't see, not a restatement of the model.
   - `confidence`, `reasoning`, `factors`.
   - `p_model` and `p_market` at the time of writing, taken from `picks sheet`.

   Sizing:

   | Read | When |
   |---|---|
   | 0.1 to 0.25 | A real but modest edge: a style matchup, a layoff, age. |
   | 0.4 to 0.8 | Only when the model is plainly uninformed, e.g. no UFC data for either fighter. |
   | 0, or no read | When genuinely even or unknown. |
3. **Pundit picks.** Record every pick you read (outlet, author, pick, method, link), with FanDuel's no-vig probability for the pick as `p_market`.
4. **Publish:** `python -m mma_predictor scout sync`, then write the listed documents to the `scouting` collection with ArtifactData. Page: https://claude.ai/artifact/4kRut1VP9KGeCFqMd9fR2A. Use `list` first so every existing document is pinned with `if_version`; at most 50 writes per batch.
5. Commit `data/scouting` and push.

Reads feed:

- **The site's predictions**, as the factor "Claude's scouting read".
- **The AI Picks betting sheet.** The read shifts the model's number before it's blended with FanDuel's price. Run `picks sheet` after the reads are in.

## After the card

```bash
python -m mma_predictor scout grade    # reads and pundit picks vs results Wikipedia and Sherdog agree on
python -m mma_predictor scout sync     # then ArtifactData batch as above; commit and push
```

## Weighting (be patient)

- **Reads** count at full weight. Once 150 bouts are graded, `reads.fit_read_weight` re-fits the multiplier to how much the reads actually improve on the model (log loss); apply it then.
- **Pundits** each count equally until they have 40 graded picks. Each pick is compared with the market's probability for the fighter picked, as z = (wins − expected) / SE:

  | z | Weight |
  |---|---|
  | beyond +1.96 | ×1.5 |
  | beyond +2.58 | ×2 |
  | below −1.96 | ×0.5 |
  | below −2.58 | dropped (0) |

  Until then, pundits inform the reads only qualitatively. Don't adjust anyone's weight early: a few cards can't separate skill from luck.
