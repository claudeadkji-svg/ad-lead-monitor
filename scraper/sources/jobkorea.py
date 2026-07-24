# -*- coding: utf-8 -*-
"""잡코리아 마케터 채용공고 검색"""
from bs4 import BeautifulSoup

from common import get, item

SOURCE = "잡코리아"
CATEGORY = "채용공고 리드"
SEARCH = "https://www.jobkorea.co.kr/Search/?stext=%EB%A7%88%EC%BC%80%ED%84%B0&ord=RegDtDesc"


def collect():
    r = get(SEARCH)
    if r.status_code != 200:
        return [], f"오류: HTTP {r.status_code}"
    soup = BeautifulSoup(r.text, "html.parser")
    items, seen_href = [], set()
    for a in soup.select('a[href*="/Recruit/GI_Read/"]'):
        href = a.get("href", "").split("?")[0]
        title = a.get_text(" ", strip=True) or a.get("title", "")
        if not title or len(title) < 5 or href in seen_href:
            continue
        seen_href.add(href)
        url = href if href.startswith("http") else "https://www.jobkorea.co.kr" + href
        # 회사명: 공고 링크 주변 컨테이너에서 탐색
        company = ""
        parent = a.find_parent(["article", "li", "div", "tr"])
        if parent:
            c = parent.select_one('a[href*="/Recruit/Co_Read/"], a[href*="company"]')
            if c and c is not a:
                company = c.get_text(" ", strip=True)[:50]
        items.append(item(
            SOURCE, CATEGORY, title=title[:120], url=url,
            company=company, description="잡코리아 마케터 채용공고",
        ))
        if len(items) >= 30:
            break
    return items, f"성공: {len(items)}건"
