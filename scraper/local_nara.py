# -*- coding: utf-8 -*-
"""나라장터 로컬 수집기 (Windows 작업 스케줄러가 매일 06:00 실행)

data.go.kr이 해외 IP(GitHub 서버)를 차단하므로, 한국 IP인 이 PC가
나라장터만 수집해 docs/data/nara_cache.json으로 커밋·푸시합니다.
06:30 클라우드 수집이 이 캐시를 읽어 대시보드에 병합합니다.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "docs", "data", "nara_cache.json")


def main():
    from sources import g2b

    if not os.environ.get("NARA_API_KEY", "").strip():
        print("NARA_API_KEY 환경변수 없음 — 종료")
        sys.exit(1)

    items, status = g2b.collect()
    print(f"나라장터: {status}")
    if not items or status.startswith("캐시"):
        print("신규 수집 실패 — 캐시 갱신 생략")
        sys.exit(1)

    kst = timezone(timedelta(hours=9))
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump({
            "updated": datetime.now(kst).strftime("%Y-%m-%d %H:%M"),
            "items": items,
        }, f, ensure_ascii=False, indent=1)

    def run(*args):
        r = subprocess.run(["git", "-C", ROOT] + list(args),
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("git", args[0], "실패:", (r.stderr or r.stdout)[:200])
        return r.returncode

    run("pull", "--rebase")
    run("add", "docs/data/nara_cache.json")
    if run("diff", "--cached", "--quiet") != 0:  # 변경 있음
        run("commit", "-m", "data: nara cache (local)")
        run("pull", "--rebase")
        run("push")
        print("캐시 푸시 완료")
    else:
        print("변경 없음")


if __name__ == "__main__":
    main()
