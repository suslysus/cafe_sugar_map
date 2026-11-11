/* GA4 방문 통계. 배포 사이트에서 동의한 방문만 수집하며 인증·메뉴 API와 독립적입니다. */
(function () {
  "use strict";
  const measurementId = window.CafeConfig && window.CafeConfig.googleAnalyticsMeasurementId;
  const origin = "https://suslysus.github.io";
  const basePath = "/cafe_sugar_map/";
  const pages = {
    "index.html": "지도·메뉴 · Cafe Sugar Map",
    "search.html": "메뉴 검색 · Cafe Sugar Map",
    "trends.html": "트렌드·신메뉴 · Cafe Sugar Map",
    "mypage.html": "마이페이지 · Cafe Sugar Map"
  };
  const page = location.pathname.slice(basePath.length) || "index.html";
  if (typeof measurementId !== "string" || !/^G-[A-Z0-9]+$/.test(measurementId) ||
      location.origin !== origin || !location.pathname.startsWith(basePath) ||
      !Object.prototype.hasOwnProperty.call(pages, page)) return;
  // 인증 콜백·returnTo가 있는 마이페이지에서는 Google 태그 자체를 로드하지 않습니다.
  if (page === "mypage.html" && (location.search || location.hash)) return;

  const consentKey = "csm.analytics.consent.v1";
  const consentLifetime = 180 * 24 * 60 * 60 * 1000;
  const disabledKey = "ga-disable-" + measurementId;
  let started = false;

  function readConsent() {
    try {
      const saved = JSON.parse(localStorage.getItem(consentKey));
      if (saved && typeof saved.allowed === "boolean" && Number.isFinite(saved.at) &&
          saved.at <= Date.now() && Date.now() - saved.at < consentLifetime) return saved.allowed;
    } catch (_) { /* 저장소 차단·잘못된 값은 미동의로 취급합니다. */ }
    return null;
  }
  function cleanReferrer() {
    try {
      const referrer = new URL(document.referrer);
      return ["https:", "http:"].includes(referrer.protocol) ? referrer.origin + "/" : "";
    } catch (_) { return ""; }
  }
  function start() {
    window[disabledKey] = false;
    if (started) return;
    started = true;
    window.dataLayer = window.dataLayer || [];
    const gtag = function () { window.dataLayer.push(arguments); };
    window.gtag = gtag;
    const tagConfig = {
      send_page_view: false,
      page_location: origin + basePath + page,
      page_referrer: cleanReferrer(),
      page_title: pages[page],
      allow_google_signals: false,
      allow_ad_personalization_signals: false,
      cookie_domain: "none",
      cookie_path: basePath,
      cookie_prefix: "csm",
      cookie_expires: 30 * 24 * 60 * 60,
      cookie_update: false,
      cookie_flags: "SameSite=Lax;Secure"
    };
    // 태그의 자동 초기화에도 URL 정리·쿠키·자동 조회 차단 설정을 적용합니다.
    gtag("set", tagConfig);
    gtag("js", new Date());
    gtag("config", measurementId, tagConfig);
    gtag("event", "page_view", {
      send_to: measurementId,
      page_location: tagConfig.page_location,
      page_referrer: tagConfig.page_referrer,
      page_title: tagConfig.page_title
    });
    const script = document.createElement("script");
    script.async = true;
    script.referrerPolicy = "no-referrer";
    script.src = "https://www.googletagmanager.com/gtag/js?id=" + measurementId;
    script.onerror = function () { status.textContent = "통계를 불러오지 못했어요. 사이트는 계속 이용할 수 있어요."; };
    document.head.append(script);
  }
  function stop() {
    window[disabledKey] = true;
    // 이 통계 태그의 쿠키만 삭제하고 Supabase 세션·다른 프로젝트 쿠키는 보존합니다.
    document.cookie.split(";").forEach(function (cookie) {
      const name = cookie.split("=")[0].trim();
      if (/^csm_ga(?:_|$)/.test(name)) {
        document.cookie = name + "=; Max-Age=0; Path=" + basePath + "; SameSite=Lax; Secure";
      }
    });
  }

  const controls = document.createElement("div");
  controls.className = "analytics-controls";
  controls.innerHTML = '<button type="button" class="text-link" data-analytics-settings aria-expanded="false" aria-controls="analytics-notice">방문 통계 설정</button><span class="small muted" role="status" data-analytics-status></span>';
  const notice = document.createElement("section");
  notice.id = "analytics-notice";
  notice.className = "analytics-notice";
  notice.hidden = true;
  notice.setAttribute("aria-labelledby", "analytics-notice-title");
  notice.innerHTML = '<h2 id="analytics-notice-title">방문 통계 수집에 동의하시겠어요?</h2><p>동의하면 Google Analytics가 쿠키 식별자, 페이지 방문·이용 시간, 브라우저·기기 및 대략적인 지역 정보를 처리합니다. 이메일·이름·비밀번호·검색어·현재 위치 좌표는 통계 항목으로 보내지 않습니다. 거절해도 모든 기능을 이용할 수 있어요.</p><details><summary>수집·설정 안내</summary><p>사이트 이용 현황 확인을 위해 Google의 Analytics 서비스로 정보가 전송됩니다. 이 사이트의 통계 쿠키는 생성 후 최대 30일, 동의 선택은 이 브라우저에 180일간 저장합니다. 아래에서 언제든 동의를 철회할 수 있습니다. 철회는 이후 수집을 중단하며 이미 수집된 기록을 자동 삭제하지는 않습니다.</p><a class="text-link" href="https://policies.google.com/privacy?hl=ko" target="_blank" rel="noopener noreferrer">Google 개인정보처리방침 ↗</a></details><div class="analytics-actions"><button type="button" class="button secondary" data-analytics-deny>동의하지 않음</button><button type="button" class="button primary" data-analytics-allow>동의하고 시작</button></div>';
  const main = document.querySelector("main") || document.body;
  main.append(controls, notice);
  const settings = controls.querySelector("[data-analytics-settings]");
  const status = controls.querySelector("[data-analytics-status]");
  function show(open) {
    notice.hidden = !open;
    settings.setAttribute("aria-expanded", String(open));
  }
  function apply(allowed) {
    status.textContent = allowed ? "방문 통계 허용" : "방문 통계 수집 안 함";
    if (allowed) start(); else stop();
  }
  function choose(allowed) {
    let stored = true;
    try { localStorage.setItem(consentKey, JSON.stringify({ allowed: allowed, at: Date.now() })); }
    catch (_) { stored = false; }
    apply(allowed);
    if (!stored) status.textContent += " · 선택을 저장할 수 없어 다음 페이지에서 다시 확인해요.";
    show(false);
    settings.focus();
  }
  settings.addEventListener("click", function () { show(notice.hidden); });
  notice.querySelector("[data-analytics-allow]").addEventListener("click", function () { choose(true); });
  notice.querySelector("[data-analytics-deny]").addEventListener("click", function () { choose(false); });
  window.addEventListener("storage", function (event) {
    if (event.key !== consentKey && event.key !== null) return;
    const allowed = readConsent();
    apply(allowed === true);
    show(allowed === null);
  });
  const allowed = readConsent();
  apply(allowed === true);
  show(allowed === null);
}());
