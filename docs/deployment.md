# 배포와 운영

2026-11-03. 공유 주소는 [Cafe Sugar Map](https://suslysus.github.io/cafe_sugar_map/)이다. GitHub Pages 기본 도메인을 사용하며 별도 도메인을 구매하지 않는다.

## 현재 설정

[저장소 Settings → Pages](https://github.com/suslysus/cafe_sugar_map/settings/pages)에서 다음 값을 저장했다.

| 항목 | 값 |
| --- | --- |
| Source | Deploy from a branch |
| Branch | main |
| Folder | / (root) |
| HTTPS | 기본 도메인에서 강제 적용 |
| 첫 배포 | main의 8f4b042, 기존 데모 화면 |
| Supabase 기능 | PR #2 merge 후 로그인 코드 배포 확인 (2026-11-03) |

빌드 명령이나 별도 Node 서버는 필요 없다. 네 HTML 파일이 저장소 루트에 있으며 CSS·JS·페이지 링크는 프로젝트 경로 아래에서 동작하는 상대 경로를 유지한다. `/assets/...`처럼 도메인 루트 기준으로 바꾸면 `/cafe_sugar_map/` 배포에서 깨질 수 있다.

## 팀원 작업 순서

개인 브랜치 수정 → push → PR → 카카오톡 작업 보고·검토 요청 → 다른 팀원 검토 → main에 merge 순서를 유지한다. Pages를 설정했다고 main 직접 push가 허용되는 것은 아니다. 개인 브랜치는 배포하지 않으며, Pages 배포용으로 main을 우회해 다른 브랜치를 지정하지 않는다.

merge 이후 [Actions](https://github.com/suslysus/cafe_sugar_map/actions)의 `pages build and deployment` 실행이 성공하면 배포 주소에서 변경을 확인한다. 이 자동 작업은 GitHub가 Pages용으로 제공하며, 메뉴 크롤링 작업과는 별개다. 실패하면 해당 실행의 오류를 먼저 확인한다.

## Supabase 인증

Supabase Authentication → URL Configuration의 Site URL은 `https://suslysus.github.io/cafe_sugar_map/mypage.html`로 설정했다. 초기 로그인 구현은 [PR #2](https://github.com/suslysus/cafe_sugar_map/pull/2)로 main에 반영했다. PR #2의 초기 설정 기록에 localhost Site URL이 적혀 있으면 아래 배포 설정을 최신 값으로 따른다. 공유 프로젝트의 Site URL을 각자 localhost로 바꾸지 않는다.

허용 Redirect URLs는 다음 세 개다.

```text
https://suslysus.github.io/cafe_sugar_map/mypage.html
http://localhost:8000/mypage.html
http://127.0.0.1:8000/mypage.html
```

PR #2의 코드는 메일을 요청한 페이지 기준으로 `mypage.html` 복귀 주소를 생성한다. 다른 포트로 개발한다면 해당 경로를 허용 목록에 추가해야 한다. HTML 파일을 직접 여는 `file://` 대신 로컬 정적 서버나 배포 주소를 사용한다.

배포 사이트에서 가입·인증 메일을 새로 요청하고 같은 브라우저에서 연다. localhost에서 과거에 요청한 메일의 복귀 주소가 새 설정으로 모두 바뀌는 것은 아니다. localhost 주소는 각자 PC이므로 로컬 서버가 꺼져 있으면 열리지 않는다. 이메일 인증과 비밀번호 입력·변경은 계정 소유자가 직접 확인한다.

## 카카오 지도

지도 페이지는 카카오 지도 JavaScript SDK를 사용한다. 키는 `assets/js/config.js`의 `kakaoJavaScriptKey`에 두며 브라우저 공개용이다. 코드와 문서에 카카오 REST API 키·관리자 키를 넣지 않는다.

[카카오 개발자 콘솔](https://developers.kakao.com)의 해당 앱에서 다음을 설정한다. 메뉴 이름은 콘솔 개편으로 달라질 수 있다.

- JavaScript SDK 도메인(플랫폼 → Web 사이트 도메인)에 아래 세 개를 등록한다. 프로토콜과 포트를 포함하고 경로는 붙이지 않는다.
- 앱 설정에서 카카오맵 사용 설정을 켠다.

```text
https://suslysus.github.io
http://localhost:8000
http://127.0.0.1:8000
```

다른 포트나 주소로 개발하면 그 주소도 등록한다. 등록하지 않았거나 키가 비어 있으면 지도 페이지는 예시 지도로 대체 표시되어 화면은 깨지지 않지만 실제 지도와 매장은 나타나지 않는다. 그러므로 지도 PR을 merge하기 전에 배포 도메인 등록을 확인하고, merge 후 배포 주소에서 실제 지도가 표시되는지 확인한다.

브라우저의 현재 위치 허용은 `localhost`와 HTTPS 주소에서만 동작한다. 카카오맵 API의 무료 사용량·쿼터 제공 방식은 정책이 바뀔 수 있으므로 어느 앱에서 카카오맵을 활성화했는지와 사용량을 콘솔에서 확인한다. 이 SDK는 저장소에 포함하지 않고 실행 시 카카오 서버에서 불러온다.

## 크롤링과 비용

선택한 구성은 GitHub Pages(화면) + Supabase(인증·DB) + GitHub Actions(정기 수집)다. **이번에는 Pages 배포와 인증 복귀 주소만 설정했다. 크롤러·메뉴 DB·수집용 Actions는 아직 구현하지 않았다.** 수집할 사이트와 갱신 주기를 정한 후 개발한다.

공개 저장소의 Pages와 표준 GitHub-hosted Actions 실행은 무료이고 Supabase는 Free 사용량 안에서 운영한다. Supabase Free는 DB 500 MB 등 제한이 있으며 활동이 적은 상태가 약 일주일 지속되면 프로젝트가 일시정지될 수 있다. Actions 예약 실행도 지연될 수 있으므로 정확한 실시간 수집을 전제로 하지 않는다. 유료 플랜·유료 실행 환경을 임의로 선택하지 않는다.

향후 수집용 비밀 키는 GitHub Actions Secrets에 두고, HTML·JS·README·로그·생성 결과물에 포함하지 않는다. 브라우저의 publishable key와 서버 수집용 비밀 키를 구분한다. 프런트엔드는 저장된 메뉴를 읽고, 수집 작업만 필요한 범위에서 DB를 갱신하도록 설계한다.

## 공식 참고

- [Pages 배포 소스 설정](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHub Actions 요금](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [예약 실행](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [Supabase 요금](https://supabase.com/pricing)
- [Supabase Redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls)