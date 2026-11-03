# Supabase 연결·운영

2026-11-03. 로그인·마이페이지는 Supabase Auth와 Postgres를 사용한다. 별도 Node 서버나 빌드는 필요 없다. 기존 메뉴·지도·트렌드는 공통 예시 데이터이며, 추가 전달된 JSON/CSV 5개는 사용하지 않는다.

## 연결 설정

`assets/js/config.js`에 Project URL과 **publishable key**를 설정한다. 이 키는 브라우저 배포용 공개 키로 프로젝트 코드에 포함할 수 있다. `sb_secret_`, `service_role`, DB 비밀번호는 절대 넣지 않는다. 코드도 해당 종류의 키를 거부한다. 키의 공개 여부와 별개로 실제 사용자 데이터는 RLS 정책으로 보호한다.

공식 SDK 2.118.0을 로컬 `assets/vendor/`에 포함했다. npm 설치나 CDN 연결은 필요 없지만 실제 인증·데이터 사용에는 Supabase 네트워크 연결이 필요하다. SDK 출처·라이선스는 [외부 라이브러리](third-party.md)에 기록했다.

## 초기 DB 적용

현재 연결한 `dmwpzbmcabwfyczjgqkt` 프로젝트에는 2026-11-03 초기 스키마와 RLS를 SQL Editor로 적용했다. 같은 프로젝트를 사용하는 조원은 초기 SQL을 다시 실행하지 않는다. Site URL `http://localhost:8000`과 아래 두 마이페이지 Redirect URL도 등록했다. Email 로그인·가입 활성화, 이메일 인증 유지 상태를 확인했다.

신규 프로젝트에서 `supabase/migrations/202611030001_profiles_favorites.sql`을 SQL Editor로 한 번 실행한다. 이미 테이블이 있는 프로젝트에서는 무조건 재실행하지 말고 스키마와 이력을 확인한다. Supabase CLI를 도입하면 이 파일을 마이그레이션으로 관리할 수 있다. SQL Editor의 수동 실행은 CLI 이력을 자동 생성하지 않는다.

생성하는 항목은 `public.profiles`, `public.favorites`, RLS 정책 5개, 가입 시 프로필 생성 트리거다. 기존 사용자에게도 프로필을 초기 생성한다. 기존 `docs/schema/*.sql`은 이전 SQLite 참고 자료이므로 Supabase에서 실행하지 않는다.

## 인증 설정

대시보드 Authentication에서 Email 로그인과 회원가입을 활성화한다. 이메일 인증은 유지한다. 로컬 개발의 Site URL은 `http://localhost:8000`을 기준으로 하고 허용 Redirect URL에는 아래 주소를 추가한다.

```text
http://localhost:8000/mypage.html
http://127.0.0.1:8000/mypage.html
```

다른 포트나 배포 주소를 사용할 때는 해당 주소의 정확한 `mypage.html` 경로를 등록한다. 로그인 복귀 파라미터 `returnTo`는 같은 디렉터리의 지도·검색·트렌드 페이지만 허용한다. 외부 주소는 무시한다.

비밀번호는 회원가입 화면에서 8~72자로 입력한다. 실제 최종 정책은 Supabase 설정도 충족해야 한다. PKCE 방식이므로 인증·재설정 메일은 요청한 브라우저에서 연다. 비밀번호 재설정은 SDK의 `PASSWORD_RECOVERY` 이벤트를 받은 로그인 상태에서만 표시하며, URL 파라미터만으로 변경 화면을 열지 않는다. 복구 메일을 열고 새 비밀번호를 설정하는 절차는 본인이 직접 진행한다.

이메일 발송은 Supabase 설정·발송 제한을 따른다. 기본 메일 서비스의 수신자 제한이나 rate limit이 걸리면 SMTP와 허용 수신자를 확인한다. 발송 제한을 피하려고 이메일 인증을 임의로 끄지 않는다.

## 구현 범위와 파일

| 파일 | 역할 |
| --- | --- |
| mypage.html / assets/css/mypage.css / assets/js/mypage.js | 로그인·가입·메일 안내·비밀번호 재설정·프로필·즐겨찾기·권한 상태 UI |
| assets/js/supabase-auth.js | Auth 초기화·세션 이벤트·프로필·즐겨찾기 DB 요청 |
| assets/js/api.js | 기존 페이지가 사용하는 공통 계약. 메뉴는 예시, 인증·저장은 Supabase로 위임 |
| assets/js/common.js | 로그인 이름·즐겨찾기 표시 갱신, 기존 상세창·사이드바 유지 |
| assets/js/config.js | 공개 프로젝트 설정 |
| supabase/migrations/202611030001_profiles_favorites.sql | Postgres 테이블·제약·RLS·트리거 |

세션은 Supabase SDK가 지속 저장·갱신하며 브라우저 저장소를 사용한다. 비밀번호를 직접 저장하지 않는다. 이전 `csm.demo.session.v1`과 `csm.demo.favorites.v1`는 실제 계정으로 이전하지 않는다. 로그아웃은 이 브라우저 세션을 대상으로 하며 저장한 즐겨찾기 자체는 DB에 유지한다.

## 장애 처리

- 설정 누락·잘못된 키·SDK 로드 실패: 로그인을 비활성화하고 연결 안내를 표시한다. 가짜 로그인 성공으로 대체하지 않는다.
- 잘못된 로그인·미인증 이메일·요청 제한: 각각 안내한다. 서버의 원문 오류나 토큰을 화면에 노출하지 않는다.
- DB 테이블·정책 문제: 로그인 상태와 별개로 저장 목록 오류를 표시하고 재시도를 제공한다. 불러오기 실패를 빈 목록으로 표시하지 않는다.
- 계정 변경: 즐겨찾기 캐시를 지우고 해당 계정의 목록을 읽는다. 이전 요청이 늦게 끝나도 다른 계정 화면에 반영하지 않는다.
- 메뉴 ID: 현재 공통 예시 ID를 저장한다. 메뉴 DB 도입 시 ID를 보존하고 알 수 없는 ID의 처리와 FK를 별도 설계한다.

## 검증 범위

2026-11-03 결과와 실제/모의 검증의 구분은 [검증 기록](validation-supabase.md)에 정리했다.

실제 프로젝트에서 `supabase/tests/rls.sql`을 실행해 본인 데이터 조회·저장·수정·삭제, 타인 프로필/즐겨찾기 접근 차단, 소유자 컬럼 보호, 비로그인 조회 차단을 확인했다. 테스트 사용자는 모두 ROLLBACK되었다. 공개 키로 Auth 설정 조회 200 및 비로그인 테이블 조회 거부도 확인했다.

실제 프로젝트의 스키마·RLS 검증과 격리된 브라우저 테스트를 구분해 기록한다. 모의 SDK 검사만으로 실제 이메일 도착·Supabase 인증·접근 제어가 검증됐다고 하지 않는다. 실제 회원가입·이메일 인증·비밀번호 변경은 테스트 소유자가 직접 확인한다.

## 공식 참고

- [API 키](https://supabase.com/docs/guides/getting-started/api-keys)
- [비밀번호 인증](https://supabase.com/docs/guides/auth/passwords)
- [사용자 프로필](https://supabase.com/docs/guides/auth/managing-user-data)
- [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
