# 공식 소식 수집기 기본 구조

이 변경은 수집기 개발의 첫 PR입니다. **공통 데이터 형식과 검증 CLI만 구현했습니다.** 실제 사이트 수집·자동 분류·이미지 다운로드·DB 접속·웹페이지 연결은 아직 하지 않습니다. 기존 네 페이지와 인증·지도·DB는 변경하지 않습니다.

## 실행

Python 3.12 이상이 필요합니다. 저장소 루트에서 설치된 uv를 사용할 경우:

```text
uv run tools/launch-collector/collect.py --help
uv run tools/launch-collector/collect.py validate tools/launch-collector/examples/brand-payload.json
```

이미 Python과 Pydantic 2.12 이상이 준비돼 있으면 동일한 명령을 `python tools/launch-collector/collect.py ...`로 실행할 수 있습니다. uv 첫 실행은 라이브러리 내려받기가 발생할 수 있습니다.

정상 검증은 종료 코드 0과 브랜드·건수·상태 JSON을 출력합니다. 잘못된 형식·키 불일치·읽을 수 없는 파일은 종료 코드 2로 끝납니다. 실제 수집·DB 저장은 일어나지 않습니다.

`collect --brand paik`는 후속 수집 명령의 자리만 예약했습니다. 현재 실행하면 `COLLECTION_NOT_IMPLEMENTED`와 종료 코드 2를 반환하며, 빈 성공 결과나 데이터 파일을 만들지 않습니다.

## 구조

| 파일 | 역할 |
| --- | --- |
| collect.py | CLI 실행 진입점과 PEP 723 의존성 |
| launch_collector/models.py | 원문 내용·판정 결과·UTC 시각 타입 |
| launch_collector/batch.py | 브랜드별 저장 입력과 키 분할 검사 |
| launch_collector/adapters.py | 향후 브랜드별 목록·상세 수집 인터페이스 |
| launch_collector/cli.py | 검증 명령과 종료 코드 |
| examples/brand-payload.json | 실제 수집 결과가 아닌 가짜 형식 예시 |
| tests/ | 형식·오류 처리·CLI 동작 검사 |

브랜드 ID는 최신 main과 같은 `starbucks/mega/compose/paik`입니다. 게시글은 메뉴와 별도 단위입니다. `source_key`는 원본 글의 고정 키이고, 저장 ID는 `브랜드ID:원본키`로 만들 예정입니다. 현재 입력에는 DB 관리 ID·수동 판정·생성 열을 받지 않습니다.

날짜 미확인은 null, 시즌·한정 미확인도 null입니다. 본문이 이미지뿐인 글은 빈 본문과 이미지 배열로 표현합니다. 본문과 이미지가 모두 없는 글은 거부합니다. 확인 시각은 UTC 오프셋을 가진 ISO 시각으로 받습니다.

`seen`의 고유 키는 `posts`(본문 추출 성공)와 `failed_details`(실패) 중 정확히 한 곳에 있어야 합니다. 중복·누락·양쪽 중복을 거부합니다. 목록 자체가 실패한 입력은 세 배열이 비어 있고 오류 코드가 있어야 합니다. 판정 needs_review/excluded는 수집 실패와 구분합니다.

이 단계에서는 자동 판정값의 형식과 content_hash의 64자리 형식만 검사합니다. 실제 글이 음료 출시인지 판별하거나 해시를 재계산하는 기능은 아직 없습니다. 예시의 해시는 자리표시자입니다. 형식 검증 성공을 출시 확인·게시 승인·DB 저장 성공으로 해석하지 않습니다.

## 테스트

수집기 폴더를 프로젝트로 사용합니다. 아래 명령은 해당 폴더의 .venv에 개발 의존성을 준비할 수 있습니다.

```text
uv run --project tools/launch-collector --group dev python -m pytest -p no:cacheprovider tools/launch-collector/tests
```

테스트는 네트워크·실계정·DB를 사용하지 않습니다. 실제 사이트 파서와 실제 DB 동작은 후속 PR에서 각각 확인해야 합니다.

## 다음 변경 묶음

1. 빽다방 목록·상세 추출과 정규화, dry-run 출력.
2. 스타벅스·메가·컴포즈 추가와 부분 실패 처리.
3. 팀 규격 조율 후 Supabase 저장·조회 연결.
4. 공식 소식 화면의 목록·필터·상세 연결.

DB 테이블·RPC는 아직 생성하지 않습니다. 쓰기 키나 계정 정보는 이 도구와 웹페이지에 넣지 않습니다. 카톡 작업 보고와 팀원 검토 후 merge하는 기존 협업 규칙을 따릅니다.
