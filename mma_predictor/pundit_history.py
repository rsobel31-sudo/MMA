"""Fight Track Record: published fight picks from analysts and outlets, graded against verified results.

Anyone who publishes picks in the open can be on the board: a famous name gets no head start. Every
pick is matched to a bout in our verified results (two sources agree on the winner) and carries the
market's no-vig closing probability for the fighter picked, so the ledger (`reads.Pundits`) can rank
pickers by how far they beat the betting favourite on the same fights, not by raw accuracy: picking
-500 favourites wins often and proves nothing.

Sources (each parser turns one article into (picker, fighter A, fighter B, pick, method) rows; names are
resolved against the event's real bouts, so a surname or a nickname-free short name is enough):

- Sherdog previews (Tom Feely and others): every bout, one page per bout, "the pick is X via ...".
- CBS Sports expert picks: a table, one column per expert, "Van TKO2".
- Cageside Press staff picks: a table whose cells are the picked fighter's headshot (named file).
- Expert grids, one column per picker (RotoWire, and CBS's older layouts): `parse_grid`; ESPN's
  "Expert | Pick | Method" panels: `parse_espn`.
- Staff-pick articles written as "Name: ... Prediction: X by ..." (Bleacher Report, SI's MMA Knockout,
  MMASucka and similar): `parse_staff`.

    python -m mma_predictor scout history --sources sherdog,cageside --since 2025-01-01
"""

from __future__ import annotations

import csv
import html as htmllib
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from urllib.parse import unquote
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .sources.wikipedia import match_key

FIGHTS = Path("data/verified/fights.csv")
ALIASES = Path("data/name_aliases.json")
SOURCES_FILE = Path("data/scouting/pick_sources.json")
NICKNAMES = Path("data/scouting/fighter_nicknames.json")
PENDING = Path("data/scouting/picks_pending.jsonl")  # picks on bouts not yet fought/verified, retried each run

Row = Dict[str, object]


# ------------------------------------------------------------------ text helpers
def text_of(fragment: str) -> str:
    s = re.sub(r"<(script|style|svg|noscript)[^>]*>.*?</\1>", " ", fragment, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</p>|</h\d>|</li>|</div>|</td>|</th>|</tr>", "\n", s, flags=re.I)
    s = htmllib.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"[ \t\r\f\v\xa0]+", " ", s)
    return re.sub(r"\n\s*", "\n", s).strip()


_ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}


def parse_method(s: str) -> Tuple[str, Optional[int]]:
    """'via second-round knockout' -> ('KO/TKO', 2); 'UD' -> ('DEC', None); '' -> ('', None)."""
    t = s.lower()
    m = ""
    if re.search(r"\b(t?ko|tko|knock ?out|stoppage|strikes|punches|ground and pound|doctor)", t) or re.search(r"\b(t?ko)\d", t):
        m = "KO/TKO"
    elif re.search(r"\bsub(mission)?s?\b|\bsub\d|choke|armbar|triangle|guillotine|kimura|heel hook", t):
        m = "SUB"
    elif re.search(r"\b(decision|ud|sd|md|dec|points|judges|scorecards)\b", t):
        m = "DEC"
    rnd = None
    r = re.search(r"\b(first|second|third|fourth|fifth|one|two|three|four|five)[- ]round\b", t) or \
        re.search(r"\b(?:round|rd\.?|r)\s*(\d)\b", t) or re.search(r"\b(?:t?ko|sub)\s*(\d)\b", t)
    if r and m in ("KO/TKO", "SUB"):
        g = r.group(1)
        rnd = int(g) if g.isdigit() else _ORD[g]
    return m, rnd


# ------------------------------------------------------------------ verified bouts
_NOISE = {"by", "via", "the", "and", "vs", "ko", "tko", "sub", "dec", "ud", "sd", "md", "round", "rd", "first", "second", "third",
          "fourth", "fifth", "decision", "unanimous", "split", "majority", "knockout", "submission", "jr", "pick", "png", "jpg",
          "headshot", "ufc", "of", "in", "to", "win", "wins", "c", "ic", "middleweights", "lightweights", "heavyweights"}
class Bouts:
    """Verified bouts with results and closing odds, indexed by date for matching picks to fights."""

    def __init__(self, path: Path = FIGHTS, aliases: Path = ALIASES) -> None:
        self.by_date: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                if r["event"].startswith("UFC") or "Contender" in r["event"]:
                    self.by_date[r["date"]].append(r)
        self.nick_tokens: Dict[str, set] = defaultdict(set)  # what pickers call fighters: 'BSD', 'Suga', 'MVP'
        nicks = json.loads(NICKNAMES.read_text()) if NICKNAMES.exists() else {}
        for k, v in nicks.items():
            if not k.startswith("_"):
                self.nick_tokens[v] |= set(match_key(k).split())
        al = json.loads(Path(aliases).read_text()) if Path(aliases).exists() else {}
        self.alias_tokens: Dict[str, set] = defaultdict(set)  # Sherdog name -> tokens of other spellings
        for k, v in al.items():
            if not k.startswith("_"):
                self.alias_tokens[v] |= set(match_key(k).split())

    def window(self, published: str, before: int = 1, after: int = 9) -> List[Dict[str, str]]:
        d0 = date.fromisoformat(published[:10])
        out = []
        for i in range(-before, after + 1):
            out += self.by_date.get((d0 + timedelta(days=i)).isoformat(), [])
        return out

    def tokens(self, name: str) -> set:
        return set(match_key(name).split()) | self.alias_tokens.get(name, set()) | self.nick_tokens.get(name, set())

    def hits(self, frag: str, fighter: str) -> int:
        """How well a written name matches a fighter: 2 for the full name, 1 for a distinctive token, 0 for none."""
        ft = [t for t in match_key(frag).split() if len(t) > 1 and t not in _NOISE]
        mine = self.tokens(fighter)
        if not ft:
            return 0
        common = [t for t in ft if t in mine or (len(t) > 3 and any(len(m) > 3 and SequenceMatcher(None, t, m).ratio() >= 0.8 for m in mine))]
        if len(common) == len(ft) and len(ft) > 1:
            return 2
        return 1 if common else 0

    def find(self, cands: List[Dict[str, str]], a: str, b: str = "") -> Optional[Dict[str, str]]:
        """The bout two written names (or one, if unique) refer to."""
        best, score = None, 0
        for r in cands:
            fa, fb = r["fighter_a"], r["fighter_b"]
            if b:
                s = max(min(self.hits(a, fa), self.hits(b, fb)), min(self.hits(a, fb), self.hits(b, fa)))
            else:
                s = max(self.hits(a, fa), self.hits(a, fb))
            if s > score:
                best, score = r, s
            elif s == score and s and best is not None and best is not r and not b:
                best = None if score == 1 else best  # ambiguous single surname
        return best if score else None

    def side(self, frag: str, bout: Dict[str, str]) -> Optional[str]:
        ha, hb = self.hits(frag, bout["fighter_a"]), self.hits(frag, bout["fighter_b"])
        if ha > hb:
            return bout["fighter_a"]
        if hb > ha:
            return bout["fighter_b"]
        return None


def novig(a_odds: str, b_odds: str) -> Optional[float]:
    """Market probability that fighter A wins, without the bookmaker's margin."""
    try:
        oa, ob = float(a_odds), float(b_odds)
    except (TypeError, ValueError):
        return None
    imp = lambda o: 100 / (o + 100) if o > 0 else -o / (-o + 100)  # noqa: E731
    pa, pb = imp(oa), imp(ob)
    return round(pa / (pa + pb), 3)


def to_row(B: Bouts, bout: Dict[str, str], outlet: str, author: str, pick: str, method: str, rnd: Optional[int],
           url: str, published: str) -> Row:
    a, b = bout["fighter_a"], bout["fighter_b"]
    pa = novig(bout.get("a_odds", ""), bout.get("b_odds", ""))
    row: Row = {"event": bout["event"], "date": bout["date"], "a": a, "b": b, "outlet": outlet, "author": author,
                "pick": pick, "method": (method + (f" R{rnd}" if rnd else "")).strip(), "pick_method": method,
                "pick_round": rnd, "url": url, "published": published[:10],
                "p_market": None if pa is None else (pa if pick == a else round(1 - pa, 3))}
    w, res = bout.get("winner") or "", bout.get("method", "")
    if w in (a, b) and res not in ("NC", "DRAW"):
        rm = "DEC" if res in ("DEC", "S-DEC") else res if res in ("KO/TKO", "SUB") else "OTHER"
        row.update({"winner": w, "grade": "won" if pick == w else "lost", "result_method": rm,
                    "result_round": int(bout["round"]) if str(bout.get("round", "")).isdigit() else None})
        if method:
            row["method_correct"] = pick == w and method == rm
    else:
        row.update({"winner": None, "grade": "void"})
    return row


# ------------------------------------------------------------------ parsers
def parse_sherdog(page: str) -> List[Tuple[str, str, str, str]]:
    """One Sherdog preview page -> [(author, fighter A, fighter B, pick sentence)]."""
    flat = re.sub(r"\s*\n\s*", " ", text_of(page))
    au = re.search(r"/authors/([A-Za-z-]+)-\d+", page)
    author = au.group(1).replace("-", " ") if au else ""
    rec = r"\(\d+-\d+[^)]{0,30}\)"  # (10-1), (36-17-1, 1 N/C), (12-3, 1 NC)
    vs = re.search(r"([^()]{2,120}?) " + rec + r" vs\. ([^()]{2,60}?) " + rec, flat)
    end = flat.find("Jump To")
    body = flat[:end] if end > 0 else flat
    picks = re.findall(r"[Tt]he pick is ([^.;]{2,300})[.;]", body)
    pick = picks[-1] if picks else None
    if not pick or not re.match(r"[A-Z]", pick):  # free-form endings: "The pick is that Todorovic ...",
        tail = body[-600:]  # "look for Stirling to ...", "I lean slightly towards Janicic", "Blachowicz via KO"
        nm = r"((?:[A-Z][\w'’.-]+ ){0,2}[A-Z][\w'’.-]+)"
        found = []
        for rx in (r"[Tt]he pick is (?:that )?" + nm, r"\blean(?:s|ing)?(?: slightly| a bit)? (?:towards?|to|with) " + nm,
                   r"[Ll]ook for " + nm + r" to\b", r"(?:side|go|going) with " + nm, nm + r" (?:via|by|wins via|wins by)\b"):
            found += [(m.start(), m.group(1)) for m in re.finditer(rx, tail)]
        if found:
            pos, who = max(found)
            pick = f"{who} via {tail[pos:]}"
    if not pick:
        return []
    if not vs:  # main events are written as prose: the bout is in the page title, "Preview: ... - Song vs. Figueiredo"
        tt = re.search(r"<title>[^<]*? - ([^<]+?) vs\.? ([^<]+?)\s*(?:\||</title>)", page)
        return [(author, htmllib.unescape(tt.group(1)).strip(), htmllib.unescape(tt.group(2)).strip(), pick)] if tt else []
    a = vs.group(1)
    a = re.split(r"\b\d{4}\b|Odds|Advertisement", a)[-1]  # drop the byline and date before the names
    a = re.sub(r"^\s*(?:(?:Women's |Light |Super )?\w+weights?|Catchweight|Catch Weight)\s+", "", a.strip(), flags=re.I)
    return [(author, a.strip(), vs.group(2).strip(), pick)]


def split_pick(s: str) -> Tuple[str, str]:
    """'Pinas via second-round knockout' -> ('Pinas', 'via second-round knockout')."""
    m = re.match(r"\s*(.+?)\s+(?:via|by|wins by|to win by|in|with|,)\s+(.*)$", s)
    if m:
        return m.group(1), m.group(2)
    m = re.match(r"\s*(.+?)\s+((?:T?KO|TKO|Sub|SUB|UD|SD|MD|Dec|DEC)\d?\b.*)$", s)
    return (m.group(1), m.group(2)) if m else (s.strip(), "")


def parse_cbs(page: str) -> List[Tuple[str, str, str, str]]:
    """CBS Sports expert-picks table -> [(expert, fighter A, fighter B, 'Van TKO2')]. Experts' full names from the byline/text."""
    i = page.find("<table")
    if i < 0:
        return []
    tb = page[i:page.find("</table>", i)]
    rows = [[text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)] for r in re.findall(r"<tr.*?</tr>", tb, re.S)]
    if not rows or len(rows[0]) < 2:
        return []
    body = text_of(page)
    names = []
    for sur in rows[0][1:]:
        m = re.search(r"\b([A-Z][a-z]+(?:-[A-Z][a-z]+)?) " + re.escape(sur) + r"\b", body)
        names.append(f"{m.group(1)} {sur}" if m else sur)
    out = []
    for r in rows[1:]:
        if len(r) != len(rows[0]) or " vs" not in r[0]:
            continue
        a, b = re.split(r"\s+vs\.?\s+", re.sub(r"\((?:c|ic)\)", "", r[0]), maxsplit=1)
        for name, cell in zip(names, r[1:]):
            if cell:
                out.append((name, a.strip(), b.strip(), cell))
    return out


def parse_cageside(content: str) -> List[Tuple[str, str, str, str]]:
    """Cageside Press staff-picks table (cells are the picked fighter's headshot) -> [(writer, A, B, image name)]."""
    out = []
    for tb in re.findall(r"<table.*?</table>", content, re.S):
        trs = re.findall(r"<tr.*?</tr>", tb, re.S)
        if not trs:
            continue
        head = [text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", trs[0], re.S)]
        bouts = [re.split(r"\s+vs\.?\s+", re.sub(r"\s+\d+$", "", h), maxsplit=1) for h in head[1:]]
        for tr in trs[1:]:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            if len(cells) != len(head):
                continue
            writer = re.sub(r"\s*\(\d+-\d+(?:-\d+)?\)\s*$", "", text_of(cells[0])).strip()
            for bt, cell in zip(bouts, cells[1:]):
                img = re.search(r'src="([^"]+)\.(?:png|jpe?g|webp)', cell)
                pick = unquote(unquote(img.group(1))).rsplit("/", 1)[-1] if img else text_of(cell)
                pick = re.sub(r"[-_]+", " ", re.sub(r"(?i)headshot|[0-9a-f]{8,}|\d+x\d+|_\d\d-\d\d|scaled", " ", pick))
                if len(bt) == 2 and pick.strip():
                    out.append((writer, bt[0], bt[1], pick))
    return out


def _cells(tr: str) -> List[str]:
    return [text_of(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]


def _full_name(word: str, body: str) -> str:
    """A table header ('Campbell', 'JON', 'Joe "SunTszu"') -> the person's name as the article writes it."""
    w = re.sub(r'["“”].*?["“”]', "", word).strip()
    nick = re.search(r'["“”]([^"“”]+)["“”]', word)
    if not w and nick:
        return nick.group(1)
    w = w.title() if w.isupper() else w
    if nick:  # a handle is how this picker is known: 'Joe "SunTszu"' (spelled as the article's text has it)
        nm = re.search(re.escape(nick.group(1).strip()), body[body.find("EXPERTS"):] if "EXPERTS" in body else body, re.I)
        return f'{w} "{nm.group(0) if nm else nick.group(1).strip()}"'.strip()
    m = re.search(r"\b(" + re.escape(w) + r" [A-Z][a-z]+(?:-[A-Z][a-z]+)?)\s*:", body) or \
        re.search(r"\b([A-Z][a-z]+(?:-[A-Z][a-z]+)? " + re.escape(w) + r")\b", body) or \
        re.search(r"\b(" + re.escape(w) + r" [A-Z][a-z]+(?:-[A-Z][a-z]+)?)\b", body)
    return m.group(1) if m else (w + (f" ({nick.group(1)})" if nick else ""))


def parse_grid(page: str, byline_name: str = "") -> List[Tuple[str, str, str, str]]:
    """Expert-grid tables (CBS Sports, RotoWire, ...): one row per bout ('A vs. B' in some column), one column per
    picker. A picker column is one whose cells name a fighter of that row's bout on most rows."""
    body = text_of(page)
    out = []
    for tb in re.findall(r"<table.*?</table>", page, re.S):
        trs = re.findall(r"<tr.*?</tr>", tb, re.S)
        if len(trs) < 2:
            continue
        head = _cells(trs[0])
        rows = [_cells(tr) for tr in trs[1:]]
        bouts = []
        for r in rows:
            k = next((i for i, c in enumerate(r) if re.search(r"\bvs\.?\s", c)), None)
            if k is not None and len(r) == len(head):
                a, b = re.split(r"\s+vs\.?\s+", re.sub(r"\((?:c|ic)\)|\([+-]\d+\)", "", r[k]), maxsplit=1)
                bouts.append((r, a.strip(), b.strip(), k))
        if not bouts:
            continue
        for j, h in enumerate(head):
            if not h.strip() or any(j == k for _, _, _, k in bouts[:1]):
                continue
            named = [(r[j], a, b) for r, a, b, _ in bouts if r[j]]
            surn = lambda x: {t for t in match_key(x).split() if len(t) > 2}  # noqa: E731
            hits = [c for c, a, b in named if surn(c) & (surn(a) | surn(b))]
            if len(named) and len(hits) >= max(1, 0.6 * len(named)):
                if re.fullmatch(r"(?i)\s*(prediction|pick|winner|my pick)\s*", h):  # one writer's table: credit the byline
                    if not byline_name:
                        continue
                    who = byline_name
                else:
                    who = _full_name(h, body)
                out += [(who, a, b, c) for c, a, b in named]
    return out


def parse_espn(page: str) -> List[Tuple[str, str, str, str]]:
    """ESPN panels: per bout a table 'Expert | Pick | Method'; the bout is whichever one the pick names."""
    out = []
    for tb in re.findall(r"<table.*?</table>", page, re.S):
        trs = re.findall(r"<tr.*?</tr>", tb, re.S)
        if not trs or [c.lower() for c in _cells(trs[0])][:2] != ["expert", "pick"]:
            continue
        for tr in trs[1:]:
            c = _cells(tr)
            if len(c) >= 2 and c[1]:
                name = c[0].split("\n")[0].strip()
                out.append((name, c[1], "", c[1] + (" by " + c[2] if len(c) > 2 and c[2] else "")))
    return out


def parse_numbered_grid(content: str) -> List[Tuple[str, str, str, str]]:
    """Pools whose rows are 'Fight #1', 'Fight #2'... with each picker's surname pick (MMAOddsBreaker):
    the bout is found from the names picked on that row."""
    out = []
    for tb in re.findall(r"<table.*?</table>", content, re.S):
        trs = re.findall(r"<tr.*?</tr>", tb, re.S)
        if len(trs) < 2:
            continue
        head = _cells(trs[0])
        for tr in trs[1:]:
            c = _cells(tr)
            if len(c) != len(head) or not re.match(r"(?i)(fight|bout)\s*#?\s*\d+", c[0]):
                continue
            names = list(dict.fromkeys(x.strip() for x in c[1:] if x.strip()))
            fa, fb = (names + [""])[:2] if len(names) <= 2 else ("", "")
            if not fa:
                continue
            out += [(w.strip(), fa, fb, x.strip()) for w, x in zip(head[1:], c[1:]) if x.strip() and w.strip()]
    return out


def parse_over(page: str, author: str) -> List[Tuple[str, str, str, str]]:
    """'MW: Brendan Allen (4) over Christian Duncan (13)' lines (MMA Intel's full-card predictions)."""
    out = []
    for m in re.finditer(r"^(?:[A-Z]{1,5}:\s*)?([A-Z][^()\n]{2,40}?)\s*(?:\([^)]*\))?\s+over\s+([A-Z][^()\n]{2,40}?)\s*(?:\([^)]*\))?\s*$",
                         text_of(page), re.M):
        out.append((author, m.group(1).strip(), m.group(2).strip(), m.group(1).strip()))
    return out


_PRED = re.compile(r"(?:Prediction|Pick|Official pick|My pick|Verdict)\s*:\s*([^\n)]{2,120})", re.I)
_NAME = re.compile(r"^([A-Z][\w'.À-ſ-]+(?: [A-Z][\w'.À-ſ-]+){0,2})\s*:\s*(.*)$")
_NOT_WRITER = r"(?i)^(prediction|pick|odds|records?|staff|note|official|verdict|result|method|round|editor|photo|related|read|also|update|my pick|the pick|bet|best bet|lean|weight|why)\b"


def bylines(page: str) -> List[str]:
    """The article's credited writers (structured data first, then the author meta tag)."""
    names: List[str] = []
    for blk in re.findall(r'"author"\s*:\s*(\[[^\]]*\]|\{[^}]*\})', page)[:3]:
        names += re.findall(r'"name"\s*:\s*"([^"]+)"', blk)
    if not names:
        m = re.search(r'<meta[^>]+name="author"[^>]+content="([^"]+)"', page)
        names = re.split(r"\s*(?:,|\band\b|&)\s*", m.group(1)) if m else []
    out = []
    for n in names:
        n = htmllib.unescape(n).strip()
        if n and n not in out and " " in n and not re.search(r"(?i)staff|editor|team|\.com|news|sports|unknown", n):
            out.append(n)
    return out


def parse_staff(page: str, B: Bouts, cands: List[Dict[str, str]], default_writer: str = "") -> List[Tuple[str, str, str, str]]:
    """Staff-pick articles: a bout heading, then 'Writer:' paragraphs each ending in a pick.
    The current bout is the last line naming both fighters of a real bout on the card. An article with no
    'Writer:' lines at all is one person's picks: credited to `default_writer` (the byline), if given."""
    names = bylines(page)
    got = _parse_staff(page, B, cands, "", names)
    if got or not default_writer:
        return got
    return _parse_staff(page, B, cands, default_writer, names)


def _parse_staff(page: str, B: Bouts, cands: List[Dict[str, str]], default_writer: str, credited: List[str] = ()) -> List[Tuple[str, str, str, str]]:
    raw = [re.sub(r"^-->\s*", "", l).strip() for l in text_of(page).split("\n")]
    lines: List[str] = []
    for l in raw:
        if not l or (lines and l == lines[-1]):
            continue
        if lines and re.fullmatch(r"(?i)vs\.?", lines[-1]) and len(lines) > 1:  # "Name -245 / Vs. / Name +205"
            lines.pop()
            l = lines.pop() + " vs. " + l
        lines.append(re.sub(r"\s+[+-]\d{3,5}\b", "", l) if " vs" in l.lower() else l)
    out, seen, full = [], set(), {}
    for n in credited:  # "Mat:" in the text is "Mathew Riddle" in the byline
        full.setdefault(n.split()[0], n)
    bout, writer, buf = None, None, []

    def flush():
        if not (bout and writer):
            return
        txt = "\n".join(buf)
        m = _PRED.search(txt) or re.search(r"^([A-Z][\w'.-]+(?: [A-Z][\w'.-]+)?) (?:by|via) ([^\n]{2,80})$", txt, re.M)
        pick = None
        if m and m.re is _PRED:
            pick = m.group(1)
        elif m:
            pick = f"{m.group(1)} by {m.group(2)}"
        elif len(buf) <= 2 and buf and re.search(r"\b(by|via)\b", buf[0]):
            pick = buf[0]
        if pick and (writer, bout["fighter_a"], bout["fighter_b"]) not in seen:
            seen.add((writer, bout["fighter_a"], bout["fighter_b"]))
            out.append((writer, bout["fighter_a"], bout["fighter_b"], pick))

    for l in lines:
        vs = re.match(r"^(.{3,50}?)\s+vs\.?\s+(.{3,60}?)(?:\s+(?:II|2|3|Predictions?|Prediction & Pick))?$", l)
        if vs and len(l) < 110:
            bt = B.find(cands, vs.group(1), vs.group(2))
            if bt:
                flush()
                bout, writer, buf = bt, (default_writer or None), []
                continue
        nm = _NAME.match(l)
        if nm and bout and not re.match(_NOT_WRITER, nm.group(1)):
            name = nm.group(1)
            if " " in name:
                full.setdefault(name.split()[0], name)
            elif name in full or any(k.startswith(name) and len(name) >= 3 for k in full):
                name = full.get(name) or next(v for k, v in full.items() if k.startswith(name))
            else:
                nm = None
            if nm:
                flush()
                writer, buf = name, ([nm.group(2)] if nm.group(2) else [])
                continue
        if writer is not None:
            buf.append(l)
    flush()
    return out


# ------------------------------------------------------------------ assembling rows
def resolve(B: Bouts, raw: Iterable[Tuple[str, str, str, str]], outlet: str, url: str, published: str,
            cands: Optional[List[Dict[str, str]]] = None, pending: Optional[List[Dict[str, str]]] = None) -> Tuple[List[Row], List[str]]:
    """Parsed picks -> ledger rows; picks we can't tie to one real bout and one fighter are reported, not guessed.
    With `pending`, picks on bouts not in the verified results yet are kept there to be graded on a later run."""
    cands = cands if cands is not None else B.window(published)
    rows, skipped = [], []
    for author, fa, fb, pick_text in raw:
        bout = B.find(cands, fa, fb)
        if not bout:
            skipped.append(f"{author}: no verified bout for {fa} vs {fb}")
            if pending is not None and fb:
                pending.append({"author": author, "a": fa, "b": fb, "pick": pick_text, "outlet": outlet, "url": url, "published": published[:10]})
            continue
        who, how = split_pick(pick_text)
        side = B.side(who, bout) or B.side(pick_text, bout)
        if not side:
            skipped.append(f"{author}: can't tell who '{pick_text}' means in {bout['fighter_a']} vs {bout['fighter_b']}")
            continue
        method, rnd = parse_method(how or pick_text)
        rows.append(to_row(B, bout, outlet, author.strip(), side, method, rnd, url, published))
    return rows, skipped


# ------------------------------------------------------------------ finding articles
def published_of(page: str) -> str:
    m = re.search(r'(?:article:published_time|datePublished|"pubdate"|publish-date)"?\s*(?:content=|:)\s*"(\d{4}-\d{2}-\d{2})', page)
    if m:
        return m.group(1)
    from .sources.common import find_date
    d = find_date(text_of(page)[:4000])
    return d.isoformat() if d else ""


def discover(fetcher, source: str, since: str) -> List[Dict[str, str]]:
    """Article URLs for one source, newest first, back to `since` (as far as the outlet's own listings go)."""
    out: List[Dict[str, str]] = []
    if source == "sherdog":
        for n in range(1, 60):
            page = fetcher.get("https://www.sherdog.com/tag/previews" + (f"/list/{n}" if n > 1 else ""), fresh=n <= 2)
            links = sorted(set(re.findall(r'href="(/news/articles/Preview-(?:UFC|Noche)[^"]+)"', page)))
            dates = [d for d in re.findall(r"([A-Z][a-z]{2} \d{1,2}, \d{4})", text_of(page))]
            out += [{"outlet": "Sherdog", "url": "https://www.sherdog.com" + l} for l in links]
            from .sources.common import parse_date
            ds = []
            for d in dates:
                try:
                    ds.append(parse_date(d))
                except ValueError:
                    pass
            if not links or (ds and min(ds).isoformat() < since):
                break
    elif source == "cageside":
        for n in range(1, 10):
            try:
                d = json.loads(fetcher.get(f"https://cagesidepress.com/wp-json/wp/v2/posts?search=staff%20picks&per_page=100&page={n}"
                                           "&_fields=link,date,title", fresh=n == 1))
            except Exception:  # past the last page
                break
            if not isinstance(d, list) or not d:
                break
            out += [{"outlet": "Cageside Press", "url": x["link"], "published": x["date"][:10]} for x in d
                    if x["date"][:10] >= since and re.search(r"ufc|noche|tuf|contender", x["link"])]
            if d[-1]["date"][:10] < since:
                break
    elif source == "mmasucka":
        for n in (1, 2, 3):
            try:
                xml = fetcher.get(f"https://mmasucka.com/sitemap-predictions-{n}.xml", fresh=True)
            except Exception:
                break
            for loc, mod in re.findall(r"<loc>([^<]+)</loc>\s*(?:<lastmod>([^<]+)</lastmod>)?", xml):
                if "staff-picks" in loc and re.search(r"ufc|noche", loc) and (not mod or mod[:10] >= since):
                    out.append({"outlet": "MMASucka", "url": loc})
    elif source == "bleacher":
        y, m = date.today().year, date.today().month
        while f"{y}-{m:02d}" >= since[:7]:
            xml = fetcher.get(f"https://bleacherreport.com/sitemaps/articles/{y}-{m:02d}", cache=True, fresh=(y, m) == (date.today().year, date.today().month))
            out += [{"outlet": "Bleacher Report", "url": u} for u in re.findall(r"<loc>([^<]+)</loc>", xml)
                    if "ufc" in u and re.search(r"staff-(?:predictions|picks)", u)]
            y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    elif source == "oddsbreaker":  # WordPress API, content inline; robots.txt asks for 10 s between requests
        for n in range(1, 30):
            try:
                d = json.loads(fetcher.get("https://www.mmaoddsbreaker.com/wp-json/wp/v2/posts?search=staff%20picks&per_page=20"
                                           f"&page={n}&_fields=link,date,content", fresh=n == 1))
            except Exception:
                break
            if not isinstance(d, list) or not d:
                break
            out += [{"outlet": "MMAOddsBreaker", "url": x["link"], "published": x["date"][:10], "content": x["content"]["rendered"]}
                    for x in d if x["date"][:10] >= since and "staff-picks" in x["link"]]
            if d[-1]["date"][:10] < since:
                break
    elif source == "mmaintel":  # upcoming cards only (old picks are taken down): recorded weekly, graded once fought
        out.append({"outlet": "MMA Intel", "url": "https://mmaintel.blog/upcoming-ufc-predictions/", "published": date.today().isoformat()})
    elif source == "rotowire":
        xml = fetcher.get("https://www.rotowire.com/mma_articles.xml", fresh=True)
        out += [{"outlet": "RotoWire", "url": u} for u in re.findall(r"<loc>([^<]+)</loc>", xml) if "expert-picks" in u]
    for a in json.loads(SOURCES_FILE.read_text()).get("articles", []) if SOURCES_FILE.exists() else []:
        if a.get("source", "").lower() == source or (source == "staff" and a.get("source", "").lower() == "espn"):
            out.append(a)
    seen, uniq = set(), []
    for a in out:
        if a["url"] not in seen:
            seen.add(a["url"])
            uniq.append(a)
    return uniq


PARSERS = {"sherdog": "sherdog", "cageside": "cageside", "cbs": "cbs"}


def harvest(fetcher, B: Bouts, art: Dict[str, str], source: str, pending: Optional[List[Dict[str, str]]] = None) -> Tuple[List[Row], List[str]]:
    """Fetch one article (all its pages) and turn it into graded ledger rows."""
    url = art["url"]
    if source == "oddsbreaker":
        return resolve(B, parse_numbered_grid(art.get("content", "")), art["outlet"], url, art["published"], pending=pending)
    if source == "mmaintel":
        return resolve(B, parse_over(fetcher.get(url, fresh=True), "MMA Intel"), art["outlet"], url, art["published"], pending=pending)
    if source == "cageside":
        slug = url.rstrip("/").split("/")[-1]
        d = json.loads(fetcher.get(f"https://cagesidepress.com/wp-json/wp/v2/posts?slug={slug}&_fields=content,date"))
        if not d:
            return [], [f"{url}: not found"]
        pub = d[0]["date"][:10]
        return resolve(B, parse_cageside(d[0]["content"]["rendered"]), art["outlet"], url, pub)
    if source == "sherdog":
        first = fetcher.get(url)
        pub = published_of(first)
        slug = url.split("/news/articles/")[-1].split("/")[-1]
        pages = sorted({int(n) for n in re.findall(r"/news/articles/(\d+)/" + re.escape(slug), first)} | {1})
        rows, sk = [], []
        for n in pages:
            page = fetcher.get(f"https://www.sherdog.com/news/articles/{n}/{slug}")
            r, s = resolve(B, parse_sherdog(page), art["outlet"], f"https://www.sherdog.com/news/articles/{n}/{slug}", pub)
            rows += r
            sk += s or ([] if r else [f"{slug} p{n}: no pick found"])
        return rows, sk
    page = fetcher.get(url)
    pub = art.get("published") or published_of(page)
    if not pub:
        return [], [f"{url}: no publish date"]
    if "<table" in page:  # expert grids (CBS, RotoWire) and ESPN's panels
        names = bylines(page)
        raw = parse_cbs(page) if source == "cbs" else parse_grid(page, names[0] if len(names) == 1 else "") + parse_espn(page)
        rows = resolve(B, raw, art["outlet"], url, pub, pending=pending)
        if rows[0]:
            return rows
    cands = B.window(pub)
    names = bylines(page)
    return resolve(B, parse_staff(page, B, cands, names[0] if len(names) == 1 else ""), art["outlet"], url, pub, cands, pending)


def cmd_history(args) -> int:
    """Collect published picks from the outlets' archives into the pundit ledger, graded."""
    from .picks_cli import _fetcher
    from .reads import Pundits

    fetcher = _fetcher(args.cache)
    from .sources.common import Fetcher
    slow = Fetcher(Path(args.cache), delay=10.0, user_agent=fetcher.user_agent)  # sites whose robots.txt sets Crawl-delay: 10
    B = Bouts()
    pun = Pundits()
    added = graded = 0
    pend: List[Dict[str, str]] = []
    old = [json.loads(l) for l in PENDING.read_text().splitlines() if l.strip()] if PENDING.exists() else []
    for p in old:  # last weeks' picks on bouts that have since been fought and verified
        rows, _ = resolve(B, [(p["author"], p["a"], p["b"], p["pick"])], p["outlet"], p["url"], p["published"],
                          B.window(p["published"], after=60))
        for r in rows:
            added += pun.add(r)
            graded += r["grade"] in ("won", "lost")
        if not rows and p["published"] >= (date.today() - timedelta(days=60)).isoformat():
            pend.append(p)
    for source in [s.strip() for s in args.sources.split(",") if s.strip()]:
        fx = slow if source == "oddsbreaker" else fetcher
        arts = discover(fx, source, args.since)
        if args.limit:
            arts = arts[: args.limit]
        print(f"{source}: {len(arts)} articles", flush=True)
        n_rows, skipped = 0, 0
        for art in arts:
            try:
                rows, sk = harvest(fx, B, art, source, pend)
            except Exception as e:  # one bad page never stops the run
                print(f"  ! {art['url']}: {e}", flush=True)
                continue
            rows = [r for r in rows if str(r["date"]) >= args.since]
            for r in rows:
                added += pun.add(r)
                graded += r["grade"] in ("won", "lost")
            n_rows += len(rows)
            skipped += len(sk)
            if args.verbose:
                for s in sk:
                    print("   skip", s)
        print(f"  {n_rows} picks ({skipped} skipped: no verified bout yet, or the pick couldn't be read)", flush=True)
        pun.save()
    keep = {(p["author"], p["a"], p["b"], p["outlet"]): p for p in pend if p["published"] >= (date.today() - timedelta(days=60)).isoformat()}
    PENDING.write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in keep.values()))
    print(f"{added} new picks, {graded} graded; {len(keep)} picks waiting for their bouts")
    for s in pun.scoreboard()[:40]:
        print(f"  {s['outlet']:<16} {s['author']:<22} {s['correct']:>3}/{s['picks']:<3} ({s['accuracy']:.0%}; market {s['expected'] or 0:.0%}) z {s['z']:+.2f} ×{s['weight']}")
    return 0
