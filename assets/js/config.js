/* 공개 브라우저 설정: Supabase URL·publishable 키, 카카오 JavaScript 키, GA4 측정 ID.
 * secret/service_role 키 및 DB 비밀번호는 절대 넣지 않습니다.
 * Supabase 설정 전에는 실제 로그인·저장을 비활성화하며 데모 계정으로 대체하지 않습니다.
 */
window.CafeConfig = Object.freeze({
  supabaseUrl: "https://dmwpzbmcabwfyczjgqkt.supabase.co",
  supabasePublishableKey: "sb_publishable_tnRR7uttXCuFh0Lzzj5Csg_r_yZc3qw",
  kakaoJavaScriptKey: "77d5514931660f5562c38efcfcfab35b",
  // 빈 값이면 방문 통계 UI와 Google 태그 요청 모두 비활성화합니다.
  googleAnalyticsMeasurementId: "G-RD5RGR7SHN"
});
