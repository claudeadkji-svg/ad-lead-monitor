// 사이트 설정
// PASSWORD_HASH: 접속 비밀번호의 SHA-256 해시값입니다.
// 변경 방법: 브라우저 콘솔에서
//   crypto.subtle.digest('SHA-256', new TextEncoder().encode('새비밀번호')).then(b=>console.log([...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,'0')).join('')))
// 실행 후 나온 값으로 아래를 교체하세요. (초기 비밀번호: nas2026)
window.SITE_CONFIG = {
  TITLE: "AD LEAD MONITOR",
  SUBTITLE: "신규 광고주·대행사 영업 리드 데일리 모니터링",
  PASSWORD_HASH: "df8ab53cabe895638e16712e3f6d60b879161a50db1d4a57e2d21086ea6ff3c4",
};
