# -*- coding: utf-8 -*-
"""RSS 기반 업계 뉴스: 모비인사이드, 매드타임스"""
import re
import xml.etree.ElementTree as ET

from common import get, item

CATEGORY = "업계 협회·뉴스"
FEEDS = [
    ("모비인사이드", "https://www.mobiinside.co.kr/feed/"),
    ("매드타임스", "https://www.madtimes.co.kr/rss/allArticle.xml"),
]
TAG_RE = re.compile(r"<[^>]+>")


def parse_rss(text, source):
    items = []
    try:
        root = ET.fromstring(text.encode("utf-8"))
    except ET.ParseError:
        # CDATA/엔티티 문제 시 정규식 폴백
        for m in re.finditer(r"<item>([\s\S]*?)</item>", text):
            blk = m.group(1)
            t = re.search(r"<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</title>", blk)
            l = re.search(r"<link>([\s\S]*?)</link>", blk)
            if t and l:
                items.append((t.group(1).strip(), l.group(1).strip(), "", ""))
        return items
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        desc = TAG_RE.sub("", it.findtext("description") or "").strip()
        pub = (it.findtext("pubDate") or "")[:16]
        if title and link:
            items.append((title, link, desc, pub))
    return items


def collect():
    all_items, statuses = [], []
    for source, url in FEEDS:
        try:
            r = get(url)
            if r.status_code != 200:
                statuses.append(f"{source} HTTP {r.status_code}")
                continue
            rows = parse_rss(r.text, source)[:12]
            for title, link, desc, pub in rows:
                all_items.append(item(
                    source, CATEGORY, title=title, url=link,
                    description=desc[:200], posted=pub,
                ))
            statuses.append(f"{source} {len(rows)}건")
        except Exception as e:
            statuses.append(f"{source} 오류:{type(e).__name__}")
    return all_items, "; ".join(statuses)
