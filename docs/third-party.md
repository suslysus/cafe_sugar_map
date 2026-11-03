# 외부 라이브러리

## Supabase JavaScript SDK

- 패키지: `@supabase/supabase-js` 2.118.0 (고정 버전)
- 파일: `assets/vendor/supabase-2.118.0.js`
- 출처: [공식 npm 패키지](https://www.npmjs.com/package/@supabase/supabase-js/v/2.118.0)
- 배포: npm tarball의 `dist/umd/supabase.js`. 가져올 때 npm `dist.integrity`의 SHA-512를 확인했다.
- 파일 SHA-256: `ee3be8de192b97cb1d73d1e95d6b82bb1f6b658c0f97c4ef757fc331996ed3d3`
- 라이선스: MIT. 원본 고지: `assets/vendor/SUPABASE-LICENSE.txt`

사이트는 SDK를 로컬 정적 파일로 제공한다. 인증·DB 사용에는 설정된 Supabase 프로젝트와 네트워크 연결이 필요하다. 버전 갱신은 공통 연결 코드를 검증한 후 팀에 공유한다.
