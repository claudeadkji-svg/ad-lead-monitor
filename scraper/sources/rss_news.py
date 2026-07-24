# -*- coding: utf-8 -*-
"""RSS 기반 업계 뉴스: 모비인사이드, 매드타임스 (최근 N일 이내만)"""
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from common import get, item

CATEGORY = "업계 협회·뉴스"
FEEDS = [
    ("모비인사이드", "https://www.mobiinside.co.kr/feed/"),
    ("매드타임스", "https://www.madtimes.co.kr/rss/allArticle.xml"),
]
TAG_RE = re.compile(r"<[^>]+>")
RECENT_DAYS = 30


def parse_date(pubdate):
    try:
        dt = parsedate_to_datetime(pubdate)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt, dt.astimezone(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    except Exception:
        return None, ""


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
        pub = (it.findtext("pubDate") or "").strip()
        if title and link:
            items.append((title, link, desc, pub))
    return items


def collect():
    cutoff = datetime.now(timezone.utc) - timedelta(days=RECENT_DAYS)
    all_items, statuses = [], []
    for source, url in FEEDS:
        try:
            r = get(url)
            if r.status_code != 200:
                statuses.append(f"{source} HTTP {r.status_code}")
                continue
            picked = []
            for title, link, desc, pub in parse_rss(r.text, source):
                dt, ymd = parse_date(pub)
                # 발행일을 읽을 수 있으면 최근 N일만; 못 읽으면 일단 채택
                if dt is not None and dt < cutoff:
                    continue
                picked.append((dt, title, link, desc, ymd))
            oldest = datetime(1970, 1, 1, tzinfo=timezone.utc)
            picked.sort(key=lambda x: x[0] or oldest, reverse=True)
            for dt, title, link, desc, ymd in picked[:12]:
                head = f"📅 {ymd} · " if ymd else ""
                all_items.append(item(
                    source, CATEGORY, title=title, url=link,
                    description=(head + desc)[:200], posted=ymd,
                ))
            statuses.append(f"{source} {len(picked[:12])}건")
        except Exception as e:
            statuses.append(f"{source} 오류:{type(e).__name__}")
    return all_items, "; ".join(statuses)
