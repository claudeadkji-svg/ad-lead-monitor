# -*- coding: utf-8 -*-
"""수집 완료 후 신규 리드 요약을 슬랙으로 발송

GitHub Secrets에 SLACK_WEBHOOK_URL 등록 시 활성화됩니다.
(슬랙 워크스페이스에서 Incoming Webhook 생성 → URL을 Secret으로 등록)
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://claudeadkji-svg.github.io/ad-lead-monitor/"


def main():
    webhook = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not webhook:
        print("SLACK_WEBHOOK_URL 미설정 — 알림 생략")
        return

    kst = timezone(timedelta(hours=9))
    today = os.environ.get("FORCE_DATE") or datetime.now(kst).strftime("%Y-%m-%d")
    path = os.path.join(ROOT, "docs", "data", f"{today}.json")
    try:
        with open(path, encoding="utf-8") as f:
            snap = json.load(f)
    except Exception as e:
        print(f"스냅샷 로드 실패: {e}")
        return

    new_items = [i for i in snap["items"] if i.get("is_new")]
    by_cat = {}
    for i in new_items:
        by_cat.setdefault(i["category"], []).append(i)

    lines = [f"*📊 AD LEAD MONITOR — {today}*",
             f"오늘 신규 리드 *{len(new_items)}건* / 전체 {snap['total']}건"]
    for cat, items in sorted(by_cat.items()):
        lines.append(f"\n*{cat}* ({len(items)}건)")
        for i in items[:5]:
            company = f" — {i['company']}" if i.get("company") else ""
            lines.append(f"• <{i['url']}|{i['title'][:60]}>{company}")
        if len(items) > 5:
            lines.append(f"  _...외 {len(items) - 5}건_")
    lines.append(f"\n<{SITE}|👉 대시보드 전체 보기>")

    r = requests.post(webhook, json={"text": "\n".join(lines)}, timeout=15)
    print(f"슬랙 발송: HTTP {r.status_code}")


if __name__ == "__main__":
    main()
