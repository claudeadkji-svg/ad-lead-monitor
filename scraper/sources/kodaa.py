# -*- coding: utf-8 -*-
"""한국디지털광고협회 알림·소식 게시판 (kodaa.or.kr/16)"""
import re

from bs4 import BeautifulSoup

from common import get, item

SOURCE = "한국디지털광고협회"
CATEGORY = "업계 협회·뉴스"
BASE = "http://kodaa.or.kr"


def collect():
    r = get(BASE + "/16")
    if r.status_code != 200:
        return [], f"오류: HTTP {r.status_code}"
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for a in soup.select('a[href*="bmode=view"]'):
        href = a.get("href", "")
        title = a.get_text(" ", strip=True)
        if not title or len(title) < 4:
            continue
        url = href if href.startswith("http") else BASE + href
        items.append(item(
            SOURCE, CATEGORY, title=title, url=url,
            company="한국디지털광고협회",
            description="협회 알림·소식",
            phone="02-2144-4421", email="koda@kodaa.or.kr",
        ))
    # 같은 글이 목록에 두 번 노출될 수 있어 제목 기준 중복 제거
    seen, uniq = set(), []
    for it in items:
        k = it["title"]
        if k not in seen:
            seen.add(k)
            uniq.append(it)
    return uniq[:15], f"성공: {len(uniq[:15])}건"
