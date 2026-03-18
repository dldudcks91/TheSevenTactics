# TheSevenTactics Web RPG

## 프로젝트 개요
7대 죄악(TheSevenRPG) 세계관 기반의 웹 RPG 게임
- 세계: Aurea — 신이 걸었던 땅, 7대 죄악이 지배하는 다크 판타지 세계
- 주인공: 바알(Baal) — 타락한 마왕이 인간의 몸으로 잃어버린 힘을 되찾는 여정
- 핵심 재미: 영웅 육성 + 3인 파티 전투 + 7죄종 스킬트리

## 기술 스택
- 서버: FastAPI (async) + uvicorn
- DB: MySQL + SQLAlchemy ORM
- 캐시: Redis (async, 세션/전투 상태)
- 클라이언트: Vanilla JS (ES Modules) + Phaser.js
- 데이터: CSV 메타데이터 (서버 시작 시 로드)
- API: 단일 /api 게이트웨이 (api_code 라우팅)

## 참고 게임
- 아포칼립스 (동양온라인/플로우게임즈, 2010) - 국내 최초 RPG 웹게임
- 디아블로 시리즈 - 아이템 파밍 구조 참고
- TheSevenRPG - 세계관/스토리/몬스터 원작

## 기획 문서 위치
- `docs/GAME_DESIGN.md` - 메인 게임 디자인 문서
- `docs/DEV_PLAN.md` - 개발 계획서

## 개발 규칙
- 기획서는 한국어로 작성
- 문서 변경 시 마지막 업데이트 날짜 기재
