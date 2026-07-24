# -*- coding: utf-8 -*-
"""구글뉴스 RSS 키워드 수집 — 신규 캠페인/브랜드, 올리브영, 병원/프랜차이즈/커머스 등

TVCF·올리브영처럼 직접 크롤링이 어려운 영역을 뉴스 키워드로 보완합니다.
"""
import re
from urllib.parse import quote

from common import get, item

RSS = "https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"

# (검색어, 소스표시명, 카테고리)
QUERIES = [
    ("광고대행사 선정 OR 마케팅 대행사 선정", "뉴스(대행사 선정)", "신규 캠페인·브랜드"),
    ("신규 광고 캠페인 OR 광고모델 발탁", "뉴스(신규 캠페인)", "신규 캠페인·브랜드"),
    ("올리브영 입점 OR 올리브영 신규 브랜드", "뉴스(올리브영)", "신규 캠페인·브랜드"),
    ("브랜드 론칭 마케팅 강화", "뉴스(브랜드 론칭)", "신규 캠페인·브랜드"),
    ("스타트업 투자 유치 마케팅", "뉴스(스타트업)", "기타 뉴스 리드"),
    ("병원 개원 OR 개원 마케팅", "뉴스(로컬병원)", "기타 뉴스 리드"),
    ("프랜차이즈 가맹점 모집", "뉴스(프랜차이즈)", "기타 뉴스 리드"),
    ("커머스 플랫폼 입점 브랜드", "뉴스(커머스)", "기타 뉴스 리드"),
]
PER_QUERY = 8


def collect():
    items, statuses = [], []
    for q, source, category in QUERIES:
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
                # 제목 끝의 " - 언론사" 부분 분리
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
