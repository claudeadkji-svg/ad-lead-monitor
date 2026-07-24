# AD LEAD MONITOR

신규 광고주·대행사 영업 리드를 매일 자동 수집해 한 페이지에서 보여주는 팀 대시보드.

## 구조

- `scraper/` — Python 수집기 (GitHub Actions가 매일 06:30 KST 자동 실행)
- `docs/` — GitHub Pages로 서비스되는 대시보드 (index.html + data/*.json)
- `.github/workflows/daily.yml` — 매일 자동 수집 스케줄

## 수집 소스

| 소스 | 방식 | 상태 |
|---|---|---|
| 나라장터 | 공공데이터포털 API | `NARA_API_KEY` Secret 등록 시 활성화 |
| 한국디지털광고협회 | 게시판 크롤링 | 자동 |
| 모비인사이드 / 매드타임스 | RSS | 자동 |
| 원티드 | 내부 API (마케팅 직군) | 자동 |
| 링크드인 | 게스트 검색 API | 자동 (간헐적 차단 가능) |
| 사람인 | 크롤링 (API 키 등록 시 공식 API) | 자동 |
| 잡코리아 | 크롤링 | 자동 |
| 구글뉴스 키워드 | RSS (올리브영·병원·프랜차이즈·커머스·캠페인 등) | 자동 |

## 운영 방법

### 비밀번호 변경
`docs/config.js`의 `PASSWORD_HASH`를 교체 (파일 안 주석에 방법 설명). 초기 비밀번호: `nas2026`

### 수동 리드 추가
GitHub에서 `docs/data/manual.json`을 수정해 항목 추가 → 다음 수집 때 대시보드에 반영.

### 나라장터 활성화 (권장)
1. [data.go.kr](https://www.data.go.kr) 가입 → "나라장터 입찰공고정보서비스" 검색 → 활용신청 (무료, 즉시 승인)
2. 저장소 Settings → Secrets and variables → Actions → `NARA_API_KEY` 등록
3. 다음 수집부터 광고/홍보/마케팅 입찰공고가 담당자 이메일·전화번호와 함께 수집됨

### 즉시 수집 실행
Actions 탭 → daily-collect → Run workflow

## 로컬 실행

```
pip install -r requirements.txt
python scraper/main.py
```
