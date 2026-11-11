# 방문 통계 (Google Analytics 4)

2026-11-09. 일반 GA4 무료 버전을 사용한다. Analytics 360, 광고, 유료 Google Cloud 연동은 신청하지 않는다. 이 문서는 연결 코드의 동작을 설명하며, 실제 운영 데이터 수신 확인을 완료했다는 뜻은 아니다.

## 계정과 웹 스트림

이 프로젝트의 웹 스트림은 `Cafe Sugar Map`, URL은 `https://suslysus.github.io/cafe_sugar_map/`, 측정 ID는 `G-RD5RGR7SHN`이다. 측정 ID는 공개 설정으로, 비밀번호나 관리자 권한을 제공하는 비밀 키가 아니다. 스트림 ID 숫자나 `GTM-...` 컨테이너 ID와 혼동하지 않는다.

Analytics 계정 소유자가 서비스 약관 동의를 직접 완료한다. 계정 이름·속성 이름은 Cafe Sugar Map, 보고 시간대는 대한민국으로 설정한다. 방문 통계 외의 추가 데이터 공유는 사용하지 않는 방향으로 설정한다.

**배포 전에 관리 → 데이터 스트림 → Cafe Sugar Map 웹 스트림에서 ‘향상된 측정’을 끈다.** 이 구현은 기본 자동 page_view를 끄고 직접 한 번만 전송한다. 향상된 측정이 켜져 있으면 방문 외의 검색어·폼·링크 이벤트나 기록 변경에 따른 중복 page_view가 자동 수집될 수 있으므로, 코드만 바꾸고 이 설정을 생략하지 않는다. 별도 Google 태그/GTM 스니펫을 네 HTML에 중복 설치하지 않는다.

## 코드와 수집 범위

네 HTML에서 `assets/css/analytics.css`, `assets/js/analytics.js`를 불러온다. JS는 config와 기존 페이지 JS 뒤에 실행되며 기존 로그인·검색·지도 코드를 수정하지 않는다. `assets/js/config.js`의 `googleAnalyticsMeasurementId`를 빈 문자열로 만들면 통계 UI와 Google 태그 로드를 모두 비활성화한다.

운영 HTTPS 도메인과 `/cafe_sugar_map/` 아래 네 페이지에서만 작동한다. 로컬 서버, file URL, 임시 미리보기에서는 Google 태그를 로드하지 않는다. 마이페이지에 쿼리 또는 해시가 있으면 인증 콜백·returnTo 처리와 분리하기 위해 통계를 실행하지 않는다. 홈 경로 `/cafe_sugar_map/`는 `index.html`로 합쳐 집계한다.

화면 하단에서 ‘동의하고 시작’을 선택한 뒤에만 Google 태그를 로드한다. 미선택·거절 상태에서는 이 모듈이 Google로 요청을 보내지 않는다. 재방문 동의는 `csm.analytics.consent.v1`에 180일 동안 저장하며, 저장소 사용이 차단되면 이번 페이지에서만 선택이 적용되어 다음 페이지에서 다시 묻는다. ‘방문 통계 설정’을 열어 ‘동의하지 않음’을 선택하면 이후 수집을 중단하고 이 태그의 통계 쿠키를 지운다. 이미 Google에 전송된 기록까지 삭제되는 것은 아니다. Supabase 세션·프로필·즐겨찾기는 변경하지 않는다.

페이지 경로·고정 제목·유입 출처의 도메인을 전달한다. 검색어와 모든 URL 쿼리·해시, 이메일·표시 이름·비밀번호·Supabase 토큰·현재 위치 좌표·사용자 ID를 이 모듈의 통계 항목으로 보내지 않는다. GA는 자체적으로 쿠키 식별자·세션·기기·브라우저·대략적인 지역 등의 정보를 처리할 수 있으므로 완전히 익명인 집계라고 표현하지 않는다. Google Signals와 광고 개인 최적화 신호는 사용하지 않는다. 통계 쿠키는 host 전용, 프로젝트 경로 전용, `csm` 접두사이며 최대 30일로 설정한다.

## 실제 적용 순서와 수신 확인

개인 브랜치에서 코드 검토 → 사용자 허락 후 PR 작성 → 다른 팀원 리뷰 → merge → Actions의 `pages build and deployment` 성공 순서를 따른다. 이 단계가 끝나기 전에는 현재 배포 사이트에 Analytics가 설치된 것으로 보고하지 않는다.

배포 후 [사이트](https://suslysus.github.io/cafe_sugar_map/)를 광고 차단이 없는 브라우저에서 열고 화면 하단의 방문 통계 수집에 동의한다. 지도·검색·트렌드로 이동한 뒤 [Google Analytics](https://analytics.google.com/)에서 Cafe Sugar Map 속성을 선택하고 **보고서 → 실시간**에서 활성 사용자와 `page_view` 수신을 확인한다. 메뉴 이름은 선택한 보고서 구성에 따라 다를 수 있다. 사이트 이동 없이 설정 창만 여러 번 열었다고 page_view가 추가되지는 않는다.

개발자 도구 Network에서 `collect`를 검색하면 `google-analytics.com/g/collect` 또는 `analytics.google.com/g/collect` 요청을 확인할 수 있다. `tid`가 `G-RD5RGR7SHN`, `en`이 `page_view`인지 확인하고 `dl` 주소에 검색어·code·토큰 등이 없는지도 확인한다. 페이지 소스에 파일이 있다는 것과 실제 GA 수신 완료는 구분한다. Google 태그 설치 테스트가 미수신으로 나와도 통계 동의 전·차단 브라우저라면 요청이 발생하지 않는 것이 정상이다.

누적 페이지 조회는 **보고서 → 참여도 → 페이지 및 화면**, 유입 경로는 **보고서 → 획득 → 트래픽 획득**에서 확인한다. 비즈니스 목표에 따라 해당 보고서가 숨겨졌다면 보고서 라이브러리에서 관련 모음을 추가한다. 실시간과 달리 일반 보고서는 보통 24~48시간의 처리 시간이 필요할 수 있다.

## 통계를 해석할 때

설치·배포 이후 동의한 방문부터 기록되며, 이전 방문 기록은 복원하지 못한다. 거절·차단·로컬 접속·인증 콜백은 포함되지 않고 팀원의 실제 배포 사이트 테스트는 포함될 수 있다. 기기·브라우저·쿠키 초기화에 따라 사용자 수가 달라져 실제 사람 수와 정확히 같지 않다. 방문 통계는 사이트가 외부 글에서 몇 번 인용됐는지 나타내는 수치가 아니다. 유입 경로는 링크를 눌러 들어온 방문에 관한 정보이며, 외부 인용은 별도 검색이나 Search Console 링크 보고서로 확인한다.

## 배포 전 검증 기록

2026-11-09 Luna low 검증: 가짜 DOM·localStorage를 사용한 Node VM 검사 37/37 통과. 비운·잘못된 ID/운영 외 주소/인증 콜백 차단, 동의·거절·철회·다른 탭 동기화, URL 정리, 태그·page_view 중복 방지, 저장소 차단, SDK 로드 오류, 네 HTML의 로드 순서를 확인했다. `node --check`와 `git diff --check`도 통과했다. 검사는 Google·Supabase·카카오에 요청을 보내지 않았으므로 실제 GA 수신과 실제 SDK의 쿠키 동작은 배포 후 확인이 남아 있다. Analytics의 향상된 측정은 계정 소유자가 직접 끈 뒤 화면에서 OFF 상태를 별도로 확인했다.

## 공식 참고

- [무료 Analytics 안내](https://marketingplatform.google.com/about/small-business/)
- [계정·속성·웹 스트림 설정](https://support.google.com/analytics/answer/14183469?hl=ko)
- [page_view 수동 전송과 향상된 측정](https://developers.google.com/analytics/devguides/collection/ga4/views)
- [수신 확인](https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot)
- [개인 식별 정보 전송 방지](https://support.google.com/analytics/answer/6366371?hl=ko)
- [Google 개인정보처리방침](https://policies.google.com/privacy?hl=ko)
