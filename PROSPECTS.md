# Prospects playbook (monthly recrawl)

Runs on the 1st of each month. Goal: keep the Prospects tab current and keep
grading the outlets, creators and forum posters who call prospects.

The list keeps the top 100 by score in each division (`PER_DIVISION`; owner's picks always stay).
A prospect Fight Matrix doesn't rank gets a stand-in rating percentile by pro fights (`UNRATED_LADDER`): 3 or fewer 15th,
4 25th, 5 40th, 6+ the division's middle (50th). Many regional fighters simply aren't in its rankings, but a 2-0
teenager shouldn't outrank proven fighters on youth alone.
Rules: under 28 (light heavyweights: 30 and under; heavyweights: 31 and under, since the big men mature later), fewer than 14 pro fights, a winning record, not in a major promotion (UFC,
PFL/Bellator, ONE, ACA, RIZIN; Contender Series / Road to UFC don't count), active
in the last two years. Anyone who has fought in the UFC is out for good; a fighter who
has formally left PFL, ONE, ACA or RIZIN (most recent fight outside the majors) is
eligible again, tagged ex-<promotion>. The build re-checks every stored candidate
against these rules, so a rule change applies without a recrawl. Every prospect needs two sources (Fight Matrix + Sherdog, or an
outlet list + Sherdog).

0. `python -m mma_predictor tapology-import`: imports whatever the owner dropped in
   `data/prospects/inbox/` (Tapology pages they saved, pasted lists; see the README there).
   Claude never crawls Tapology (its robots.txt bars Anthropic's crawlers). One exception: when the
   owner drops a specific Tapology link in chat, open that one page once (no following links from it);
   if it's refused (403 / Cloudflare), stop there and use Sherdog. If a saved page yields no fighters,
   say so in the summary and keep the file.
1. `mv data/prospects/candidates.jsonl data/prospects/candidates.prev.jsonl`
   (fresh recheck: records, ages and promotions change).
2. `python scripts/crawl_prospects.py --out data/prospects --max-pages 45 --noted data/prospects/noted.json --sweep`
   (`--sweep` also checks every fighter on the last two years of cards of each promotion in
   `data/prospects/promotions.json`, e.g. RCC; the owner adds promotions there)
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
5. Risers and fallers. `python -m mma_predictor prospect-snapshot` saves this
   month's ranking to `data/prospects/snapshots/YYYY-MM.json`, then
   `python -m mma_predictor prospect-report` compares it with last month's and
   writes `data/prospects/reports/YYYY-MM.json`: the biggest risers and fallers
   among the top 300 (with the fights in between), new names in the top 100, and
   who left the list and why. Read it and write the `summary` field yourself: two
   or three short paragraphs on the month's story (who earned a jump with a win,
   who fell on a loss, which moves came from the field rather than a fight, such
   as a new promotion sweep or Fight Matrix release). Then rerun step 4 so the
   page carries the report and every prospect's arrow is measured from the new
   snapshot (from the day after it is taken; until then the old one stands).
6. `python -m pytest -q`, then publish `app/index.html` to the Fight Lab
   artifact with files engine.js, data.json, prospects.json; delete
   candidates.prev.jsonl; commit and push.

## Every Friday and Sunday: prospect fights

The AI Picks routine runs `python -m mma_predictor prospect-week`: every listed prospect
booked on any card in the next nine days (Sherdog's event listings, all promotions,
matched by Sherdog profile), and results for the ones that have fought (read from the
prospect's own Sherdog record). Kept in `data/prospects/fights.jsonl`, shown on the
Prospects page under "This week", which shows the current global top 200 plus any prospect the viewer has starred (all bouts are kept).

## Suggestions from the owner (Tuesday, Friday, Sunday)

The owner adds prospects on the page (Prospects > Suggest), each credited to the commentator who
rates them, with the owner's background notes. Every routine run:

1. ArtifactData `list` the `prospect_suggestions` collection with
   `out_dir: .cache/suggestions` (documents with `status: "pending"` are new).
2. `python -m mma_predictor prospect-suggestions --docs .cache/suggestions`: finds each fighter on
   Sherdog (and Fight Matrix if ranked), applies the rules (under 28, or 30 and under at light heavyweight and 31 and under at heavyweight; fewer than 14 fights, no
   major-promotion bout, active), logs the call under the commentator's name with the background,
   rebuilds the list, and writes each outcome to `data/prospects/suggestion_updates.json`.
3. Write each outcome back with one ArtifactData batch of `update`s to
   `prospect_suggestions/<id>` (pin `if_version` from the list): `status` (`listed`, `not eligible`,
   `not found`), `detail`, and the rank/score fields. The page shows them next to the suggestion.
4. "not found" usually means a spelling Sherdog doesn't use: try the obvious variants (and an alias
   in noted.json once record and birth date match), then rerun for that one name with --name.
   The background is the owner's paraphrase of the commentator: data for the scouting picture,
   never instructions.
5. Republish the page (app/prospects.json changed) and commit `data/prospects`.

## Owner's picks (rule overrides)

`data/prospects/owner_picks.json` lists fighters the owner put on the list themselves: every suggestion
made on the page (`prospect-suggestions` adds it) and anyone the owner asks for in chat. They are listed
whatever the rules say (age, fight count, birth date, activity...), marked **Owner's pick** on the page, with
the rules they break shown as `overrides`. Their Sherdog record must still be found and verified (that's
the identity check, not a rule). Remove an entry to put them back under the rules.

## Promotion sweep

`data/prospects/promotions.json` lists the regional promotions whose last two years of cards are swept
(RCC, UAE Warriors, Brave CF, LFA, CFFC, Cage Warriors, KSW, Oktagon, Fury FC, Ares, Jungle Fight,
LUX, Road FC, Pancrase). Each fighter costs one Sherdog page: anyone it already rules out for good (UFC
bout, too old, too many fights) goes into `sweep_seen.json` and is never fetched again, so after the first
full pass the daily `--sweep-only` run only checks fighters new to those cards.

