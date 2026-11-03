# 현재 API 계약

2026-11-03. 메뉴·지도·트렌드는 기존 예시 데이터이며, 인증·프로필·즐겨찾기는 Supabase SDK로 연결한다. 각 페이지는 CafeAPI 공개 함수를 호출한다. 별도 /api/v1 서버는 현재 없다.

## 인증·프로필·저장

| CafeAPI 함수 | 입력·반환 | 실제 연결 |
| --- | --- | --- |
| authReady | 초기화 Promise. 설정 실패도 상태로 보존 | CafeAuth.ready |
| getAuthStatus() | initialized/configured/error/code/dataError/recovery | 연결·복구 UI 상태 |
| getSession() | Promise<User 또는 null> | Supabase Auth 세션 + profiles 표시 이름 |
| login({ email, password }) | Promise<User> | auth.signInWithPassword |
| signUp({ email, password, displayName }) | Promise<{ signedIn }> | auth.signUp, display_name 메타데이터 |
| logout() | Promise<void> | auth.signOut(scope: local) |
| updateProfile(displayName) | Promise<User> | profiles 본인 행 UPDATE |
| getFavorites() | Promise<메뉴 DTO 배열> | favorites 조회 후 현재 공통 메뉴 ID 연결 |
| toggleFavorite(menuId) | Promise<저장 여부 boolean> | 본인 favorites INSERT/DELETE |
| isFavorite(menuId) | 동기 boolean 캐시 조회 | 로그인·저장 변경 이벤트로 갱신 |
| resendConfirmation(email) | Promise<void> | auth.resend(type: signup) |
| sendPasswordReset(email) | Promise<void> | auth.resetPasswordForEmail |
| updatePassword(password) | Promise<void> | 복구 이벤트로 인증된 상태에서 auth.updateUser |

User 형태는 { id, email, displayName, isDemo: false }다. 식별자는 Supabase 사용자 UUID이며 표시 이름으로 계정을 나누지 않는다. 회원가입의 signedIn:false는 이메일 인증 안내를 표시한다. 비밀번호는 함수 호출에만 사용하고 앱 코드가 직접 저장하지 않는다.

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

getBrands(), getCategories(), getStores(), getMenus({ brandId, category, q, isNew }), getMenu(menuId), getTrends()는 예시 데이터에 대한 Promise를 반환한다. getCompare()/toggleCompare()/clearCompare()는 기존 로컬 비교 선택을 유지한다.

메뉴 DTO는 { id, brandId, name, categoryTags, sizeLabel, volumeMl, temperature, priceKrw, sugarG, caloriesKcal, tone, isNew, seasonal, sourceUrl, checkedAt, isDemo }다. 단위는 원/g/kcal이고 미확인은 null이다. 현재 모든 메뉴는 isDemo:true다. 공유받은 JSON/CSV 5개는 사용하지 않는다.

실제 메뉴 수집·저장소로 바꾸더라도 메뉴 ID와 DTO를 유지한다. 저장소에 남았지만 현재 카탈로그에서 찾을 수 없는 메뉴는 getFavorites() 결과에서 제외된다. 실제 메뉴를 도입할 때 해당 항목의 표시·삭제·ID 이관 규칙을 추가해야 한다.

## 후속 서버 설계

이전 문서의 /api/v1/catalog/meta, /stores, /menus, /trends 등은 별도 서버를 도입할 때 검토할 제안이다. 인증과 즐겨찾기에 같은 기능의 자체 비밀번호·세션 서버를 중복 구축하지 않는다. SQL과 설정은 [DB 문서](database.md), [Supabase 연결 안내](supabase-setup.md)를 참고한다.
