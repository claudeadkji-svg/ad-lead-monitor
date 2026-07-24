# -*- coding: utf-8 -*-
"""나라장터 입찰공고 — 공공데이터포털 API (NARA_API_KEY 등록 시 활성화)

신형 나라장터(g2b.go.kr)는 SPA 구조라 직접 크롤링이 불가능합니다.
data.go.kr에서 '조달청_나라장터 입찰공고정보서비스' 활용신청(무료) 후
발급 키를 GitHub Secrets `NARA_API_KEY`에 등록하면 자동으로 켜집니다.
"""
import json
import os
from datetime import datetime, timedelta, timezone

from common import ROOT, get, item, load_keywords

CACHE = os.path.join(ROOT, "docs", "data", "nara_cache.json")

SOURCE = "나라장터"
CATEGORY = "정부·공공 입찰"
ENDPOINT = os.environ.get(
    "NARA_API_ENDPOINT",
    "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch",
)


def keywords():
    return load_keywords().get("나라장터_검색어", ["광고", "홍보", "마케팅"])


def from_cache(reason):
    """API 실패 시 로컬 PC가 커밋해 둔 캐시 사용 (data.go.kr 해외 IP 차단 우회)"""
    try:
        with open(CACHE, encoding="utf-8") as f:
            c = json.load(f)
        return c.get("items", []), f"캐시 사용: {len(c.get('items', []))}건 (로컬 수집 {c.get('updated', '?')})"
    except Exception:
        return [], reason


def collect():
    key = os.environ.get("NARA_API_KEY", "").strip()
    if not key:
        return from_cache("대기: NARA_API_KEY 미설정 (data.go.kr에서 무료 발급 후 등록하면 자동 활성화)")

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    begin = (now - timedelta(days=7)).strftime("%Y%m%d0000")
    end = now.strftime("%Y%m%d2359")

    items, errors = [], []
    for kw in keywords():
        try:
            r = get(ENDPOINT, params={
                "serviceKey": key, "pageNo": "1", "numOfRows": "50",
                "inqryDiv": "1", "inqryBgnDt": begin, "inqryEndDt": end,
                "bidNtceNm": kw, "type": "json",
            }, timeout=30)
            if r.status_code != 200 or not r.text.lstrip().startswith("{"):
                errors.append(f"{kw}: HTTP {r.status_code} {r.text.strip()[:80]!r}")
                continue
            data = r.json()
            rows = (data.get("response", {}).get("body", {}).get("items") or [])
            if isinstance(rows, dict):
                rows = rows.get("item", [])
            for row in rows:
                url = row.get("bidNtceDtlUrl") or row.get("bidNtceUrl") or "https://www.g2b.go.kr"
                items.append(item(
                    SOURCE, CATEGORY,
                    title=row.get("bidNtceNm", ""),
                    url=url,
                    company=row.get("ntceInsttNm", ""),
                    description=f"수요기관: {row.get('dminsttNm', '')} / 마감: {row.get('bidClseDt', '')}",
                    email=row.get("ntceInsttOfclEmailAdrs", ""),
                    phone=row.get("ntceInsttOfclTelNo", ""),
                    posted=(row.get("bidNtceDt", "") or "")[:10],
                ))
        except Exception as e:
            errors.append(f"{kw}: {type(e).__name__}")

    # 중복 제거
    seen, uniq = set(), []
    for it in items:
        if it["id"] not in seen:
            seen.add(it["id"])
            uniq.append(it)
    if not uniq and errors:
        return from_cache("오류: " + "; ".join(errors))
    return uniq, f"성공: {len(uniq)}건"
