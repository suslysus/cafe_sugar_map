# Cafe Sugar Map

주변 카페의 메뉴를 찾고 가격·당류·칼로리를 확인하는 웹프로그래밍 13조 프로젝트입니다.

**2026-11-03 · HTML / CSS / JavaScript · 로그인·마이페이지: Supabase Auth + Postgres**

> [!WARNING]
> **이번 기초본 업로드까지만 main에 직접 반영합니다. 이후 팀원 전원은 개인 작업 브랜치에서 수정 → push → Pull Request(PR) → 카카오톡 작업 보고·검토 요청 → 다른 팀원 확인 후 main에 merge하는 순서를 지켜 주세요.**
>
> main에서 직접 개발하거나 `git push --force`하지 마세요. `git pull`은 다른 사람의 변경을 내 컴퓨터에 받는 명령이고, PR은 내 변경을 main에 합쳐 달라는 요청입니다. 두 작업은 다릅니다.

## 1. 현재 구현과 연결 범위

- 1·2·3페이지의 지도·메뉴·트렌드 데이터는 기존 가상 예시입니다. 별도 전달된 JSON/CSV 5개는 사용하지 않습니다.
- 4페이지는 이메일·비밀번호 로그인, 이메일 인증 후 이름·비밀번호를 입력하는 회원가입, 인증 메일 재요청, 비밀번호 재설정, 로그아웃, 표시 이름 수정, 계정별 즐겨찾기를 Supabase로 연결합니다.
- 메뉴 목록·매장 위치·가격·영양값·NEW 표시는 실제 정보가 아닙니다. 랜덤 추천은 제외했습니다.
- 계정은 Supabase Auth, 프로필과 즐겨찾기는 Supabase Postgres에 저장합니다. 초기 설정은 [Supabase 안내](docs/supabase-setup.md)를 따릅니다. 설정·테이블이 준비되지 않으면 실제 저장은 사용할 수 없습니다.
- URL·publishable key는 `assets/js/config.js`에 둡니다. 브라우저 공개 키이므로 코드에 포함할 수 있지만 **secret/service_role·DB 비밀번호는 넣지 않습니다.** RLS가 사용자별 접근을 제한합니다.
- Supabase SDK가 브라우저 저장소의 인증 세션을 관리합니다. 비밀번호를 직접 저장하지 않으며 예전 데모 계정·즐겨찾기는 실제 계정으로 옮기지 않습니다.
- 비교 선택 목록만 기존 브라우저 로컬 저장을 유지합니다. 별도 비교 화면·길 안내는 추가 범위입니다.

## 2. 사이트 주소·배포·실행 방법

사이트 주소는 **[https://suslysus.github.io/cafe_sugar_map/](https://suslysus.github.io/cafe_sugar_map/)**이며, 로그인·회원가입은 [마이페이지](https://suslysus.github.io/cafe_sugar_map/mypage.html)에서 이용합니다. 배포된 사이트는 개인 PC에서 서버를 켜지 않아도 접속할 수 있습니다.

배포는 **GitHub Pages**를 사용합니다. [저장소 Settings → Pages](https://github.com/suslysus/cafe_sugar_map/settings/pages)의 Source는 `Deploy from a branch`, Branch는 `main`, 폴더는 `/ (root)`로 설정했습니다. 별도 설치·빌드 명령은 없습니다.

개인 브랜치 수정 → PR → 팀원 검토·승인 → main에 merge → [Actions](https://github.com/suslysus/cafe_sugar_map/actions)의 `pages build and deployment` 성공 순서로 배포합니다. Approve나 개인 브랜치 push만으로는 사이트에 반영되지 않습니다. 상세 설정과 장애 확인은 [배포 안내](docs/deployment.md)를 참고하세요. 정기 크롤링용 Actions는 아직 구성하지 않았습니다.

로컬에서 개발할 때는 저장소 폴더에서 정적 서버를 실행합니다.

```bash
python -m http.server 8000
```

브라우저에서 **http://localhost:8000**을 엽니다. Windows에서 `python`이 없다면 `py -m http.server 8000`을 사용하거나 VS Code Live Server로 `index.html`을 여세요. 종료는 터미널에서 `Ctrl+C`입니다.

HTML을 직접 여는 `file://` 대신 정적 서버를 사용합니다. 로컬 인증 복귀 주소는 `localhost:8000/mypage.html`과 `127.0.0.1:8000/mypage.html`을 허용해 두었습니다. 다른 포트는 Supabase 허용 목록에도 추가해야 합니다. 실제 이메일 인증은 이용 중인 주소에서 메일을 요청하고 같은 브라우저에서 확인하세요.

## 3. 페이지와 담당 파일

| 페이지 | 담당 | HTML | 개인 CSS / JS | 현재 동작 |
| --- | --- | --- | --- | --- |
| 지도·메뉴 | 강민재 | `index.html` | `assets/css/map.css`, `assets/js/map.js` | 예시 지도 핀 선택, 브랜드별 메뉴, 공통 상세창 |
| 메뉴 검색 | 강다은 | `search.html` | `assets/css/search.css`, `assets/js/search.js` | 이름 검색, 브랜드·카테고리 필터, 즐겨찾기, 비교 선택 목록 |
| 트렌드·신메뉴 | 현준혁 | `trends.html` | `assets/css/trends.css`, `assets/js/trends.js` | 예시 키워드→검색 연결, 신메뉴 브랜드 필터, 공통 상세창 |
| 로그인·마이페이지 | 한정원 | `mypage.html` | `assets/css/mypage.css`, `assets/js/mypage.js` | 이메일 로그인·회원가입·재설정, 프로필 편집, 계정별 즐겨찾기, 위치 권한 상태 |

왼쪽 사이드바로 네 페이지를 이동합니다. 모바일에서는 상단 메뉴 버튼으로 사이드바를 엽니다.

```text
index.html / search.html / trends.html / mypage.html
assets/
  css/
    common.css           공통 디자인·사이드바·카드·상세창
    map.css              강민재
    search.css           강다은
    trends.css           현준혁
    mypage.css            한정원
  js/
    mock-data.js         공통 예시 데이터·브랜드·카테고리 ID
    api.js               메뉴는 예시, 인증·즐겨찾기는 Supabase 연결
    common.js            사이드바·헤더·카드·상세창·알림
    config.js            공개 Supabase 연결 설정
    supabase-auth.js     실제 인증·프로필·즐겨찾기 어댑터
    map.js / search.js / trends.js / mypage.js
  (각 페이지는 자신의 CSS·JS를 사용)
docs/
  api.md                 현재 SDK 호출·화면 연결 계약
  database.md            Supabase 테이블·RLS 설계
  supabase-setup.md      실제 Supabase 초기화·인증 설정
  schema/accounts.sql    이전 SQLite 참고 예시 (Supabase 실행 금지)
  schema/catalog.sql     이전 SQLite 참고 예시 (Supabase 실행 금지)
supabase/
  migrations/            현재 Postgres 초기 스키마
  tests/rls.sql           가상 사용자 롤백 방식의 DB 권한 검사
```

**각자 개인 파일부터 수정해 주세요.** 공통 파일은 한정원을 기본 조율 창구로 하되, 변경 전 팀과 협의합니다. 수집 담당의 추가 분담과 메뉴 저장 방식은 아직 확정하지 않았습니다. 계정·즐겨찾기는 Supabase로 결정했습니다.

## 4. 팀원 필독: 작업·동기화·merge 순서

### 처음 받는 사람

```bash
git clone https://github.com/suslysus/cafe_sugar_map.git
cd cafe_sugar_map
git switch main
git pull --ff-only origin main
```

### 작업을 시작할 때

`git status`로 저장되지 않은 변경이 없는지 확인합니다. 변경이 있다면 현재 작업 브랜치에서 커밋하거나 stash로 보관한 뒤 이동하세요.

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/minjae-map
```

개인 브랜치 예시: `feature/minjae-map`, `feature/daeun-search`, `feature/junhyeok-trends`, `feature/jeongwon-mypage`. 이미 만든 브랜치에는 `git switch 브랜치이름`으로 이동하고 `-c`를 다시 쓰지 않습니다.

### 수정 후 올릴 때

```bash
git status
git diff
git add index.html assets/css/map.css assets/js/map.js
git commit -m "feat: connect map store selection"
git push -u origin feature/minjae-map
```

경로와 브랜치는 **본인 담당 파일·브랜치로 바꿔서** 실행합니다. 필요한 파일만 올리세요. 공통 파일을 수정했다면 PR에 변경 이유와 영향받는 페이지를 적습니다.

### main의 최신 변경을 내 브랜치에 받을 때

작업 내용을 먼저 커밋하거나 stash로 보관하고 **본인 작업 브랜치에서** 실행합니다.

```bash
git fetch origin
git merge origin/main
```

충돌이 나면 충돌 표시를 확인하고 해당 담당자와 함께 해결합니다. 무조건 내 쪽/상대 쪽으로 덮어쓰지 마세요. 해결한 파일을 `git add`하고 merge 커밋을 완료한 뒤 네 페이지를 확인하고 push합니다. 중단하려면 `git merge --abort`로 이번 merge만 취소할 수 있습니다.

### main에 합칠 때

1. GitHub에서 **base: main / compare: 본인 브랜치**로 PR을 만듭니다.
2. 수정한 파일별 변경 내용, 추가·변경·삭제한 기능, 확인한 동작, 공통 파일 변경 여부를 적습니다.
3. **카카오톡 단체방에도 파일별 작업 내용과 PR 링크를 올리고 검토를 요청합니다.** 아래 양식을 참고합니다.
4. 다른 팀원이 PR을 검토하고 GitHub에서 Approve 또는 확인 댓글을 남긴 뒤, 단체방에도 검토 결과를 공유합니다. **검토 확인 없이 바로 merge하지 않습니다.**
5. merge 후 단체방에 완료 사실과 해당 PR을 알리고, 각자 main으로 이동해 `git pull --ff-only origin main`으로 받습니다.
6. 다음 작업은 최신 main에서 새 브랜치를 만들어 시작합니다.

### PR 생성 후 카카오톡 작업 보고 (필수)

**작업 단위의 수정이 끝나 PR을 올리면 단체방에도 반드시 보고합니다.** 파일 이름만 적거나 ‘수정했습니다’로 끝내지 말고, 다른 사람이 무엇을 확인하면 되는지 알 수 있게 씁니다. 여러 파일을 수정했다면 파일별로 어떤 부분이 바뀌었는지 구분합니다. HTML뿐 아니라 CSS·JS·데이터·문서 수정도 동일하게 공유합니다.

보고에 포함할 내용:

- 수정한 파일 경로와 각 파일에서 바꾼 부분.
- 추가·변경·삭제한 기능 또는 화면 동작. 기능 변경이 없으면 ‘기능 변경 없음, 문구/스타일/문서만 수정’처럼 표시.
- 공통 파일이나 다른 페이지에 영향이 있는지.
- main으로 합치기 위해 올린 **실제 PR 링크**와 검토 요청.

아래는 보고 형식 예시이며, 실제로 구현한 변경을 주장하는 내용이 아닙니다. 본인이 수정한 파일·동작으로 바꿔서 사용하세요.

```text
[작업 공유 / 한정원]

mypage.html에서 즐겨찾기 목록의 안내 문구와 빈 목록 영역을 수정했습니다.
assets/js/mypage.js에서는 저장한 메뉴가 없을 때 안내가 표시되도록 기능을 추가했습니다.
공통 파일 수정은 없고 마이페이지에만 영향이 있습니다.

main에 merge하려고 PR 올렸습니다.
PR: [실제 PR 링크]

시간 되시는 분 확인해 주시고, 문제없으면 GitHub에서 Approve나 확인 댓글 남겨 주세요.
단톡에도 ‘PR 확인했습니다. merge해도 됩니다’처럼 체크해 주시면 감사하겠습니다.
```

검토자는 변경 파일과 실제 동작을 확인한 뒤 결과를 남깁니다. 수정이 필요하면 어떤 파일의 어떤 동작을 고쳐야 하는지 알려 주세요. 작성자는 보완한 내용도 단체방에 공유하고 다시 확인을 요청합니다.

단체방에 올릴 전체 공지문은 [협업 공지문](docs/team-notice.md)에 있습니다. 이 문서는 복사해 보낼 초안이며 카카오톡으로 자동 전송되지 않습니다.

> [!IMPORTANT]
> **브랜치 이름만 나눈다고 충돌이 없어지는 것은 아닙니다.** `common.css`, `common.js`, `api.js`, `mock-data.js`, README, API·DB 문서를 동시에 고치기 전에 서로 알려 주세요. 이 내용은 협업 규칙이며 GitHub의 기술적 브랜치 보호 설정은 별도로 적용하지 않았습니다.

## 5. 서로의 페이지를 깨뜨리지 않으려면

- **파일명·경로를 임의로 바꾸지 마세요.** 변경 시 사이드바 링크, HTML의 CSS/JS 경로, 로그인 복귀 경로까지 함께 수정합니다.
- HTML의 `body data-page`, `app-sidebar`, `app-topbar`와 스크립트 순서를 유지하세요: `mock-data.js → config.js → Supabase SDK → supabase-auth.js → api.js → common.js → 개인 JS`.
- 개인 JS는 `CafeAPI`로 데이터를 받습니다. 페이지마다 메뉴 배열이나 서버 URL을 중복 관리하지 않습니다. `CafeMock` 직접 참조는 공통 구현 내부에만 둡니다.
- **메뉴·브랜드·카테고리 ID는 공통 계약입니다.** 변경 시 검색 URL·즐겨찾기·비교 선택·API·DB도 맞춥니다. 메뉴 이름으로 식별하지 마세요.
- 기초본의 `categoryTags`는 복수 태그입니다. 최종 분류는 팀에서 정합니다. 디카페인과 무카페인은 구분하세요.
- 영양정보는 **제공 사이즈·HOT/ICE·기본 레시피**와 함께 관리합니다. 미확인은 `null`로 두고 ‘확인 중’으로 표시합니다. 0과 미확인은 다릅니다.
- 외부·사용자 문자열을 `innerHTML`에 그대로 넣지 마세요. 현재 템플릿에서는 `CafeUI.escape()`를 사용합니다. 외부 URL도 허용 프로토콜을 검증합니다.
- `.env`, 비밀번호, 사용자 세션 토큰, 비밀 API 키, DB 비밀번호·파일, 개인 정보는 커밋하지 않습니다. Supabase publishable key만 공개 설정에 사용합니다. 데모와 실데이터를 구분합니다.
- 사용자 권한은 Supabase Auth의 JWT와 DB의 RLS로 검사합니다. 브라우저 저장소 값이나 표시 이름으로 접근 권한을 판단하지 마세요.
- 크롤러는 별도 작업으로 두고 방문자 페이지 로딩 때마다 사이트를 긁지 않습니다. 사이트별 접근·이용 조건을 확인하고 과도한 요청을 피합니다.
- 수집 실패를 메뉴 판매 종료로 처리하지 않습니다. 원본 상품 ID·출처·확인 시각을 보존하고 최초 발견일을 출시일로 쓰지 않습니다.

## 6. 실제 연결과 API 계약

페이지는 `CafeAPI`를 사용합니다. 로그인·프로필·즐겨찾기는 `supabase-auth.js`가 공식 SDK를 통해 Supabase에 요청합니다. 기존 `/api/v1/...`는 별도 서버를 도입할 때의 제안이며 현재 제공하지 않습니다.

| 기능 | 화면에서 호출 | 실제 저장·인증 |
| --- | --- | --- |
| 로그인 | `login({ email, password })` | Supabase Auth |
| 가입 메일 인증 / 가입 완료 | `requestSignupVerification(email)` / `completeSignup({ displayName, password })` | Supabase Auth + profiles |
| 세션 / 로그아웃 | `getSession()` / `logout()` | Supabase Auth SDK |
| 표시 이름 수정 | `updateProfile(displayName)` | `public.profiles` |
| 즐겨찾기 조회·추가·삭제 | `getFavorites()` / `toggleFavorite(menuId)` | `public.favorites` + RLS |
| 인증 메일 / 비밀번호 재설정 | `resendConfirmation(email)` / `sendPasswordReset(email)` / `updatePassword(password)` | Supabase Auth |
| 메뉴·지도·트렌드 | 기존 `getMenus/getMenu/getStores/getTrends` | 기존 공통 예시 데이터 |

자세한 계약은 [API 문서](docs/api.md), 연결 설정은 [Supabase 안내](docs/supabase-setup.md)를 참고합니다. `isFavorite()`는 동기 캐시 조회 계약을 유지하고 Auth 준비·변경 이벤트로 화면을 갱신합니다. 이를 임의로 Promise로 바꾸지 마세요.

## 7. DB 구성

**Supabase 프로젝트 하나에서 Auth와 Postgres를 함께 사용**합니다. 사용자·비밀번호·인증 세션은 Supabase Auth가 관리하며, 앱이 별도 비밀번호·세션 테이블을 만들지 않습니다.

| 저장 위치 | 저장하는 내용 |
| --- | --- |
| `auth.users` (Supabase 관리) | 계정 ID·이메일·인증 정보 |
| `public.profiles` | 계정 ID, 표시 이름, 생성 시각 |
| `public.favorites` | 계정 ID, 메뉴 ID, 저장 시각. 계정·메뉴 조합의 중복 저장 방지 |

가입 시 트리거가 프로필을 생성합니다. `profiles`와 `favorites`에는 **RLS(행 단위 접근 제한)**를 적용해 비로그인 접근과 다른 계정 데이터 접근을 차단합니다. 로그인한 사용자는 본인 표시 이름을 수정하고 본인 즐겨찾기를 조회·추가·삭제할 수 있습니다. 브라우저 연결 설정은 `assets/js/config.js`의 공개 publishable key를 사용하며 관리자 비밀 키·DB 비밀번호는 넣지 않습니다.

메뉴는 당분간 기존 공통 예시 파일을 유지합니다. 나중에 메뉴 테이블을 추가하더라도 메뉴 ID와 화면 API 계약을 보존합니다. 이전 JSON/CSV 5개는 이번 작업에서 사용하지 않습니다.

[DB 설계](docs/database.md)와 `supabase/migrations/202611030001_profiles_favorites.sql`이 현재 기준입니다. **`docs/schema/accounts.sql`·`catalog.sql`은 과거 SQLite 참고 자료이며 Supabase에 실행하지 않습니다.**

## 8. PR 전 확인할 동작

- 사이드바에서 네 페이지 이동과 현재 페이지 표시.
- 지도 핀 선택→오른쪽 카페·메뉴 변경, 상세창 열기·닫기.
- 검색·필터·결과 없음·초기화, 비교 선택·해제와 페이지 이동 후 목록 유지.
- 신메뉴 필터와 트렌드→검색 이동. 랜덤 추천 제외 여부.
- 비로그인 즐겨찾기→로그인→원래 페이지 복귀, 계정별 저장→마이페이지 조회·삭제·새로고침 유지.
- 회원가입·이메일 인증, 잘못된 로그인, 이름 수정, 비밀번호 재설정, 계정 전환·로그아웃, 긴 이름·특수문자, 영양정보 `null` 처리.
- 모바일 가로 넘침, 사이드바 열기·닫기, 키보드 접근.

## 기존 기획·중간 보고 자료

- [화면 설계안](docs/design.md) / [기능 명세](docs/requirements.md) / [회의 기록](docs/meetings.md)
- [2026-10-17 중간 보고서 — Figma Slides](https://www.figma.com/slides/Np9n3FqsM4UbkmR2TywNCi)
- [중간 보고서와 회의록](docs/midterm/README.md) / [당시 메뉴 예시와 출처](docs/menu-example.md)

중간 보고 자료는 당시 기록입니다. 이번 메뉴는 기존 실제 메뉴 예시와 별개의 가상 데이터입니다. 현재 구현 범위와 협업 방법은 이 README를 기준으로 봅니다.
