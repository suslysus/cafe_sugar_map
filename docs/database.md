# DB·메뉴 저장소 설계안

2026-11-02 · **제안 문서. DB·서버·크롤러는 만들거나 연결하지 않았다.** 메뉴 저장 위치와 인증 기술은 팀 결정이 필요하다.

## DB와 테이블 분리

로그인과 메뉴가 다르다고 DB를 두 개 운영할 필요는 없다. 기본 제안은 **서버 DB 하나 안에 계정·세션·즐겨찾기·메뉴 테이블을 분리**하는 것이다. 사용자마다 테이블을 만드는 것도 아니다. 각 사용자는 `users`의 행이다.

현재 기초본은 공통 예시 JS와 브라우저 데모 저장소만 사용한다.

## 선택 A — 인증 DB + 메뉴 JSON

- 서버 DB: `users`, `sessions`, `favorites`.
- 메뉴: 수집·검수한 공통 JSON. 서버 메뉴 API가 읽어서 DTO로 응답한다.
- 장점: 초기 구성이 단순하며 메뉴가 적고 갱신이 드물 때 관리하기 쉽다.
- 제약: 동시 수정·검색·자동 갱신 이력·무결성을 별도 관리한다. JSON은 검증 후 교체한다.
- 즐겨찾기는 JSON에서도 유지되는 안정적인 `menu_id`를 저장하고 서버가 메뉴 존재 여부를 검사한다.
- ‘로컬 메뉴’는 서버의 배포 파일을 뜻한다. 방문자가 개발자 PC 파일을 직접 읽는 것이 아니다. 정적 파일로 배포하면 데이터는 공개되며 갱신 시 재배포가 필요하다.

## 선택 B — 같은 DB에 메뉴 테이블 추가

- A의 계정 테이블 + `brands`, `menus`, `menu_servings`, `categories`, `menu_category_tags`.
- 장점: 수집 결과 갱신·브랜드/카테고리 검색·관계 관리가 편리하다.
- 제약: 초기 수집·정규화·마이그레이션이 추가된다.
- API와 기존 메뉴 ID를 유지하면서 A→B로 전환할 수 있다.
- 현재 규모에서 두 DB의 운영 복잡성은 우선 도입하지 않는 방향을 제안한다.

## 계정 테이블

| 테이블 | 주요 필드 | 역할 |
| --- | --- | --- |
| users | id PK, email UNIQUE nullable, password_hash nullable, display_name, created_at | 사용자 정보. 인증 방식 선택 후 자격 증명 필드 확정 |
| sessions | token_hash PK, user_id FK, expires_at, created_at | 서버 세션. 토큰 원문 대신 해시 보관 예시 |
| favorites | user_id FK, menu_id, created_at / PK(user_id, menu_id) | 사용자별 중복 없는 저장 목록 |

비밀번호 원문은 저장하지 않는다. 인증 라이브러리로 해시 생성·검증을 구현하며 SQL 자체는 인증하지 않는다. 소셜 인증을 선택하면 provider/subject 관계 등 설계를 추가한다.

## 메뉴 DB 추가 테이블

| 테이블 | 주요 필드 | 역할 |
| --- | --- | --- |
| brands | id PK, name | 대상 브랜드 |
| menus | id PK, brand_id FK, source_product_id, name, official_is_new nullable, seasonal nullable, released_at nullable, first_seen_at, last_seen_at, source_url | 원본 상품 식별·메뉴 정보 |
| menu_servings | id PK, menu_id FK, size_label, volume_ml nullable, temperature, price_krw nullable, sugar_g nullable, calories_kcal nullable, source_url, checked_at | 사이즈·HOT/ICE별 값 |
| categories | id PK, name | 검색 분류 |
| menu_category_tags | menu_id FK, category_id FK / 복합 PK | 복수 분류와 메뉴 연결 |

관계: `users 1:N sessions`, `users 1:N favorites`, `brands 1:N menus`, `menus 1:N menu_servings`, `menus N:M categories`. B에서는 `favorites.menu_id → menus.id` 관계도 추가한다.

수집 로그·변경 이력·트렌드 근거 테이블은 수집 방식 결정 후 확장한다. 가상 매장 x/y를 실제 위치로 저장하지 않는다. 매장 API·지도 제공처 선택 후 매장 저장 여부를 정한다.

## 데이터 기준

- 이름 대신 **내부 ID + 브랜드 원본 상품 ID**로 식별한다. 원본 ID가 없으면 별도 매핑한다.
- 기본 레시피·옵션 추가 및 변경 없음. 사이즈·온도를 보존하고 최소 제공 사이즈 선택 규칙을 합의한다.
- 1회 제공량과 100ml 기준을 혼합하지 않는다. 임의 환산해 최소 사이즈를 채우지 않는다.
- 가격은 원, 당류는 g, 칼로리는 kcal. 누락은 `NULL`, 확인된 0은 숫자 0이다.
- `first_seen_at`은 최초 발견 시각이다. **출시일이 아니며 첫 수집에서 모든 메뉴를 신메뉴로 표시하지 않는다.**
- 공식 NEW·출시일·시즌 여부는 근거가 있을 때만 채운다. 트렌드 인기 점수와 구분한다.
- 수집 실패·구조 변경으로 메뉴가 급감하면 갱신을 보류하고 이전 정상 데이터를 유지한다.
- 매장·주문 채널·교환권 가격을 섞지 않는다. 실제 확인 없이 품절·구매 가능 상태를 단정하지 않는다.

## SQL과 전환

`schema/accounts.sql`과 `schema/catalog.sql`은 **SQLite 문법 설계 예시**다. 앱에서 실행하지 않으며 DBMS를 확정한 것이 아니다.

1. A를 택하면 계정 테이블과 검증된 메뉴 JSON을 서버에서 사용한다.
2. B를 택하면 **기존 메뉴 ID 그대로** DB에 이관한다.
3. A의 JSON 참조 때문에 `favorites.menu_id`에는 메뉴 FK가 없다. B 전환 시 고아 즐겨찾기를 정리한 뒤 FK 추가 마이그레이션을 작성한다. SQLite에서는 테이블 재생성이 필요할 수 있다. 두 SQL을 실행한다고 이 FK가 자동 추가되지는 않는다.
4. API 응답·공통 JS 계약과 네 페이지를 검증한다.

세션·DB 파일·사용자 정보는 GitHub에 올리지 않는다. `demo-user`를 실제 사용자 ID로 사용하지 않는다.
