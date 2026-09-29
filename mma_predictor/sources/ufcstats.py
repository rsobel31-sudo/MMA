"""UFCStats.com importer: per-bout striking and grappling stats for UFC fights.

Crawl path: completed-events list -> event pages (date + bout links) ->
fight-details pages (result, method, round, time, format, per-corner
totals) -> fighter-details pages (DOB, height, reach, stance).

Output is a stats-rich dataset in this project's schema. Combine it with a
Sherdog career dataset via ``merge`` (put this one first so its stats and
bios take priority).
"""

from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional, Tuple

from ..data import Method, fight_csv_header, parse_date
from .common import FIGHTER_HEADER, Fetcher, length_cm, method_from_text
from .html import Node, parse_html

EVENTS_URL = "http://ufcstats.com/statistics/events/completed?page=all"
_OF = re.compile(r"(\d+)\s+of\s+(\d+)")


def _label_value(root: Node, label: str) -> str:
    """Text following e.g. 'Method:' inside the fight/fighter details boxes."""
    for node in root.find_all("i", pred=lambda n: label.lower() in n.text().lower()[: len(label) + 2]):
        txt = node.text()
        if ":" in txt:
            return txt.split(":", 1)[1].strip()
    text = root.text()
    m = re.search(re.escape(label) + r":\s*([^:]{1,60}?)(?:\s+[A-Z][A-Za-z. ]+:|$)", text, re.I)
    return m.group(1).strip() if m else ""


def list_events(fetcher: Fetcher, limit: Optional[int] = None) -> List[Tuple[str, str]]:
    """[(event url, event name)] most recent first, completed events only."""
    root = parse_html(fetcher.get(EVENTS_URL))
    out = []
    for a in root.find_all("a", pred=lambda a: "/event-details/" in a.attrs.get("href", "")):
        out.append((a.attrs["href"], a.text()))
    return out[:limit] if limit else out


def parse_event(html: str) -> Tuple[Optional[str], List[str]]:
    root = parse_html(html)
    date_txt = ""
    for li in root.find_all("li", "b-list__box-list-item"):
        t = li.text()
        if t.lower().startswith("date:"):
            date_txt = t.split(":", 1)[1].strip()
    links = []
    for tr in root.find_all("tr", pred=lambda n: "fight-details" in n.attrs.get("data-link", "")):
        links.append(tr.attrs["data-link"])
    if not links:
        links = [a.attrs["href"] for a in root.find_all("a", pred=lambda a: "/fight-details/" in a.attrs.get("href", ""))]
    return date_txt or None, list(dict.fromkeys(links))


def _pair(cell: Node) -> Tuple[str, str]:
    ps = cell.find_all("p")
    if len(ps) >= 2:
        return ps[0].text(), ps[1].text()
    return cell.text(), ""


def _of(txt: str) -> Tuple[int, int]:
    m = _OF.search(txt)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def _clock(txt: str) -> int:
    m = re.search(r"(\d+):(\d{2})", txt)
    return int(m.group(1)) * 60 + int(m.group(2)) if m else 0


def parse_fight(html: str) -> Dict[str, str]:
    root = parse_html(html)
    people = root.find_all("div", "b-fight-details__person")
    if len(people) < 2:
        raise ValueError("fight page without two fighters")
    names, statuses, urls = [], [], []
    for p in people[:2]:
        link = p.find("a") or p.find("h3")
        names.append(link.text() if link else "")
        urls.append(link.attrs.get("href", "") if link else "")
        st = p.find("i", "b-fight-details__person-status")
        statuses.append(st.text().strip().upper() if st else "")
    method_raw = _label_value(root, "Method")
    rnd = re.search(r"\d+", _label_value(root, "Round"))
    time_txt = _label_value(root, "Time")
    fmt = _label_value(root, "Time format")
    sched = re.search(r"(\d)\s*Rnd", fmt)
    title_node = root.find("i", "b-fight-details__fight-title")
    title_txt = title_node.text() if title_node else ""

    if "W" in statuses:
        winner = names[statuses.index("W")]
    elif "D" in statuses:
        winner = "draw"
    else:
        winner = "nc"
    try:
        method = method_from_text(method_raw)
    except ValueError:
        method = Method.NC
    if winner == "draw":
        method = Method.DRAW

    row = {
        "fighter_a": names[0],
        "fighter_b": names[1],
        "winner": winner,
        "method": method.value,
        "round": rnd.group() if rnd else "1",
        "time": re.search(r"\d+:\d{2}", time_txt).group() if re.search(r"\d+:\d{2}", time_txt) else "",
        "scheduled_rounds": sched.group(1) if sched else "3",
        "title_fight": "1" if "title" in title_txt.lower() else "0",
        "weight_class": re.sub(r"\s*(UFC|Title|Bout|Interim|Tournament)\s*", " ", title_txt).strip(),
        "_urls": "|".join(urls),
    }
    # First "Totals" table: Fighter, KD, Sig. str., Sig. str. %, Total str., Td, Td %, Sub. att, Rev., Ctrl
    for table in root.find_all("table"):
        head = [th.text().lower() for th in table.find_all("th")]
        if not head or "kd" not in head or "ctrl" not in head:
            continue
        idx = {h: i for i, h in enumerate(head)}
        body = table.find("tbody") or table
        tr = body.find("tr", pred=lambda n: len(n.child_elements("td")) >= len(head))
        if tr is None:
            continue
        cells = tr.child_elements("td")
        cols = {h: _pair(cells[i]) for h, i in idx.items()}
        for side, px in ((0, "a"), (1, "b")):
            sl, sa = _of(cols.get("sig. str.", ("", ""))[side])
            tl, ta = _of(cols.get("td", ("", ""))[side])
            row.update({
                f"{px}_sig_landed": str(sl), f"{px}_sig_attempted": str(sa),
                f"{px}_td_landed": str(tl), f"{px}_td_attempted": str(ta),
                f"{px}_sub_attempts": re.sub(r"\D", "", cols.get("sub. att", ("0", "0"))[side]) or "0",
                f"{px}_knockdowns": re.sub(r"\D", "", cols.get("kd", ("0", "0"))[side]) or "0",
                f"{px}_ctrl_seconds": str(_clock(cols.get("ctrl", ("", ""))[side])),
            })
        break
    return row


def parse_fighter(html: str, url: str) -> Dict[str, str]:
    root = parse_html(html)
    name_node = root.find("span", "b-content__title-highlight")
    dob_txt = _label_value(root, "DOB")
    try:
        dob = parse_date(dob_txt).isoformat() if dob_txt and dob_txt != "--" else ""
    except ValueError:
        dob = ""
    height = length_cm(_label_value(root, "Height"))
    reach = length_cm(_label_value(root, "Reach").replace('"', ' in'))
    stance = _label_value(root, "STANCE").split()[0] if _label_value(root, "STANCE") else ""
    return {
        "name": name_node.text() if name_node else "",
        "dob": dob,
        "height_cm": f"{height:.1f}" if height else "",
        "reach_cm": f"{reach:.1f}" if reach else "",
        "stance": stance.title() if stance and stance != "--" else "",
        "prior_wins": "0",
        "prior_losses": "0",
        "source": "ufcstats",
        "url": url,
    }


def crawl(fetcher: Fetcher, events: Optional[int] = None, log: Callable[[str], None] = print) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    fights: List[Dict[str, str]] = []
    fighter_urls: Dict[str, str] = {}
    for ev_url, ev_name in list_events(fetcher, events):
        date_txt, links = parse_event(fetcher.get(ev_url))
        if not date_txt:
            continue
        when = parse_date(date_txt).isoformat()
        for link in links:
            try:
                row = parse_fight(fetcher.get(link))
            except (ValueError, OSError) as exc:
                log(f"  skip {link}: {exc}")
                continue
            row.update(date=when, event=ev_name)
            for name, u in zip((row["fighter_a"], row["fighter_b"]), row.pop("_urls").split("|")):
                if u:
                    fighter_urls.setdefault(name, u)
            fights.append(row)
        log(f"  {ev_name} ({when}): {len(links)} bouts")
    fighters = []
    for name, u in fighter_urls.items():
        try:
            f = parse_fighter(fetcher.get(u), u)
        except (ValueError, OSError):
            f = {"name": name}
        f["name"] = name  # keep the spelling used in the fight rows
        fighters.append(f)
    header = fight_csv_header()
    fights = [{k: r.get(k, "") for k in header} for r in sorted(fights, key=lambda r: r["date"])]
    fighters = [{k: f.get(k, "") for k in FIGHTER_HEADER} for f in fighters]
    return fighters, fights
