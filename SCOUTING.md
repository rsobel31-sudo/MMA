# Scouting playbook

Statistics miss the feel of a fight: rhythm, habits, how a fighter builds offence, what happens when they're hurt. Scouting fills that gap:

- **Reports** on how each fighter fights.
- **Reads**: a bounded judgement per bout that feeds the prediction.
- **The Fight Track Record**: a pundit ledger that learns which analysts are worth listening to (Insights tab).

## Where things live

| What | File | Page database (`scouting` collection) |
|---|---|---|
| News index (metadata only: outlet, title, link, date, fighters) | `data/scouting/news.jsonl` | none |
| Fighter reports, in our own words with sources | `data/scouting/reports/<slug>.json` | `<slug>` (kind `report`) |
| Reads per bout, with pundit picks | `data/scouting/reads/<date>-<event>.json` | `read--<slugA>--<slugB>` (kind `read`) |
| Pundit ledger (Fight Track Record) | `data/scouting/pundits.jsonl` | `scoreboard` |
| Pick articles found by search (CBS, SI, ...) | `data/scouting/pick_sources.json` | none |
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
   `scout card` prints each bout's **weighted consensus**: every picker counts by their Fight Track Record weight
   (×2, ×1.5, ×1, ×½ or 0). Lean on that, not the headcount: five chalk pickers agreeing tell you less than one
   picker with a proven edge over the market. Say in the read when a proven picker disagrees with the model.
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

## Fight Track Record (pundit history)

The ledger is filled from the outlets' own archives, not just the picks read in fight week, so pickers arrive
with years of graded picks. Anyone who publishes picks in the open belongs on it: the goal is to find the best
pickers, not the most famous, so keep adding sources, especially smaller outlets and staff tables.

```bash
python -m mma_predictor scout history --since 2024-01-01      # all sources; re-runs only add new picks
python -m mma_predictor scout history --sources cbs,staff --since <60 days ago> --verbose
```

| Source | Listing | Parser |
|---|---|---|
| Sherdog previews (every bout) | tag page `/tag/previews` | `parse_sherdog` |
| Cageside Press staff picks | WordPress API search | `parse_cageside` (headshot = pick) |
| MMASucka staff picks | `sitemap-predictions-N.xml` | `parse_staff` |
| Bleacher Report staff predictions | monthly article sitemaps | `parse_staff` |
| CBS Sports expert picks | `pick_sources.json` (web search) | `parse_cbs`, else `parse_staff` with the byline |
| RotoWire expert picks (six pickers, PPV main cards) | `mma_articles.xml` sitemap | `parse_grid` |
| MMAOddsBreaker staff pool (eight analysts incl. MikesMMAPicks, Big Marcel; every bout) | WordPress API (Crawl-delay 10) | `parse_numbered_grid` |
| MMA Intel (independent blog, every bout) | upcoming page only: recorded weekly | `parse_over` |
| SI MMA Knockout, ESPN panels, F4W and any other staff article | `pick_sources.json` (web search) | `parse_staff` / `parse_grid` / `parse_espn` |

Sources that only show upcoming picks (MMA Intel; add others the same way) are read every week: picks on bouts not yet
fought wait in `data/scouting/picks_pending.jsonl` and are graded on a later run once the results are verified. Niche,
independent pickers are the point: a self-reported record (MMA Intel claims 74%) means nothing until it is graded
here against the market.

Each pick is tied to a bout in `data/verified/fights.csv` (two sources agree on the winner) and its closing no-vig
odds; a pick that can't be tied to one bout and one fighter is skipped and listed with `--verbose`, never guessed.
Never use Tapology. MMA Junkie is an approved source (owner, Oct 2026), but it refuses automated reads (HTTP 402), so in practice its stories can't be fetched. To add a source: put its articles in `pick_sources.json` with
`source: "staff"` (or write a parser if the format is new), run `scout history`, and check the `--verbose` skips.

Every Tuesday, after the Sunday data refresh has verified the last card's results: search for that card's
CBS Sports and SI staff picks and any new outlet with named staff picks, add them to `pick_sources.json`, run
`scout history --since <60 days ago>`, then `scout sync` and publish the `scoreboard` document.


## Sherdog watchlist (every Tuesday)

`data/scouting/watchlist.json` lists forum members whose posts we follow. Sherdog's forums sit behind
Cloudflare bot protection and rate-limit hard, so this is done by hand with WebFetch at a gentle pace
(at most ~8 forum pages per run; on a 429, stop and try again next week; never try to get around the
protection). robots.txt allows /threads/ and /members/ pages; never fetch /search/ or /posts/.

1. Member profile pages (`profile` in the watchlist) are shown only to logged-in users (HTTP 403),
   so don't fetch them and never log in. Find each member's recent posts through web search instead:
   `site:forums.sherdog.com "<name>"`, plus the same with "prospect", "sign", "hype" or a division
   name, and the threads they started or posted in that you already know (`seen`).
2. Open threads (public) that are new since `last_checked` or not yet in `seen`, newest first, and
   read the member's posts in them (a thread's later pages: `<thread url>page-N`).
3. Read each new post. Every fighter they tout as a prospect or as someone a promotion should sign
   becomes a call: append a list to `data/prospects/noted.json` with `kind: "forum"`,
   `outlet: "Sherdog Forums"`, `author` and `person` set to the member's name, the post's date and
   thread URL, and the names exactly as written. Fight picks they make for UFC cards are pundit picks
   (SCOUTING.md pundits), not prospect calls. Opinions about how a fighter fights can go into that
   fighter's scouting report, cited.
4. Add the URLs to `seen`, set `last_checked`, and in the summary list who said what.
