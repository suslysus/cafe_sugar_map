# Supabase DB 설계

2026-11-03 결정: 계정과 앱 저장소는 Supabase를 사용한다. 로그인·마이페이지 범위부터 구현하며 메뉴는 기존 공통 예시를 유지한다.

## 현재 테이블

| 테이블 | 주요 필드 | 책임 |
| --- | --- | --- |
| auth.users | Supabase 관리 사용자 ID·인증 정보 | 이메일·비밀번호 인증. 앱이 비밀번호를 직접 저장하지 않음 |
| public.profiles | id UUID PK/FK→auth.users, display_name(1~24자), created_at | 사용자 표시 이름 |
| public.favorites | user_id UUID FK→auth.users, menu_id TEXT, created_at, PK(user_id, menu_id) | 계정별 중복 없는 즐겨찾기 |

Supabase Auth가 비밀번호·인증 세션을 관리하므로 기존 SQLite 예시의 users/sessions 테이블을 별도로 만들지 않는다. auth.users의 신규 가입 트리거가 profiles를 생성하고, 사용자 삭제 시 FK의 ON DELETE CASCADE로 연결된 프로필·즐겨찾기도 정리된다. 계정 삭제 기능 자체는 이번 UI 범위에 포함하지 않는다.

## 권한

profiles/favorites 모두 RLS를 활성화한다. 비로그인 anon 역할은 두 테이블을 조회·수정할 수 없다. authenticated 사용자는 JWT의 auth.uid()와 같은 ID의 프로필을 읽고 표시 이름만 수정할 수 있다. 프로필 소유자 ID·생성일을 수정하거나 프로필을 직접 생성·삭제할 권한은 주지 않는다.

즐겨찾기는 본인의 user_id 행만 조회·추가·삭제할 수 있다. 다른 사용자 ID를 요청에 넣어도 DB가 거부한다. 중복 저장은 복합 기본 키로 막는다. 클라이언트는 INSERT/DELETE로 처리하므로 불필요한 UPDATE 정책을 열지 않는다.

프로필 생성 함수는 security definer + 빈 search_path를 사용하며 브라우저에서 직접 실행할 권한을 주지 않는다. 로그인 이름이나 user_metadata를 권한 판단에 사용하지 않는다.

## 메뉴와의 연결

메뉴는 당분간 assets/js/mock-data.js를 사용한다. favorites.menu_id에는 같은 공통 메뉴 ID를 저장하며 현재 메뉴 FK는 없다. 메뉴를 Supabase에 이관할 때 ID를 유지하고 실제 메뉴 테이블·제공형태·분류와 FK를 별도 마이그레이션으로 추가한다.

크롤링·메뉴 데이터는 다른 페이지 담당과 협의할 후속 범위다. 이번에는 메뉴 원본 파일 5개를 가져오거나 새 크롤러를 만들지 않는다. 가격·영양정보의 최소 사이즈/HOT·ICE/기본 레시피 기준은 유지한다.

## 마이그레이션과 검증

현재 실행 대상은 supabase/migrations/202611030001_profiles_favorites.sql이다. docs/schema/accounts.sql과 catalog.sql은 과거 SQLite 참고 자료이며 Supabase에서 실행하지 않는다. 배포 방법과 인증 설정은 [Supabase 안내](supabase-setup.md)를 따른다.

supabase/tests/rls.sql은 postgres 역할로 가상 사용자 2명을 한 트랜잭션에서 생성해 본인 데이터 CRUD·타인 데이터 차단·소유자 컬럼 보호·익명 조회 차단을 확인한 뒤 ROLLBACK하는 검사다. 실제 이메일 발송이나 비밀번호 생성은 하지 않으며 테스트 사용자가 남지 않는지도 확인한다. 이 DB 검사는 실제 이메일 인증 흐름 검증과는 별개다.
