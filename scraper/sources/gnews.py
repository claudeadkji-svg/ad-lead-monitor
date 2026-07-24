# -*- coding: utf-8 -*-
"""구글뉴스 RSS 키워드 수집 — 키워드는 저장소 루트 keywords.json에서 관리"""
import json
import os
import re
from urllib.parse import quote

from common import get, item

RSS = "https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
PER_QUERY = 8
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_queries():
    try:
        with open(os.path.join(ROOT, "keywords.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        return [(k["검색어"], k["표시명"], k["카테고리"]) for k in cfg.get("뉴스_키워드", [])]
    except Exception:
        return [("광고대행사 선정", "뉴스(대행사 선정)", "신규 캠페인·브랜드")]


def collect():
    items, statuses = [], []
    for q, source, category in load_queries():
        try:
            r = get(RSS.format(q=quote(q)))
            if r.status_code != 200:
                statuses.append(f"{source} HTTP {r.status_code}")
                continue
            blocks = re.findall(r"<item>([\s\S]*?)</item>", r.text)[:PER_QUERY]
            n = 0
            for blk in blocks:
                t = re.search(r"<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</title>", blk)
                l = re.search(r"<link>([\s\S]*?)</link>", blk)
                p = re.search(r"<pubDate>([\s\S]*?)</pubDate>", blk)
                if not (t and l):
                    continue
                title = t.group(1).strip().replace("&amp;", "&").replace("&quot;", '"')
                press = ""
                if " - " in title:
                    title, press = title.rsplit(" - ", 1)
                items.append(item(
                    source, category, title=title, url=l.group(1).strip(),
                    description=f"출처: {press}" if press else "",
                    posted=(p.group(1)[:16] if p else ""),
                ))
                n += 1
            statuses.append(f"{source} {n}건")
        except Exception as e:
            statuses.append(f"{source} 오류:{type(e).__name__}")
    return items, "; ".join(statuses)
