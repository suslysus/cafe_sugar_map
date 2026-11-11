# 외부 라이브러리

## Google Analytics 4 Google 태그 (선택 동의 후 로드)

- 용도: 배포 사이트의 페이지 방문 통계. 일반 GA4 무료 버전을 사용한다.
- 출처: [Google Analytics 개발자 문서](https://developers.google.com/analytics/devguides/collection/ga4/views)
- 로드: `assets/js/analytics.js`가 운영 주소에서 통계 수집에 동의한 경우에만 `https://www.googletagmanager.com/gtag/js`를 요청한다. Google 태그는 저장소에 복사하지 않으며 고정 버전이 아니다.
- Google Analytics 서비스 이용약관과 개인정보처리방침을 따른다. 쿠키 식별자·접속 기기 등은 Google에서 처리되므로 완전한 익명 통계라고 보장하지 않는다. 이메일·비밀번호·인증 코드·검색어·정밀 위치를 이 모듈의 통계 항목으로 보내지 않는다.
- 측정 ID는 공개 설정이다. 별도 관리자 비밀 키·측정 프로토콜 API 비밀번호는 필요 없다.
- 거절·로컬 환경·인증 콜백에서는 태그를 로드하지 않는다. Google 장애·차단은 사이트 로그인·검색을 막지 않는다. 운영 설정과 확인 절차는 [방문 통계 안내](analytics.md)를 따른다.

## Supabase JavaScript SDK

- 패키지: `@supabase/supabase-js` 2.118.0 (고정 버전)
- 파일: `assets/vendor/supabase-2.118.0.js`
- 출처: [공식 npm 패키지](https://www.npmjs.com/package/@supabase/supabase-js/v/2.118.0)
- 배포: npm tarball의 `dist/umd/supabase.js`. 가져올 때 npm `dist.integrity`의 SHA-512를 확인했다.
- 파일 SHA-256: `ee3be8de192b97cb1d73d1e95d6b82bb1f6b658c0f97c4ef757fc331996ed3d3`
- 라이선스: MIT. 원본 고지: `assets/vendor/SUPABASE-LICENSE.txt`

사이트는 SDK를 로컬 정적 파일로 제공한다. 인증·DB 사용에는 설정된 Supabase 프로젝트와 네트워크 연결이 필요하다. 버전 갱신은 공통 연결 코드를 검증한 후 팀에 공유한다.

## 카카오 지도 JavaScript SDK (실행 시 로드)

- 용도: 지도 페이지의 지도 표시와 주변 매장 검색(services 라이브러리)
- 출처: 카카오 Developers의 카카오맵 API ([웹 API 문서](https://apis.map.kakao.com/web/))
- 로드 방식: Supabase SDK와 달리 **저장소에 포함하지 않는다.** `assets/js/map.js`가 실행할 때 `https://dapi.kakao.com/v2/maps/sdk.js`를 불러오며, SDK가 내부적으로 `kakaocdn.net`의 추가 스크립트와 지도 데이터를 요청한다.
- 버전: 카카오 서버가 제공하는 버전을 그대로 쓰며 고정하거나 해시를 검증하지 않는다. 지도 동작이 갑자기 바뀌면 카카오 쪽 변경부터 확인한다.
- 라이선스·이용 조건: 오픈소스 라이선스가 아니며 카카오 개발자 서비스·카카오맵 API 이용 조건을 따른다. 검색 결과는 저장·재배포하지 않고 요청 시점에 조회한다.
- 키: 브라우저 공개용 JavaScript 키(`assets/js/config.js`의 `kakaoJavaScriptKey`)이며 카카오 개발자 콘솔에 등록한 도메인에서만 동작한다. REST API 키는 사용하지 않는다.
- 외부 요청·개인정보: 지도 페이지를 열면 브라우저가 카카오 서버로 요청을 보낸다. 현재 위치를 허용하면 그 좌표가 주변 매장 검색 요청에 포함되며, 앱은 좌표를 저장하지 않는다.
- 장애 시: 키가 없거나 SDK를 불러오지 못하면 기존 예시 지도로 대체한다. 설정은 [배포 안내](deployment.md#카카오-지도), 연결 계약은 [API 문서](api.md#지도-페이지의-주변-매장-카카오)를 참고한다.
