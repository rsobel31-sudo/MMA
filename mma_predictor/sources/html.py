"""A tiny tolerant DOM built on the standard-library HTML parser."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Callable, Dict, Iterator, List, Optional

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Node:
    def __init__(self, tag: str, attrs: Dict[str, str], parent: Optional["Node"] = None) -> None:
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: List["Node | str"] = []

    @property
    def classes(self) -> List[str]:
        return (self.attrs.get("class") or "").split()

    def text(self, sep: str = " ") -> str:
        parts: List[str] = []
        for c in self.children:
            parts.append(c if isinstance(c, str) else c.text(sep))
        return " ".join(sep.join(parts).split())

    def iter(self) -> Iterator["Node"]:
        for c in self.children:
            if isinstance(c, Node):
                yield c
                yield from c.iter()

    def find_all(self, tag: Optional[str] = None, cls: Optional[str] = None, pred: Optional[Callable[["Node"], bool]] = None) -> List["Node"]:
        out = []
        for n in self.iter():
            if tag and n.tag != tag:
                continue
            if cls and cls not in n.classes:
                continue
            if pred and not pred(n):
                continue
            out.append(n)
        return out

    def find(self, tag: Optional[str] = None, cls: Optional[str] = None, pred: Optional[Callable[["Node"], bool]] = None) -> Optional["Node"]:
        found = self.find_all(tag, cls, pred)
        return found[0] if found else None

    def child_elements(self, tag: Optional[str] = None) -> List["Node"]:
        return [c for c in self.children if isinstance(c, Node) and (tag is None or c.tag == tag)]


class _Builder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {})
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: v or "" for k, v in attrs}, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, {k: v or "" for k, v in attrs}, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent  # tolerate unclosed tags
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        if data.strip():
            self.cur.children.append(data)


def parse_html(html: str) -> Node:
    b = _Builder()
    b.feed(html)
    b.close()
    return b.root
