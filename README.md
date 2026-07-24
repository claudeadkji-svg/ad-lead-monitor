# AD LEAD MONITOR

신규 광고주·대행사 영업 리드를 매일 자동 수집해 한 페이지에서 보여주는 팀 대시보드.

## 구조

- `scraper/` — Python 수집기 (GitHub Actions가 매일 06:30 KST 자동 실행)
- `docs/` — GitHub Pages로 서비스되는 대시보드 (index.html + data/*.json)
- `.github/workflows/daily.yml` — 매일 자동 수집 스케줄

## 수집 소스

| 소스 | 방식 | 상태 |
|---|---|---|
| 나라장터 | 공공데이터포털 API (하이브리드) | 활성. data.go.kr이 해외 IP를 차단하므로 사무실 PC가 매일 06:00에 수집해 `nara_cache.json`으로 푸시(작업 스케줄러 `AdLeadMonitor-NaraCollect`), 06:30 클라우드 수집이 병합. PC가 꺼진 날은 직전 캐시 사용(대시보드에 캐시 시각 표시) |
| 한국디지털광고협회 | 게시판 크롤링 | 자동 |
| 모비인사이드 / 매드타임스 | RSS | 자동 |
| 원티드 | 내부 API (마케팅 직군) | GitHub 서버 IP가 차단되어 클라우드 수집 불가 (로컬 실행 시 수집됨) |
| 링크드인 | 게스트 검색 API | 자동 (간헐적 차단 가능) |
| 사람인 | 크롤링 (API 키 등록 시 공식 API) | 자동 |
| 잡코리아 | 크롤링 | 자동 |
| 구글뉴스 키워드 | RSS (올리브영·병원·프랜차이즈·커머스·캠페인 등) | 자동 |

## 운영 방법

### 비밀번호 변경
`docs/config.js`의 `PASSWORD_HASH`를 교체 (파일 안 주석에 방법 설명). 초기 비밀번호: `nas2026`

### 수동 리드 추가
GitHub에서 `docs/data/manual.json`을 수정해 항목 추가 → 다음 수집 때 대시보드에 반영.

### 수집 키워드 변경
저장소 루트 `keywords.json` 수정 (채용 검색어, 나라장터 검색어, 뉴스 키워드). 코드 지식 불필요.

### 아침 슬랙 알림 (선택)
슬랙에서 Incoming Webhook 생성 → 저장소 Settings → Secrets → `SLACK_WEBHOOK_URL` 등록.
등록하면 매일 수집 직후 신규 리드 요약이 슬랙 채널로 발송됩니다.

### 주간 엑셀 리포트
매주 월요일 07:00 KST 자동 생성 (`weekly-report` 워크플로) → 대시보드 하단에서 다운로드.

### 즉시 수집 실행
Actions 탭 → daily-collect → Run workflow

## 로컬 실행

```
pip install -r requirements.txt
python scraper/main.py
```
