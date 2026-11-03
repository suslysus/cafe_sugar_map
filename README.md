# Cafe Sugar Map

주변 카페의 메뉴를 찾고 가격·당류·칼로리를 확인하는 웹프로그래밍 13조 프로젝트입니다.

**2026-11-02 협업용 기초본 · HTML / CSS / JavaScript · 백엔드 연결 없음**

> [!WARNING]
> **이번 기초본 업로드까지만 main에 직접 반영합니다. 이후 팀원 전원은 개인 작업 브랜치에서 수정 → push → Pull Request(PR) → 카카오톡 작업 보고·검토 요청 → 다른 팀원 확인 후 main에 merge하는 순서를 지켜 주세요.**
>
> main에서 직접 개발하거나 `git push --force`하지 마세요. `git pull`은 다른 사람의 변경을 내 컴퓨터에 받는 명령이고, PR은 내 변경을 main에 합쳐 달라는 요청입니다. 두 작업은 다릅니다.

## 1. 먼저 알아둘 내용

- 실제 지도·현재 위치·크롤링·검색 트렌드·서버 인증·DB는 연결하지 않은 프런트엔드 기초본입니다.
- **매장 위치와 메뉴·가격·영양값·NEW 표시는 모두 가상 예시입니다. 실제 판매 정보나 실제 유행으로 사용하지 마세요.** 브랜드 이름만 프로젝트 대상 4곳을 사용합니다.
- 3페이지는 **트렌드·신메뉴**입니다. 랜덤 추천은 제외했습니다.
- 로그인은 표시 이름만 받는 데모입니다. 비밀번호 입력은 비활성화했으며 실제 계정을 만들거나 인증하지 않습니다.
- 즐겨찾기와 비교 선택은 `localStorage`, 데모 로그인은 현재 탭의 `sessionStorage`를 사용합니다. **실제 사용자 정보·비밀번호·API 키를 여기에 저장하지 마세요.**
- 데모 이름은 모두 같은 `demo-user` 프로필입니다. 이름을 바꿔도 다른 계정으로 분리되지 않습니다. 로그아웃 후에도 이 브라우저의 즐겨찾기는 유지됩니다.
- 비교는 **선택·해제와 목록 표시까지만** 구현했습니다. 별도 비교 화면·장바구니·길 안내는 기본 범위에 포함하지 않았습니다.

## 2. 실행 방법

공유·발표용 주소는 **[Cafe Sugar Map](https://suslysus.github.io/cafe_sugar_map/)**입니다. GitHub Pages는 `main`의 루트 폴더를 배포하며, 팀원 검토 후 PR을 merge하면 잠시 뒤 사이트도 갱신됩니다. 개인 브랜치에 push하는 것만으로 배포 화면이 바뀌지는 않습니다. 설정과 장애 확인은 [배포 안내](docs/deployment.md)를 참고하세요.

2026-11-03 첫 배포는 기존 데모가 있는 `main` 기준입니다. Supabase 연결은 [PR #2](https://github.com/suslysus/cafe_sugar_map/pull/2)가 검토 후 merge되어야 배포 사이트에서도 사용할 수 있습니다. 정기 크롤링용 Actions는 아직 구성하지 않았습니다.

설치나 빌드 없이 저장소 폴더에서 정적 서버를 실행합니다.

```bash
python -m http.server 8000
```

브라우저에서 **http://localhost:8000**을 엽니다. Windows에서 `python`이 없다면 `py -m http.server 8000`을 사용하거나 VS Code Live Server로 `index.html`을 여세요. 종료는 터미널에서 `Ctrl+C`입니다.

HTML을 직접 열어도 기본 화면은 표시되지만 `file://`에서는 저장소·권한·URL 동작이 브라우저마다 다를 수 있습니다. **팀 검증은 같은 localhost 주소에서 진행하세요.** 포트가 바뀌면 브라우저 저장 데이터도 별개입니다.

## 3. 페이지와 담당 파일

| 페이지 | 담당 | HTML | 개인 CSS / JS | 현재 동작 |
| --- | --- | --- | --- | --- |
| 지도·메뉴 | 강민재 | `index.html` | `assets/css/map.css`, `assets/js/map.js` | 예시 지도 핀 선택, 브랜드별 메뉴, 공통 상세창 |
| 메뉴 검색 | 강다은 | `search.html` | `assets/css/search.css`, `assets/js/search.js` | 이름 검색, 브랜드·카테고리 필터, 즐겨찾기, 비교 선택 목록 |
| 트렌드·신메뉴 | 현준혁 | `trends.html` | `assets/css/trends.css`, `assets/js/trends.js` | 예시 키워드→검색 연결, 신메뉴 브랜드 필터, 공통 상세창 |
| 로그인·마이페이지 | 한정원 | `mypage.html` | `assets/css/mypage.css`, `assets/js/mypage.js` | 데모 로그인·로그아웃, 즐겨찾기 목록, 위치 권한 상태 확인 |

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
    api.js               공통 데이터 접근 함수, 현재는 mock 모드
    common.js            사이드바·헤더·카드·상세창·알림
    map.js / search.js / trends.js / mypage.js
  (각 페이지는 자신의 CSS·JS를 사용)
docs/
  api.md                 향후 API 명세표·요청/응답·화면 함수 연결
  database.md            DB와 로컬 파일 비교·테이블 설계안
  schema/accounts.sql    계정·세션·즐겨찾기 SQLite 설계 예시
  schema/catalog.sql     메뉴 DB를 도입할 때의 추가 설계 예시
```

**각자 개인 파일부터 수정해 주세요.** 공통 파일은 한정원을 기본 조율 창구로 하되, 변경 전 팀과 협의합니다. 수집 담당의 추가 분담과 백엔드 기술은 아직 확정하지 않았습니다.

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
- HTML의 `body data-page`, `app-sidebar`, `app-topbar`와 스크립트 순서를 유지하세요: `mock-data.js → api.js → common.js → 개인 JS`.
- 개인 JS는 `CafeAPI`로 데이터를 받습니다. 페이지마다 메뉴 배열이나 서버 URL을 중복 관리하지 않습니다. `CafeMock` 직접 참조는 공통 구현 내부에만 둡니다.
- **메뉴·브랜드·카테고리 ID는 공통 계약입니다.** 변경 시 검색 URL·즐겨찾기·비교 선택·API·DB도 맞춥니다. 메뉴 이름으로 식별하지 마세요.
- 기초본의 `categoryTags`는 복수 태그입니다. 최종 분류는 팀에서 정합니다. 디카페인과 무카페인은 구분하세요.
- 영양정보는 **제공 사이즈·HOT/ICE·기본 레시피**와 함께 관리합니다. 미확인은 `null`로 두고 ‘확인 중’으로 표시합니다. 0과 미확인은 다릅니다.
- 외부·사용자 문자열을 `innerHTML`에 그대로 넣지 마세요. 현재 템플릿에서는 `CafeUI.escape()`를 사용합니다. 외부 URL도 허용 프로토콜을 검증합니다.
- `.env`, 비밀번호, 세션 토큰, API 키, DB 파일, 개인 정보는 커밋하지 않습니다. 데모와 실데이터는 구분합니다.
- `localStorage`는 인증 수단이 아닙니다. 데모 로그인 검사를 실제 서버의 권한 검사로 사용하지 마세요.
- 크롤러는 별도 작업으로 두고 방문자 페이지 로딩 때마다 사이트를 긁지 않습니다. 사이트별 접근·이용 조건을 확인하고 과도한 요청을 피합니다.
- 수집 실패를 메뉴 판매 종료로 처리하지 않습니다. 원본 상품 ID·출처·확인 시각을 보존하고 최초 발견일을 출시일로 쓰지 않습니다.

## 6. API 명세표

**아래 URL은 향후 연결할 설계안이며 현재 동작하는 서버 주소가 아닙니다.** 자세한 요청·응답과 `CafeAPI` 대응은 [API 문서](docs/api.md)에 있습니다.

| 기능 | 메서드 | 제안 경로 | 로그인 | 화면 |
| --- | --- | --- | --- | --- |
| 브랜드·카테고리 | GET | `/api/v1/catalog/meta` | 불필요 | 공통 |
| 주변 매장 | GET | `/api/v1/stores?lat=...&lng=...&radiusM=500` | 불필요 | 1 |
| 메뉴 검색 | GET | `/api/v1/menus?brandId=...&category=...&q=...` | 불필요 | 1·2 |
| 메뉴 상세 | GET | `/api/v1/menus/{menuId}` | 불필요 | 공통 |
| 트렌드 | GET | `/api/v1/trends` | 불필요 | 3 |
| 신메뉴 | GET | `/api/v1/menus?isNew=true&brandId=...` | 불필요 | 3 |
| 로그인 | POST | `/api/v1/auth/login` | 불필요 | 4 |
| 현재 사용자 | GET | `/api/v1/me` | 필요 | 공통 |
| 로그아웃 | POST | `/api/v1/auth/logout` | 필요 | 4 |
| 즐겨찾기 목록 | GET | `/api/v1/me/favorites` | 필요 | 4 |
| 즐겨찾기 저장 | PUT | `/api/v1/me/favorites/{menuId}` | 필요 | 1·2·3 |
| 즐겨찾기 삭제 | DELETE | `/api/v1/me/favorites/{menuId}` | 필요 | 공통 |

위치 권한 조회는 브라우저 API입니다. 비교 선택은 현재 로컬 기능이며 비교 서버 API는 정하지 않았습니다. 회원가입·소셜 로그인 여부도 미정입니다.

## 7. DB 두 개와 메뉴 로컬 저장 비교

**DB를 계정용/메뉴용으로 두 개 나누기보다, 하나의 DB 안에서 테이블을 분리하는 방식을 제안합니다.** 메뉴 저장 위치는 아직 확정하지 않았습니다.

| 선택 | 계정·즐겨찾기 | 메뉴 | 판단 |
| --- | --- | --- | --- |
| 현재 기초본 | 데모 브라우저 저장 | `mock-data.js` | 서버·DB 없이 네 페이지 개발 가능 |
| A. 서버 인증 + 메뉴 파일 | 서버 DB | 서버가 읽는 공통 JSON | 메뉴가 적고 갱신이 드물 때 단순함. 방문자가 개발자 PC 파일을 직접 읽는 구조는 아님 |
| B. 서버 인증 + 메뉴 DB | 서버 DB | 같은 DB의 메뉴 테이블 | 자동 수집·수정·필터 확장이 필요할 때 유리 |

**A로 시작해도 화면은 같은 API를 사용하고 서버 내부 저장소만 B로 바꿀 수 있게 설계합니다.** 서버 인증을 도입하면 즐겨찾기도 서버에서 사용자별로 관리합니다. 메뉴 ID가 바뀌면 기존 즐겨찾기도 검토합니다.

[DB 설계안](docs/database.md), [계정 SQL](docs/schema/accounts.sql), [메뉴 SQL](docs/schema/catalog.sql)을 참고하세요. **SQL은 미실행 설계 예시이며 DBMS·인증 기술을 확정한 것이 아닙니다.**

## 8. PR 전 확인할 동작

- 사이드바에서 네 페이지 이동과 현재 페이지 표시.
- 지도 핀 선택→오른쪽 카페·메뉴 변경, 상세창 열기·닫기.
- 검색·필터·결과 없음·초기화, 비교 선택·해제와 페이지 이동 후 목록 유지.
- 신메뉴 필터와 트렌드→검색 이동. 랜덤 추천 제외 여부.
- 비로그인 즐겨찾기→로그인→원래 페이지 복귀, 저장→마이페이지 조회·삭제.
- 새로고침·로그아웃, 긴 이름·특수문자, 영양정보 `null` 처리.
- 모바일 가로 넘침, 사이드바 열기·닫기, 키보드 접근.

## 기존 기획·중간 보고 자료

- [화면 설계안](docs/design.md) / [기능 명세](docs/requirements.md) / [회의 기록](docs/meetings.md)
- [2026-10-17 중간 보고서 — Figma Slides](https://www.figma.com/slides/Np9n3FqsM4UbkmR2TywNCi)
- [중간 보고서와 회의록](docs/midterm/README.md) / [당시 메뉴 예시와 출처](docs/menu-example.md)

중간 보고 자료는 당시 기록입니다. 이번 메뉴는 기존 실제 메뉴 예시와 별개의 가상 데이터입니다. 현재 구현 범위와 협업 방법은 이 README를 기준으로 봅니다.
