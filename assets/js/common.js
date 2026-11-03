/* 공통 UI: 사이드바·상세창·카드·알림. 각 페이지는 CafeUI 공개 함수만 사용하세요. */
(function () {
  "use strict";
  const api = window.CafeAPI;
  const paths = { map: "index.html", search: "search.html", trends: "trends.html", mypage: "mypage.html" };
  const labels = { map: "지도·메뉴", search: "메뉴 검색", trends: "트렌드·신메뉴", mypage: "마이페이지" };
  const icons = {
    map: '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z"/><path d="M9 3v15M15 6v15"/>',
    search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    trends: '<path d="m3 17 6-6 4 3 8-10M15 4h6v6"/>',
    mypage: '<circle cx="12" cy="8" r="4"/><path d="M4 22v-3a8 8 0 0 1 16 0v3"/>',
    heart: '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>'
  };
  const escape = value => String(value == null ? "" : value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
  const icon = name => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (icons[name] || icons.search) + '</svg>';
  const number = value => typeof value === "number" && Number.isFinite(value) ? value.toLocaleString("ko-KR") : "확인 중";
  const price = value => typeof value === "number" ? number(value) + "원" : "가격 확인 중";
  const brand = id => window.CafeMock.brands.find(item => item.id === id) || { name: "브랜드 확인 중", color: "#76543d", initial: "?" };
  const tone = menu => ["latte", "matcha", "coffee", "berry", "tea", "lemon"].includes(menu.tone) ? menu.tone : "latte";
  let toastTimer;
  function cup(menu) {
    return '<svg viewBox="0 0 150 175" aria-hidden="true"><ellipse cx="77" cy="159" rx="41" ry="6" fill="#3a2d2115"/><path d="M42 40h70l-8 111q-28 15-54 0Z" fill="#faf4e5"/><path d="M44 67h66l-6 84q-27 13-54 0Z" fill="var(--drink)"/><path d="M44 65h66l-1 17H45Z" fill="#f4ebd3" opacity=".82"/><path d="m54 60 4 82" stroke="#fff" opacity=".16" stroke-width="5"/><ellipse cx="77" cy="40" rx="39" ry="8" fill="#ded5c2"/><ellipse cx="77" cy="38" rx="37" ry="7" fill="#faf6eb"/><path d="m90 37 5-27" stroke="#b7a07a" stroke-width="5"/><text x="77" y="120" text-anchor="middle" fill="#fffaf1" font-size="15" font-family="Georgia,serif">csm.</text></svg>';
  }
  function favoriteButton(menu) {
    const saved = api.isFavorite(menu.id);
    return '<button type="button" class="icon-button favorite-button' + (saved ? " saved" : "") + '" data-favorite="' + escape(menu.id) + '" aria-label="' + escape(menu.name) + ' 즐겨찾기" aria-pressed="' + saved + '">' + icon("heart") + '</button>';
  }
  function card(menu, options = {}) {
    const selected = api.getCompare().includes(menu.id);
    const unit = (value, suffix) => typeof value === "number" ? '<strong>' + number(value) + '</strong>' + suffix : '<strong>—</strong> 확인 중';
    return '<article class="menu-card"><div class="menu-art tone-' + tone(menu) + '"><span class="menu-badge">' + (menu.isNew ? "NEW · 예시" : "DEMO MENU") + '</span>' + cup(menu) + favoriteButton(menu) + '</div><div class="menu-card-body"><p class="menu-brand">' + escape(brand(menu.brandId).name) + '</p><button type="button" class="menu-title-button" data-detail="' + escape(menu.id) + '">' + escape(menu.name) + '</button><p class="menu-subtitle">' + escape(menu.sizeLabel) + ' · ' + escape(menu.temperature) + '</p><div class="menu-metrics"><div class="metric-highlight">당류 ' + unit(menu.sugarG, "g") + '</div><div>열량 ' + unit(menu.caloriesKcal, "kcal") + '</div></div><div class="menu-card-footer"><span class="menu-price">' + price(menu.priceKrw) + '</span>' + (options.compare ? '<button class="compare-button" type="button" data-compare="' + escape(menu.id) + '" aria-pressed="' + selected + '">' + (selected ? "✓ 비교 선택됨" : "+ 비교에 추가") + '</button>' : '<button class="text-link" type="button" data-detail="' + escape(menu.id) + '">상세 보기 ↗</button>') + '</div></div></article>';
  }
  function empty(title, description, link) {
    return '<div class="empty-state"><h3>' + escape(title) + '</h3><p>' + escape(description) + '</p>' + (link ? '<a class="button secondary" href="search.html">메뉴 찾아보기 ↗</a>' : "") + '</div>';
  }
  function toast(message) { const node = document.getElementById("app-toast"); node.textContent = message; node.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { node.hidden = true; }, 4000); }
  function currentReturnUrl() { const file = location.pathname.split("/").pop() || "index.html"; return file + location.search; }
  function safeReturnUrl(raw) {
    if (!raw) return null;
    try { const value = new URL(raw, location.href); const file = value.pathname.split("/").pop(); const expected = new URL(paths[file === "index.html" ? "map" : file === "search.html" ? "search" : file === "trends.html" ? "trends" : "mypage"], location.href); return ["index.html", "search.html", "trends.html"].includes(file) && value.origin === expected.origin && value.pathname === expected.pathname ? file + value.search : null; }
    catch (_) { return null; }
  }
  function closeSidebar() { document.querySelector(".sidebar").classList.remove("open"); document.querySelector(".mobile-overlay").classList.remove("visible"); document.getElementById("mobile-menu-toggle").setAttribute("aria-expanded", "false"); }
  async function refreshAccount() {
    try {
      const user = await api.getSession();
      document.getElementById("account-name").textContent = user ? user.displayName + "님" : "로그인";
    } catch (_) { document.getElementById("account-name").textContent = "로그인"; }
  }
  function syncFavorites() {
    document.querySelectorAll("[data-favorite]").forEach(button => { const saved = api.isFavorite(button.dataset.favorite); button.classList.toggle("saved", saved); button.setAttribute("aria-pressed", String(saved)); });
  }
  async function showDetail(id) {
    const menu = await api.getMenu(id);
    if (!menu) return toast("메뉴를 찾을 수 없습니다.");
    const metric = (value, suffix) => typeof value === "number" ? number(value) + suffix : "확인 중";
    document.getElementById("detail-content").innerHTML = '<div class="menu-art tone-' + tone(menu) + '">' + cup(menu) + '</div><p class="menu-brand">' + escape(brand(menu.brandId).name) + ' · 데모 메뉴</p><h2 id="detail-title">' + escape(menu.name) + '</h2><p class="muted small">' + escape(menu.sizeLabel) + ' · ' + escape(menu.temperature) + ' · ' + (menu.volumeMl == null ? "용량 확인 중" : number(menu.volumeMl) + "ml") + '</p><dl class="detail-grid"><div><dt>가격</dt><dd>' + price(menu.priceKrw) + '</dd></div><div><dt>당류</dt><dd>' + metric(menu.sugarG, "g") + '</dd></div><div><dt>칼로리</dt><dd>' + metric(menu.caloriesKcal, "kcal") + '</dd></div></dl><p class="small muted">최소 사이즈 · 기본 레시피 · 옵션 추가 및 변경 없음</p><div class="demo-notice">모든 값은 개발용 예시입니다. 공식 출처·확인일은 실제 데이터 연결 시 표시합니다.</div><div class="dialog-actions">' + favoriteButton(menu) + '<a class="button secondary" href="search.html?q=' + encodeURIComponent(menu.name) + '">검색에서 보기 ↗</a></div>';
    const dialog = document.getElementById("menu-detail"); if (!dialog.open) dialog.showModal();
  }
  function init() {
    const active = document.body.dataset.page;
    document.getElementById("app-sidebar").innerHTML = '<aside class="sidebar" id="site-sidebar" aria-label="사이트 메뉴"><a class="brand" href="index.html"><svg class="brand-mark" viewBox="0 0 40 45" fill="none" aria-hidden="true"><path d="M7 16h24l-3 24H10L7 16Z" stroke="currentColor" stroke-width="2"/><path d="M4 13h30M12 7c0-5 7-5 7-5s1 9-7 9M23 11s0-8 8-7c0 0 1 7-8 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M13 25h13" stroke="currentColor" stroke-width="2"/></svg><span class="brand-name">Cafe<br>Sugar Map<span class="sr-only"> 홈</span></span></a><p class="brand-caption">A BETTER CUP, EVERY DAY.</p><p class="nav-caption">EXPLORE</p><nav class="sidebar-nav">' + Object.keys(paths).map((key, index) => '<a class="nav-link' + (active === key ? " active" : "") + '" href="' + paths[key] + '"' + (active === key ? ' aria-current="page"' : "") + '>' + icon(key) + '<span>' + labels[key] + '</span><span class="nav-number">0' + (index + 1) + '</span></a>').join("") + '</nav><div class="sidebar-bottom"><div class="sidebar-note"><strong>Know your cup.</strong><p>작은 정보가 만드는<br>나에게 맞는 커피 습관.</p></div><div class="sidebar-footer">WEB PROGRAMMING · TEAM 13</div></div></aside><div class="mobile-overlay" aria-hidden="true"></div>';
    document.getElementById("app-topbar").innerHTML = '<div class="topbar"><div class="topbar-left"><button class="icon-button mobile-menu" id="mobile-menu-toggle" type="button" aria-label="사이트 메뉴 열기" aria-expanded="false" aria-controls="site-sidebar">☰</button><span class="topbar-title">Cafe Sugar Map <span aria-hidden="true">/</span> ' + labels[active] + '</span></div><div class="topbar-actions"><span class="demo-label">MENU DEMO</span><a class="account-link" href="mypage.html">' + icon("mypage") + '<span id="account-name">로그인</span></a></div></div>';
    const extra = document.createElement("div"); extra.innerHTML = '<div id="app-toast" class="toast" role="status" aria-live="polite" hidden></div><dialog class="detail-dialog" id="menu-detail" aria-labelledby="detail-title"><div class="dialog-header"><p class="eyebrow">A CLOSER LOOK</p><button id="close-detail" class="icon-button" type="button" aria-label="메뉴 상세 닫기">×</button></div><div class="dialog-body" id="detail-content"></div></dialog>'; document.body.append(extra);
    document.getElementById("mobile-menu-toggle").addEventListener("click", () => { const open = !document.querySelector(".sidebar").classList.contains("open"); document.querySelector(".sidebar").classList.toggle("open", open); document.querySelector(".mobile-overlay").classList.toggle("visible", open); document.getElementById("mobile-menu-toggle").setAttribute("aria-expanded", String(open)); });
    document.querySelector(".mobile-overlay").addEventListener("click", closeSidebar);
    document.addEventListener("keydown", event => { if (event.key === "Escape") closeSidebar(); });
    document.getElementById("close-detail").addEventListener("click", () => document.getElementById("menu-detail").close());
    document.getElementById("menu-detail").addEventListener("click", event => { if (event.target.id === "menu-detail") { const box = event.target.getBoundingClientRect(); if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) event.target.close(); } });
    document.addEventListener("click", async event => {
      const detail = event.target.closest("[data-detail]"); if (detail) { await showDetail(detail.dataset.detail); return; }
      const favorite = event.target.closest("[data-favorite]");
      if (favorite) {
        try { const saved = await api.toggleFavorite(favorite.dataset.favorite); toast(saved ? "즐겨찾기에 저장했어요." : "즐겨찾기에서 삭제했어요."); }
        catch (error) { if (error.code === "AUTH_REQUIRED") { document.getElementById("menu-detail").close(); location.href = "mypage.html?returnTo=" + encodeURIComponent(currentReturnUrl()); } else toast(error.message); }
      }
      const compare = event.target.closest("[data-compare]"); if (compare) api.toggleCompare(compare.dataset.compare);
    });
    window.addEventListener("cafe:favorites-changed", syncFavorites);
    window.addEventListener("cafe:auth-ready", () => { refreshAccount(); syncFavorites(); });
    window.addEventListener("cafe:session-changed", () => { refreshAccount(); syncFavorites(); });
    window.addEventListener("cafe:storage-unavailable", () => toast("브라우저 저장소를 사용할 수 없어 새로고침하면 변경 내용이 사라질 수 있어요."));
    window.addEventListener("storage", event => { if (event.key === null || event.key === "csm.demo.favorites.v1") window.dispatchEvent(new CustomEvent("cafe:favorites-changed")); if (event.key === null || event.key === "csm.demo.compare.v1") window.dispatchEvent(new CustomEvent("cafe:compare-changed")); });
    refreshAccount();
  }
  window.CafeUI = { escape, icon, number, price, brand, tone, cup, card, favoriteButton, empty, toast, showDetail, safeReturnUrl };
  init();
}());
