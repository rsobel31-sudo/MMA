# Prospects playbook (monthly recrawl)

Runs on the 1st of each month. Goal: keep the Prospects tab current and keep
grading the outlets, creators and forum posters who call prospects.

Rules: under 28, fewer than 14 pro fights, not signed to a major promotion
(UFC, PFL/Bellator, ONE, ACA, RIZIN; Contender Series / Road to UFC are not
"signed"). Every prospect needs two sources (Fight Matrix + Sherdog, or an
outlet list + Sherdog).

1. `mv data/prospects/candidates.jsonl data/prospects/candidates.prev.jsonl`
   (fresh recheck: records, ages and promotions change).
2. `python scripts/crawl_prospects.py --out data/prospects --max-pages 45 --noted data/prospects/noted.json`
   (about 1-2 hours; resumable — rerun the same command if it stops).
3. Scrub for new calls (WebSearch; X posts via `site:x.com` searches; Sherdog
   forums via WebFetch; Tapology is blocked) and append them to
   `data/prospects/noted.json` with source, kind (outlet/creator/forum), date
   and names. Never edit old calls — they are graded against later results.
   When a list spells a name differently from Sherdog, add it to "aliases" only
   after checking record and birth date match (two people can share a name).
   Rerun step 2 with `--skip-ranks` to pick up new names.
   The crawl also re-checks every prospect we've listed whose rankings row no longer
   passes the screen (signed? aged out?) and confirms each signing on BestFightOdds
   (`data/prospects/signing_checks.json`); `--confirm-only` reruns just that.
4. `python -m mma_predictor prospects` rebuilds `app/prospects.json`; caller
   weights update automatically (only after 20 graded calls and |z| >= 1.96).
5. `python -m pytest -q`, then publish `app/index.html` to the Fight Lab
   artifact with files engine.js, data.json, prospects.json; delete
   candidates.prev.jsonl; commit and push.

## Every Friday and Sunday: prospect fights

The AI Picks routine runs `python -m mma_predictor prospect-week`: every listed prospect
booked on any card in the next nine days (Sherdog's event listings, all promotions,
matched by Sherdog profile), and results for the ones that have fought (read from the
prospect's own Sherdog record). Kept in `data/prospects/fights.jsonl`, shown on the
Prospects page under "This week".
