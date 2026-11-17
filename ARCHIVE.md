# Cafe Sugar Map 개발 중단 · 보관

2026-11-17 프로젝트 소유자의 결정으로 Cafe Sugar Map 개발을 중단하고 GitHub에 소스와 이력을 보관합니다. 후속 작업은 별도 프로젝트 ‘더미’에서 진행합니다.

## 보관 범위

- `archive/discontinued-2026-11-17`: 정리 시점의 원격 main(`e8d986bce6f1d0c68eb0afb2a420ba6853957cf2`)과 이 안내를 담은 보관본입니다.
- `feature/jeongwon`: PC에 있던 작업 브랜치의 마지막 상태(`67bedcf0491a5aab9609c0422217553a6e57dd51`)입니다. 로컬 수정 사항은 없었습니다.
- `archive/jeongwon-stash-2026-11-17`: 로컬에만 있던 이전 인증 브랜치의 배포 안내 초안입니다. Git stash 커밋(`815127951530b19dc43ace7f592a3cc5944eb58d`)과 부모 이력을 보존합니다. 당시 미추적 파일이었던 `docs/deployment.md`는 해당 커밋의 세 번째 부모에도 보존돼 있습니다. 최신 구현 지침으로 사용하지 마세요.
- 다른 팀원의 원격 작업 브랜치는 그대로 보존합니다. 이 정리 과정에서 main 변경·PR 생성·병합은 하지 않습니다.

GitHub 보관 상태를 확인한 뒤 PC의 `cafe_sugar_map` 코드 폴더를 제거합니다. 폴더 밖의 중간보고서 PDF·PPTX·제출 ZIP, 회의록, 새 아이디어 및 ‘더미’ 프로젝트는 PC에 유지합니다.

이번 정리는 GitHub 저장소의 읽기 전용 Archive 전환, GitHub Pages 배포 중단, Supabase DB·계정 삭제, 카카오·Google Analytics 설정 삭제를 포함하지 않습니다. 온라인 서비스와 저장 데이터의 종료는 별도로 결정해야 합니다.

## 다시 확인할 때

```sh
git clone https://github.com/suslysus/cafe_sugar_map.git
cd cafe_sugar_map
git switch archive/discontinued-2026-11-17
```

예전 초안을 확인하려면 다음 명령을 사용합니다. 최신 main에 그대로 병합하지 마세요.

```sh
git show origin/archive/jeongwon-stash-2026-11-17:README.md
git show origin/archive/jeongwon-stash-2026-11-17^3:docs/deployment.md
```
