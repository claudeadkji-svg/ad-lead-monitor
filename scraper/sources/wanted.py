# -*- coding: utf-8 -*-
"""원티드 마케팅·광고 직군 채용공고 (내부 API, tag 523 = 마케팅)"""
from common import get, item

SOURCE = "원티드"
CATEGORY = "채용공고 리드"
API = ("https://www.wanted.co.kr/api/v4/jobs?country=kr&tag_type_ids=523"
       "&job_sort=job.latest_order&years=-1&locations=all&limit=40")


def collect():
    r = get(API, headers={
        "Accept": "application/json",
        "Referer": "https://www.wanted.co.kr/wdlist/523",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    })
    if r.status_code != 200:
        return [], f"오류: HTTP {r.status_code}"
    data = r.json().get("data", [])
    items = []
    for j in data:
        jid = j.get("id")
        company = (j.get("company") or {}).get("name", "")
        addr = (j.get("address") or {}).get("location", "")
        items.append(item(
            SOURCE, CATEGORY,
            title=j.get("position", ""),
            url=f"https://www.wanted.co.kr/wd/{jid}",
            company=company,
            description=f"마케팅 직군 채용 중 · 지역: {addr}",
        ))
    return items, f"성공: {len(items)}건"
