# 공식 소식 수집기 — 네 브랜드 로컬 수집

공통 입력 검증에 빽다방·메가·컴포즈·스타벅스 공식 소식 목록·상세 수집을 추가했습니다. 여러 페이지·게시글의 제목·본문·사진 주소·공식 게시일을 추출해 로컬 JSON으로 저장합니다. `--image-dir`를 지정하면 사진 파일도 받습니다. DB 저장·웹페이지 연결·예약 실행은 하지 않습니다.

## 실행

Python 3.12 이상과 anyio/httpx2/selectolax/Pydantic이 필요합니다. 의존성은 `pyproject.toml`과 `collect.py`의 PEP 723 메타데이터에 선언돼 있습니다. 설치된 uv를 사용하면 필요한 의존성을 받을 수 있습니다.

```text
cd tools/launch-collector
uv run collect.py collect --brand paik --max-posts 12 --max-pages 2 --output output/paik.json --image-dir output/images
uv run collect.py validate output/paik.json
uv run collect.py collect --brand mega --max-posts 15 --max-pages 2 --output output/mega.json --image-dir output/images/mega
uv run collect.py collect --brand compose --max-posts 23 --max-pages 2 --output output/compose.json --image-dir output/images/compose
uv run collect.py collect --brand starbucks --max-posts 12 --max-pages 2 --output output/starbucks.json --image-dir output/images/starbucks
```

이미 의존성이 설치된 환경에서는 `uv run` 대신 `python`을 사용합니다. 출력 경로는 반드시 직접 지정해야 하며 `collect --brand paik`만 실행하면 파일을 만들거나 요청하지 않습니다. 브랜드를 하나씩 지정합니다. `all`은 단일 브랜드 payload와 혼동하지 않도록 아직 `BRAND_NOT_IMPLEMENTED`로 종료합니다.

- `--max-posts`: 서로 다른 게시글 수, 기본 10건·1~200.
- `--max-pages`: 목록 페이지 수, 기본 3·1~20.
- `--output`: 검증 가능한 `p_payload` JSON의 로컬 저장 경로.
- `--image-dir`: 선택 사항. 사진 파일과 `image-manifest.json`을 저장합니다. 지정하지 않으면 사진 주소만 수집합니다.
- 출력 JSON이 사진 폴더 자체 또는 그 안의 `image-manifest.json`과 같은 경로면 요청·쓰기 전에 `INVALID_OUTPUT_PATHS`로 거부합니다.
- stdout: 선택/성공/실패 게시글 수, 실제 읽은 목록 페이지 수, 남은 글 여부, 사진 취득/실패 건수. 제한한 범위의 결과이며 전체 게시판 수집 완료를 뜻하지 않습니다.
- 종료 코드: 선택 범위 정상 완료 0, 일부 목록/상세/사진 실패 1, 목록 전체 실패·잘못된 옵션·출력 실패 2.

## 원문·식별자·사진

- 공식 소스는 `https://paikdabang.com/news/`, `/news/page/N/`과 `/post_news/` 상세입니다. 목록의 표시 순번과 이미지 `wp-image-*` 값은 게시글 ID로 쓰지 않습니다.
- ID 입력 키는 `url:` + 정규화한 공식 원문 URL의 SHA-256입니다. HTTP/www/퍼센트 인코딩 차이와 원문의 추적 query·fragment는 같은 글로 정리합니다. 페이지 경계의 같은 키는 한 번만 상세 조회합니다.
- 메가 소스는 `/bbs/?bbs_category=3` 이벤트 게시판입니다. 인코딩된 상세 쿼리의 `bbs_idx`로 `event:{번호}` 키를 만들고 목록 페이지 번호는 키에 넣지 않습니다.
- 컴포즈 소스는 `https://composecoffee.com/?mid=news`와 실제 뉴스 페이지 링크입니다. 문서 번호를 `news:{번호}` 키로 사용합니다.
- 스타벅스는 `newsListAjax.do`·`newsViewAjax.do`의 공식 소식 JSON 조회를 사용합니다. 목록은 `cate=N01`·`pageIndex`, 상세는 `seq`·빈 `view_yn`으로 조회하고 `news:{seq}` 키를 사용합니다. 이 POST는 공개 소식 조회용이며 계정·DB 쓰기 요청이 아닙니다.
- 포스터만 있는 글은 빈 본문과 사진 배열을 가진 유효한 글입니다. 본문·사진이 둘 다 없거나 게시판 구조를 알아볼 수 없으면 실패로 기록합니다. 정상 빈 목록과 구조 변경을 구분합니다.
- script/style/iframe/noscript와 이전글·목록·footer는 본문으로 넣지 않습니다. 본문의 사진을 원문 순서대로 중복 제거합니다.
- 사진은 브랜드별로 허용한 공식 호스트의 GET만 사용하며 각 redirect도 요청 전에 검사합니다. 스타벅스는 `image.istarbucks.co.kr`, 메가는 `img.mega-mgccoffee.com` 공식 이미지 호스트도 포함합니다. 한 응답은 최대 12MiB이며 timeout과 연결 재시도가 있습니다.
- JPEG/PNG/GIF/WebP 서명을 확인하고 파일 내용 SHA-256 이름으로 저장합니다. 사진 수집 실패는 별도 manifest에 기록하고 성공한 게시글 JSON은 유지합니다. 파일 경로·사진 취득 상태는 DB용 payload에 섞지 않습니다.

## 날짜·판정과 현재 한계

공식 게시일은 목록·상세에서 읽고 없으면 null입니다. 포스터 파일명의 날짜나 수집일을 출시일로 사용하지 않습니다. 이번에는 OCR·출시일 문장 추출·시즌/한정 판정·자동 공개 승인을 하지 않으므로 `release_on`, `is_seasonal`, `is_limited`, `notice_period_text`는 null, `auto_decision`은 모두 `needs_review`입니다. 수집 성공이 신메뉴 출시·현재 판매·재고 확인을 뜻하지 않습니다.

`content_hash`는 실제 추출한 내용 9개 필드의 정규 JSON으로 계산하며 관찰 시각·조회수는 제외합니다. 게시글은 음료 메뉴와 별도 단위이고 가격·영양값을 생성하지 않습니다. 원문 사진은 서버가 주는 파일 그대로이며 자동 OCR이나 재가공하지 않습니다.

## 테스트

```text
uv run --group dev python -m pytest -p no:cacheprovider tests
```

### Windows에서 테스트할 때

Windows는 Python 기본 출력 인코딩이 UTF-8이 아니어서, CLI 출력을 UTF-8로 읽는 테스트에서 `UnicodeDecodeError` 경고가 날 수 있습니다. 테스트 전에 같은 터미널에서 `PYTHONUTF8=1`을 설정하고 위 명령을 실행하세요.

```text
# PowerShell
$env:PYTHONUTF8 = "1"

# 명령 프롬프트(cmd)
set PYTHONUTF8=1

# Git Bash
export PYTHONUTF8=1
```

설정은 해당 터미널 창에서만 유지됩니다. macOS·Linux는 기본이 UTF-8이라 따로 설정하지 않아도 됩니다.

테스트는 공식 목록 2페이지·상세 3건의 축약 fixture와 메모리 HTTP 응답을 사용합니다. 다건·페이지 경계·부분 실패·잘못된 사진 응답·외부 redirect·본문 정규화·CLI 파일 출력을 검사합니다. 실제 공식 사이트 실수집과 사진 디코딩 검증은 별도 로컬 증거에 기록하며 이 테스트 통과로 대신하지 않습니다.

기존 `validate` 명령과 공통 브랜드 ID `starbucks/mega/compose/paik`는 유지했습니다. 기존 페이지·공통 API·인증·메뉴 데이터·DB·배포 설정은 변경하지 않습니다.

### 실제 확인 범위 (2026-11-10)

공식 사이트에서 직접 수집한 결과입니다. 빽다방은 목록 2페이지에서 글 12건·사진 12개, 컴포즈는 2페이지에서 글 23건·본문 이미지 22개, 스타벅스는 2페이지에서 글 12건·본문 이미지 75개, 메가는 2페이지에서 글 15건·사진 20개를 받았습니다. 사진 파일은 별도 검증에서 디코딩·해시·크기를 확인했습니다. 글에는 음료 외 상품·행사도 포함됩니다.

메가 게시판은 Cloudflare WARP 같은 VPN 경로에서는 연결 시간 초과가 날 수 있습니다. 이때는 VPN을 끄거나 일반 네트워크에서 실행하세요.
