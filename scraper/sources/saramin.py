# -*- coding: utf-8 -*-
"""사람인 마케터 채용공고 검색 (SARAMIN_API_KEY 등록 시 공식 API 사용)"""
import os
from urllib.parse import quote

from bs4 import BeautifulSoup

from common import get, item, load_keywords

SOURCE = "사람인"
CATEGORY = "채용공고 리드"
API = "https://oapi.saramin.co.kr/job-search"


def job_keyword():
    return load_keywords().get("채용_검색어", "마케터")


def search_url():
    return ("https://www.saramin.co.kr/zf_user/search/recruit"
            f"?searchword={quote(job_keyword())}&recruitSort=reg_dt&recruitPageCount=40")


def collect_api(key):
    r = get(API, params={"access-key": key, "keywords": job_keyword(), "sr": "directhire",
                         "count": "40", "sort": "pd"},
            headers={"Accept": "application/json"})
    jobs = r.json().get("jobs", {}).get("job", [])
    items = []
    for j in jobs:
        pos = j.get("position", {})
        items.append(item(
            SOURCE, CATEGORY,
            title=pos.get("title", ""),
            url=j.get("url", ""),
            company=(j.get("company", {}).get("detail", {}) or {}).get("name", ""),
            description=f"업종: {(pos.get('industry') or {}).get('name', '')}",
        ))
    return items, f"성공(API): {len(items)}건"


def collect_scrape():
    r = get(search_url())
    if r.status_code != 200:
        return [], f"오류: HTTP {r.status_code}"
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for rec in soup.select(".item_recruit"):
        a = rec.select_one("h2.job_tit a")
        corp = rec.select_one(".corp_name a") or rec.select_one(".corp_name")
        cond = rec.select_one(".job_condition")
        if not a:
            continue
        href = a.get("href", "")
        url = href if href.startswith("http") else "https://www.saramin.co.kr" + href
        items.append(item(
            SOURCE, CATEGORY,
            title=a.get("title") or a.get_text(strip=True),
            url=url,
            company=corp.get_text(strip=True) if corp else "",
            description=cond.get_text(" ", strip=True)[:150] if cond else "",
        ))
    return items[:40], f"성공: {len(items[:40])}건"


def collect():
    key = os.environ.get("SARAMIN_API_KEY", "").strip()
    if key:
        try:
            return collect_api(key)
        except Exception:
            pass
    return collect_scrape()
