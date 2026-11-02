# API 계약 초안

2026-11-02 · **서버 미구현**. URL은 제안이며 실제 요청을 보내지 않는다. 현재 화면은 `assets/js/api.js`의 비동기 mock 함수를 사용한다. 백엔드 프레임워크·인증 방식은 미정이다.

## 공통 규칙

- 기본 경로 제안: `/api/v1`. 같은 origin 배포를 우선 검토한다.
- JSON 필드 이름은 camelCase, ID는 안정적인 문자열이다. 화면 문구와 ID를 분리한다.
- 성공 응답 예: `{ "data": ... }`. 실패 예: `{ "error": { "code": "MENU_NOT_FOUND", "message": "메뉴를 찾을 수 없습니다." } }`.
- 화면용 `CafeAPI`는 서버 응답의 `data`를 꺼내 반환한다. 목록은 배열, 없는 단일 메뉴는 `null`로 정규화한다. 현재 mock은 외피 없이 이 형태로 바로 반환한다.
- `400` 입력 오류, `401` 인증 필요, `403` 접근 불가, `404` 자원 없음, `429` 요청 초과, `500` 내부 오류를 구분한다. 서버 오류와 정상 빈 배열을 구분한다.
- 클라이언트가 `userId`를 보내 계정을 선택하지 않는다. 사용자 식별은 서버에서 검증한 세션으로 한다.
- 실제 인증은 서버 세션 + HttpOnly 쿠키를 후보로 검토한다. 도입 시 Secure/SameSite/CSRF·만료 처리를 함께 설계한다. 현재 `sessionStorage` 데모를 이 구현으로 간주하지 않는다.
- 날짜는 실제 확인·집계 시각이 있을 때만 ISO 8601로 제공한다. 아래 메뉴·숫자는 모두 가상 예시다.

## 공통 메뉴 DTO

현재는 **메뉴별 최소 제공 사이즈의 대표 정보**를 평탄화해 전달한다. 여러 사이즈·온도를 수집할 때 DB는 별도 보존하고 API의 대표 사이즈·온도 선택 규칙을 먼저 정한다. 서로 다른 온도의 영양정보를 합치지 않는다.

```json
{
  "id": "demo-s-matcha",
  "brandId": "starbucks",
  "name": "예시 말차 크림 라떼",
  "categoryTags": ["caffeine", "latte"],
  "sizeLabel": "최소 사이즈(예시)",
  "volumeMl": 350,
  "temperature": "ICE",
  "priceKrw": 6000,
  "sugarG": 25,
  "caloriesKcal": 240,
  "tone": "matcha",
  "isNew": true,
  "seasonal": true,
  "sourceUrl": null,
  "checkedAt": null,
  "isDemo": true
}
```

가격은 원, 당류는 g, 칼로리는 kcal. 미확인은 `null`이며 0으로 채우지 않는다. `tone`은 컵 일러스트 색상용으로 실제 메뉴 분류가 아니다. 실제 데이터 전환 시 `isDemo: false`, 검증된 출처·확인일을 제공하고 화면의 데모 안내도 검토한다.

## 요청·응답과 화면 함수

| 목적 | 요청 | 주요 입력 | `data` 응답 | 현재 CafeAPI |
| --- | --- | --- | --- | --- |
| 필터 메타데이터 | GET `/catalog/meta` | 없음 | `{ brands: [{ id, name }], categories: [{ id, name }] }` | `getBrands()`, `getCategories()`로 분리 반환 |
| 매장 | GET `/stores` | `lat`, `lng`, `radiusM`(m), 선택 `brandId` | `[{ id, brandId, name, latitude, longitude }]` | `getStores()` |
| 메뉴 검색 | GET `/menus` | 선택 `brandId`, `category`, `q`, `isNew` | 메뉴 DTO 배열 | `getMenus({ brandId, category, q, isNew })` |
| 메뉴 상세 | GET `/menus/{menuId}` | 메뉴 ID | 메뉴 DTO | `getMenu(menuId)` |
| 트렌드 | GET `/trends` | 집계·정렬 미정 | 트렌드 DTO 배열 | `getTrends()` |
| 로그인 | POST `/auth/login` | 최종 인증 방식에 따라 결정 | `{ id, displayName }` + 서버 세션 | mock 전용 `login({ displayName })` |
| 현재 사용자 | GET `/me` | 서버 세션 | `{ id, displayName }` | `getSession()`; 서버 401은 `null`로 변환 |
| 로그아웃 | POST `/auth/logout` | 서버 세션 | `{ loggedOut: true }` | `logout()` |
| 즐겨찾기 조회 | GET `/me/favorites` | 서버 세션 | 메뉴 DTO 배열 | `getFavorites()` |
| 즐겨찾기 저장 | PUT `/me/favorites/{menuId}` | 서버 세션, 메뉴 ID | `{ menuId, saved: true }` | `toggleFavorite(menuId)`가 상태에 따라 PUT/DELETE 선택 |
| 즐겨찾기 삭제 | DELETE `/me/favorites/{menuId}` | 서버 세션, 메뉴 ID | `{ menuId, saved: false }` | 위와 같음 |

실제 로그인에 표시 이름만 보내면 안 된다. 이메일/비밀번호 또는 소셜 로그인 중 선택 후 요청 형식을 정한다. 회원가입 API는 그 결정 이후 추가한다. 실제 비밀번호는 브라우저 저장소에 보관하지 않는다.

`isFavorite()`와 `getCompare()/toggleCompare()/clearCompare()`는 현재 동기식 UI 보조 함수다. 서버 도입 후 즐겨찾기는 조회 결과 캐시를 기준으로 표시하고 저장 요청 완료 후 갱신한다. 이들을 단순히 Promise로 바꾸면 카드 UI가 깨지므로 공개 계약 변경을 팀과 협의한다. 비교 목록은 당분간 로컬 선택 상태로 유지할 수 있다.

현재 `getStores()`의 `x/y`는 가상 지도 배치 좌표(%)다. 실제 위·경도로 재사용하지 않는다. 실제 지도 연결 시 지도 SDK에 위·경도를 전달한다.

## 트렌드 DTO 제안

```json
{
  "id": "demo-trend-matcha",
  "title": "쌉싸름한 말차의 매력",
  "keyword": "말차",
  "description": "예시 콘텐츠",
  "label": "키워드 예시",
  "tone": "matcha",
  "sourceUrl": null,
  "period": null
}
```

실제 트렌드에는 근거 종류·집계 기간·산정 기준을 추가한다. 공식 신메뉴와 검색 관심도 상승은 다른 정보다. 초기에는 검수한 콘텐츠 목록을 사용할 수도 있으며 유행 측정 방식은 미정이다. 랜덤 추천 API는 만들지 않는다.

## 데이터 저장 위치와의 관계

메뉴가 JSON 파일이든 DB든 API 응답은 동일하게 유지한다. 크롤러는 검증된 공통 데이터를 생성하고 서버가 제공한다. 크롤러 실행 API를 일반 사용자에게 열지 않는다. 출처·제공량·HOT/ICE·가격 기준을 보존하고 수집 오류로 정상 메뉴를 일괄 덮어쓰지 않는다.

```javascript
const menus = await CafeAPI.getMenus({ brandId: "starbucks", category: "latte" });
const menu = await CafeAPI.getMenu("demo-s-matcha");
// 현재는 mock 데이터. 서버 연결 시 api.js 내부를 우선 교체한다.
```
