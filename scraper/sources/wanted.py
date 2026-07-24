# -*- coding: utf-8 -*-
"""원티드 마케팅·광고 직군 채용공고 (내부 API, tag 523 = 마케팅)

데이터센터 IP에서 API가 403을 반환하는 경우가 있어,
목록 페이지를 먼저 방문해 쿠키를 확보한 뒤 API를 호출합니다.
"""
import requests
import urllib3

from common import UA, item

urllib3.disable_warnings()

SOURCE = "원티드"
CATEGORY = "채용공고 리드"
LIST_PAGE = "https://www.wanted.co.kr/wdlist/523?country=kr&job_sort=job.latest_order&years=-1&locations=all"
API = ("https://www.wanted.co.kr/api/v4/jobs?country=kr&tag_type_ids=523"
       "&job_sort=job.latest_order&years=-1&locations=all&limit=40")


def collect():
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
    })
    try:
        # 쿠키 확보용 사전 방문
        s.get(LIST_PAGE, timeout=25, verify=False,
              headers={"Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                       "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate",
                       "Sec-Fetch-Site": "none", "Upgrade-Insecure-Requests": "1"})
        r = s.get(API, timeout=25, verify=False,
                  headers={"Accept": "application/json", "Referer": LIST_PAGE,
                           "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors",
                           "Sec-Fetch-Site": "same-origin",
                           "X-Requested-With": "XMLHttpRequest"})
    except Exception as e:
        return [], f"오류: {type(e).__name__}"
    if r.status_code != 200:
        return [], f"오류: HTTP {r.status_code} (클라우드 IP 차단 가능 — 로컬 실행 시 수집됨)"
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
