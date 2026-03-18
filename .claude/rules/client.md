---
paths:
  - "fastapi/public/**"
---

# 클라이언트 코딩 규칙

아키텍처 가이드는 `web-client` skill, 코드 레벨 규칙은 `client-convention` skill 참조.

## 핵심 원칙
- 클라이언트 = 뷰어 (게임 로직을 클라이언트에 두지 않는다)
- 서버는 전투 결과를 계산해서 반환 (시뮬레이션)
- 클라이언트는 결과를 받아 애니메이션으로 재생

## 기술 스택
- Vanilla JS (ES Modules, 빌드 도구 없음)
- Phaser.js (전투 연출 전용, CDN)
- HTML/CSS (UI, 모바일 퍼스트)
- HTTP 통신 (WebSocket 미사용)

## 핵심 패턴
- **모듈**: ES Modules (`import`/`export`, IIFE 금지)
- **상태 관리**: 중앙 Store (pub/sub), API 응답 → Store → UI
- **Screen**: `mount(el)` / `unmount()` 라이프사이클
- **렌더링**: innerHTML 초기 생성 + refs 캐싱 + 부분 갱신
- **이벤트**: 이벤트 위임 (`pointerdown` + `data-action`)

## 정적 파일 서빙
- FastAPI `StaticFiles`로 `fastapi/public/` 디렉토리 마운트
- SPA 라우팅 필요 시 `html=True` 옵션 사용 중
