# -*- coding: utf-8 -*-
"""구글뉴스 RSS 키워드 수집 — 키워드는 저장소 루트 keywords.json에서 관리

구글뉴스 RSS는 기본이 '관련도순'이라 오래된 기사가 섞인다.
→ 검색어에 when:{N}d 필터를 붙이고, 발행일을 파싱해 최근 N일 이내만 최신순으로 남긴다.
"""
import json
import os
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote

from common import get, item

RSS = "https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
RECENT_DAYS = 30          # 이 기간 이내 기사만 채택
PER_QUERY = 8             # 키워드별 최대 채택 건수
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_queries():
    try:
        with open(os.path.join(ROOT, "keywords.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        return [(k["검색어"], k["표시명"], k["카테고리"]) for k in cfg.get("뉴스_키워드", [])]
    except Exception:
        return [("광고대행사 선정", "뉴스(대행사 선정)", "신규 캠페인·브랜드")]


def parse_date(pubdate):
    """RFC822 pubDate → (aware datetime, 'YYYY-MM-DD'). 실패 시 (None, '')"""
    try:
        dt = parsedate_to_datetime(pubdate)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt, dt.astimezone(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    except Exception:
        return None, ""


def collect():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=RECENT_DAYS)
    items, statuses = [], []

    for q, source, category in load_queries():
        query = f"{q} when:{RECENT_DAYS}d"
        try:
            r = get(RSS.format(q=quote(query)))
            if r.status_code != 200:
                statuses.append(f"{source} HTTP {r.status_code}")
                continue
            blocks = re.findall(r"<item>([\s\S]*?)</item>", r.text)
            picked = []
            for blk in blocks:
                t = re.search(r"<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</title>", blk)
                l = re.search(r"<link>([\s\S]*?)</link>", blk)
                p = re.search(r"<pubDate>([\s\S]*?)</pubDate>", blk)
                if not (t and l):
                    continue
                dt, ymd = parse_date(p.group(1).strip()) if p else (None, "")
                # 발행일을 못 읽거나 기간을 벗어나면 제외
                if dt is None or dt < cutoff:
                    continue
                title = t.group(1).strip().replace("&amp;", "&").replace("&quot;", '"')
                press = ""
                if " - " in title:
                    title, press = title.rsplit(" - ", 1)
                picked.append((dt, title, l.group(1).strip(), press, ymd))
            # 최신순 정렬 후 상위 N건
            picked.sort(key=lambda x: x[0], reverse=True)
            for dt, title, url, press, ymd in picked[:PER_QUERY]:
                desc = f"📅 {ymd}" + (f" · 출처: {press}" if press else "")
                items.append(item(source, category, title=title, url=url,
                                  description=desc, posted=ymd))
            statuses.append(f"{source} {len(picked[:PER_QUERY])}건")
        except Exception as e:
            statuses.append(f"{source} 오류:{type(e).__name__}")
    return items, "; ".join(statuses)
