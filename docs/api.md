# 현재 API 계약

2026-11-03. 메뉴·트렌드는 기존 예시 데이터이며, 인증·프로필·즐겨찾기는 Supabase SDK로 연결한다. 2026-11-07부터 지도 페이지의 지도와 주변 매장 위치는 카카오 지도·카카오 로컬 검색을 사용한다([지도 페이지](#지도-페이지의-주변-매장-카카오) 참고). 각 페이지는 CafeAPI 공개 함수를 호출한다. 별도 /api/v1 서버는 현재 없다.

## 인증·프로필·저장

| CafeAPI 함수 | 입력·반환 | 실제 연결 |
| --- | --- | --- |
| authReady | 초기화 Promise. 설정 실패도 상태로 보존 | CafeAuth.ready |
| getAuthStatus() | initialized/configured/error/code/dataError/recovery | 연결·복구 UI 상태 |
| getSession() | Promise<User 또는 null> | Supabase Auth 세션 + profiles 표시 이름 |
| login({ email, password }) | Promise<User> | auth.signInWithPassword |
| requestSignupVerification(email) | Promise<void> | 임시 비밀번호로 auth.signUp, 가입 대기 메타데이터, 인증 링크 발송 |
| completeSignup({ displayName, password }) | Promise<User> | auth.getUser로 인증·가입 대기 확인 → profiles 이름 수정 → auth.updateUser |
| signUp({ email, password, displayName }) | Promise<{ signedIn }> | 이전 호출 호환용. 현재 회원가입 화면에서는 사용하지 않음 |
| logout() | Promise<void> | auth.signOut(scope: local) |
| updateProfile(displayName) | Promise<User> | profiles 본인 행 UPDATE |
| getFavorites() | Promise<메뉴 DTO 배열> | favorites 조회 후 현재 공통 메뉴 ID 연결 |
| toggleFavorite(menuId) | Promise<저장 여부 boolean> | 본인 favorites INSERT/DELETE |
| isFavorite(menuId) | 동기 boolean 캐시 조회 | 로그인·저장 변경 이벤트로 갱신 |
| resendConfirmation(email) | Promise<void> | auth.resend(type: signup) |
| sendPasswordReset(email) | Promise<void> | auth.resetPasswordForEmail |
| updatePassword(password) | Promise<void> | 복구 이벤트로 인증된 상태에서 auth.updateUser |

User 형태는 { id, email, displayName, signupPending, emailVerified, isDemo: false }다. 식별자는 Supabase 사용자 UUID이며 표시 이름으로 계정을 나누지 않는다. 비밀번호는 함수 호출에만 사용하고 앱 코드가 직접 저장하지 않는다.

회원가입 화면은 이메일만 먼저 입력받는다. 인증 메일 받기는 임의의 임시 비밀번호를 Web Crypto로 생성하고 `csm_signup_pending: true` 메타데이터와 함께 Auth에 요청한다. 임시 비밀번호는 화면·저장소·로그에 남기지 않는다. 최초 요청 때 Auth 사용자와 기본 프로필 행이 생성되지만, 입력칸은 실제 인증 세션을 얻기 전까지 잠근다. 기존 Confirm signup 메일 템플릿과 PKCE 링크를 그대로 사용하며 인증번호용 템플릿 변경은 필요 없다.

메일 링크로 받은 세션의 이메일 인증과 가입 대기 상태가 확인되면 이름·비밀번호 칸이 열린다. `completeSignup`은 UI 잠금과 별개로 서버 `getUser()` 결과의 소유자·`email_confirmed_at`·가입 대기 메타데이터를 검사한다. 일반 기존 계정의 비밀번호를 이 경로로 변경하지 않는다. 프로필을 먼저 저장하고 비밀번호·가입 대기 해제를 마지막에 처리하므로 실패하면 입력값을 유지하며 재시도할 수 있다. 성공한 뒤에만 비밀번호 입력을 비운다. 재접속 시 서버 메타데이터로 가입 마무리를 이어간다. 메타데이터는 진행 상태이며 DB 권한은 기존 RLS가 담당한다.

Supabase SDK가 JWT 전달과 세션 갱신을 처리한다. 공개 publishable 키와 사용자의 JWT는 서로 다르며, DB는 RLS에서 auth.uid()를 검사한다. 브라우저용 키를 관리자 키로 교체하면 안 된다.

## 이벤트·비동기 규칙

- cafe:auth-ready: 초기 연결 상태 확인 완료.
- cafe:session-changed: 로그인·로그아웃·프로필·복구 상태 변화.
- cafe:favorites-changed: 로그인 계정·저장 목록 변화.
- Auth 이벤트 콜백 안에서 SDK 요청을 await하지 않고 다음 작업으로 예약한다.
- isFavorite()는 카드 표시를 위한 동기 캐시 계약을 유지한다. 초기화·계정 변경 때 다시 표시하며, 늦게 끝난 이전 계정의 요청은 현재 캐시에 반영하지 않는다.
- 로그인 후 returnTo는 동일 디렉터리의 index.html/search.html/trends.html만 허용한다. 이메일 확인은 mypage.html로 돌아온다.

## 오류

AUTH_REQUIRED는 로그인 안내로 이동한다. CONFIG_REQUIRED/CONFIG_INVALID/SDK_UNAVAILABLE은 로그인을 막고 설정 안내를 표시한다. 잘못된 비밀번호, 이메일 미인증, 요청 제한은 각각 안내한다. DB 연결 실패는 빈 즐겨찾기와 구분하고 재시도를 제공한다. 원문 서버 오류·토큰·비밀번호를 화면이나 로그에 출력하지 않는다.

## 기존 메뉴·로컬 기능 계약

getBrands(), getCategories(), getStores(), getMenus({ brandId, category, q, isNew }), getMenu(menuId), getTrends()는 예시 데이터에 대한 Promise를 반환한다. getStores()의 x/y는 예시 지도 대체 화면용 가상 배치 좌표(%)이며 실제 위·경도가 아니다. getCompare()/toggleCompare()/clearCompare()는 기존 로컬 비교 선택을 유지한다.

메뉴 DTO는 { id, brandId, name, categoryTags, sizeLabel, volumeMl, temperature, priceKrw, sugarG, caloriesKcal, tone, isNew, seasonal, sourceUrl, checkedAt, isDemo }다. 단위는 원/g/kcal이고 미확인은 null이다. 현재 모든 메뉴는 isDemo:true다. 공유받은 JSON/CSV 5개는 사용하지 않는다.

실제 메뉴 수집·저장소로 바꾸더라도 메뉴 ID와 DTO를 유지한다. 저장소에 남았지만 현재 카탈로그에서 찾을 수 없는 메뉴는 getFavorites() 결과에서 제외된다. 실제 메뉴를 도입할 때 해당 항목의 표시·삭제·ID 이관 규칙을 추가해야 한다.

## 지도 페이지의 주변 매장 (카카오)

지도 페이지(`index.html`)는 예외적으로 `CafeAPI.getStores()` 대신 `map.js`가 카카오 SDK를 직접 호출해 실제 매장을 찾는다. 서버 매장 API가 생기면 아래 `fetchNearbyStores()`만 교체한다. 메뉴는 이전과 같이 `CafeAPI.getMenus({ brandId })`를 사용한다.

| 항목 | 내용 |
| --- | --- |
| 설정 | `assets/js/config.js`의 `CafeConfig.kakaoJavaScriptKey`. 브라우저 공개용 JavaScript 키이며 카카오 개발자 콘솔에 등록한 도메인에서만 동작한다. **REST API 키는 사용하지 않으며 넣지 않는다.** |
| SDK | `map.js`가 실행 시 `dapi.kakao.com`에서 지도·services 라이브러리를 불러온다(저장소에 포함하지 않음). 브라우저 외부 요청이 발생한다. |
| 검색 | `getBrands()`의 브랜드 이름으로 카카오 키워드 검색(검색 범위 500m, 거리순). 카페 카테고리(CE7)이고 상호명에 브랜드명이 포함된 결과만 사용한다. |
| 반환 모양 | `{ id, brandId, name, latitude, longitude, address, distanceM }` — `id/brandId/name/latitude/longitude`는 위 서버 제안(`GET /stores`)의 매장 DTO와 같고, `address/distanceM`은 선택 필드다. |
| 매장 ID | `kakao-` + 카카오 장소 ID. 화면 선택용이며 즐겨찾기·DB 저장에 사용하지 않는다. |
| 위치 | 허용하면 내 위치, 거부·차단·실패하면 숭실대 정문(37.4963, 126.9568) 기준. 내 위치를 보던 중 재조회가 실패해도(권한 거부·위치 확인 불가·시간 초과) 숭실대 기준으로 돌아온다. 좌표는 저장하지 않고 카카오 검색 요청에만 사용한다. |
| 위치 조회 방식 | `getCurrentPosition` 1회 조회이며 이동 중 자동 추적(`watchPosition`)은 하지 않는다. 먼저 네트워크 기반(`enableHighAccuracy: false`, 15초)으로 조회하고, 위치 확인 불가·시간 초과일 때만 GPS 고정밀(20초, 캐시 없음)로 한 번 더 시도한다. 권한 거부는 재시도하지 않는다. |
| 위치 캐시 | `maximumAge`: 페이지 진입 시 자동 요청은 60000(1분 이내 캐시 허용), 내 위치(⌖) 버튼 클릭과 권한 재허용 후 재조회는 0(항상 새로 측정). |
| 대체 동작 | 키가 없거나 SDK를 불러오지 못하면 `getStores()`의 가상 매장이 있는 기존 예시 지도로 대체하고 실제 정보가 아님을 안내한다. |

브랜드 이름이 바뀌거나 브랜드가 추가되면 `map.js`의 `SEARCH_RULES`(검색어·상호 판별어)와 `PIN_STYLE`(마커 색)을 함께 확인한다. 규칙에 없는 브랜드는 브랜드 이름으로 검색하고 `mock-data.js`의 브랜드 색을 사용한다. 카카오 검색 결과의 문자열은 `CafeUI.escape()` 또는 `textContent`로만 화면에 넣고, 결과를 DB·파일에 저장하지 않는다. 저장·재사용 범위는 카카오 이용 조건을 확인한 뒤에 정한다.

## 후속 서버 설계

이전 문서의 /api/v1/catalog/meta, /stores, /menus, /trends 등은 별도 서버를 도입할 때 검토할 제안이다. 인증과 즐겨찾기에 같은 기능의 자체 비밀번호·세션 서버를 중복 구축하지 않는다. SQL과 설정은 [DB 문서](database.md), [Supabase 연결 안내](supabase-setup.md)를 참고한다.