# Cloudflare Pages 배포

이 프로젝트는 별도의 빌드 과정이 없는 정적 웹 게임입니다.

## Cloudflare Pages 설정

GitHub 저장소:
- `eska-start/Today`

설정값:
- Production branch: `main`
- Framework preset: `None`
- Build command: 비워두기
- Build output directory: `/`
- Root directory: `/`

저장 후 배포하면 `index.html`이 게임의 시작 페이지가 됩니다.

## 로컬 테스트

저장소 폴더에서 간단한 정적 서버를 실행하면 됩니다.

예:
```bash
python -m http.server 8080
```

그 다음 브라우저에서 `http://localhost:8080` 접속.

## 이후 확장

현재는 서버/DB가 필요 없는 싱글플레이어 프로토타입입니다.

추후 다음 기능을 추가할 때 Cloudflare Workers/D1을 붙일 수 있습니다.

- 세이브 데이터
- 플레이어 통계
- 일일 기록
- 랭킹
- 엔딩 기록
- NPC/문서 데이터 서버 관리
