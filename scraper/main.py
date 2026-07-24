# -*- coding: utf-8 -*-
"""AD LEAD MONITOR 수집 오케스트레이터

모든 소스를 수집해 docs/data/YYYY-MM-DD.json 스냅샷을 생성합니다.
- seen.json: 아이템별 최초 발견일 기록 → 오늘 처음 본 항목에 is_new 플래그
- index.json: 날짜 목록 (대시보드 날짜 선택용)
- manual.json: 팀원이 직접 추가한 리드 (자동 수집과 병합)
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sources import g2b, kodaa, rss_news, wanted, linkedin, saramin, jobkorea, gnews

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "docs", "data")

MODULES = [
    ("나라장터", g2b),
    ("한국디지털광고협회", kodaa),
    ("업계뉴스 RSS", rss_news),
    ("원티드", wanted),
    ("링크드인", linkedin),
    ("사람인", saramin),
    ("잡코리아", jobkorea),
    ("구글뉴스 키워드", gnews),
]


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def main():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    today = os.environ.get("FORCE_DATE") or now.strftime("%Y-%m-%d")

    seen = load_json(os.path.join(DATA, "seen.json"), {})
    all_items, source_status = [], []

    for name, mod in MODULES:
        try:
            items, status = mod.collect()
        except Exception as e:
            items, status = [], f"실패: {type(e).__name__}: {e}"
        source_status.append({"name": name, "status": status, "count": len(items)})
        all_items.extend(items)
        print(f"[{name}] {status}")

    # 수동 등록 리드 병합
    manual = load_json(os.path.join(DATA, "manual.json"), [])
    for m in manual:
        m.setdefault("id", "manual-" + str(abs(hash(m.get("title", ""))) % 10**10))
        m.setdefault("source", "수동 등록")
        m.setdefault("category", "수동 등록")
        for k in ("title", "url", "company", "description", "email", "phone", "posted"):
            m.setdefault(k, "")
    all_items.extend(manual)

    # 전체 중복 제거 (id 기준)
    dedup = {}
    for it in all_items:
        dedup.setdefault(it["id"], it)
    all_items = list(dedup.values())

    # 신규 여부 판정
    for it in all_items:
        first = seen.get(it["id"])
        if first is None:
            seen[it["id"]] = today
            first = today
        it["first_seen"] = first
        it["is_new"] = (first == today)

    # 신규 우선 정렬
    all_items.sort(key=lambda x: (not x["is_new"], x["category"], x["source"]))

    snapshot = {
        "date": today,
        "generated_at": now.strftime("%Y-%m-%d %H:%M KST"),
        "sources": source_status,
        "total": len(all_items),
        "new_count": sum(1 for i in all_items if i["is_new"]),
        "items": all_items,
    }
    save_json(os.path.join(DATA, f"{today}.json"), snapshot)

    index = load_json(os.path.join(DATA, "index.json"), {"dates": []})
    if today not in index["dates"]:
        index["dates"].insert(0, today)
    index["dates"] = sorted(set(index["dates"]), reverse=True)[:365]
    save_json(os.path.join(DATA, "index.json"), index)

    # seen.json 정리: 1년 이상 지난 기록 제거
    cutoff = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    seen = {k: v for k, v in seen.items() if v >= cutoff}
    save_json(os.path.join(DATA, "seen.json"), seen)

    print(f"\n완료: 총 {snapshot['total']}건 (신규 {snapshot['new_count']}건) → data/{today}.json")


if __name__ == "__main__":
    main()
