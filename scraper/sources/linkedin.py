# -*- coding: utf-8 -*-
"""링크드인 채용공고 (게스트 검색 API — 비로그인 공개 엔드포인트)

주의: 링크드인은 봇 차단이 강해 간헐적으로 빈 결과가 나올 수 있습니다.
실패해도 전체 수집은 계속 진행됩니다.
"""
from urllib.parse import quote

from bs4 import BeautifulSoup

from common import get, item

SOURCE = "링크드인"
CATEGORY = "채용공고 리드"
QUERIES = ["마케팅", "광고 마케터"]
API = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/"
       "search?keywords={kw}&location=South%20Korea&start=0")


def collect():
    items, statuses = [], []
    for kw in QUERIES:
        try:
            r = get(API.format(kw=quote(kw)))
            if r.status_code != 200:
                statuses.append(f"{kw}: HTTP {r.status_code}")
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("li")
            n = 0
            for card in cards[:20]:
                a = card.select_one("a.base-card__full-link")
                t = card.select_one(".base-search-card__title")
                c = card.select_one(".base-search-card__subtitle")
                d = card.select_one("time")
                if not (a and t):
                    continue
                url = a.get("href", "").split("?")[0]
                items.append(item(
                    SOURCE, CATEGORY,
                    title=t.get_text(strip=True),
                    url=url,
                    company=c.get_text(strip=True) if c else "",
                    description=f"링크드인 채용공고 ({kw})",
                    posted=d.get("datetime", "") if d else "",
                ))
                n += 1
            statuses.append(f"{kw}: {n}건")
        except Exception as e:
            statuses.append(f"{kw}: 오류 {type(e).__name__}")
    # 중복 제거
    seen, uniq = set(), []
    for it in items:
        if it["id"] not in seen:
            seen.add(it["id"])
            uniq.append(it)
    return uniq, "; ".join(statuses)
