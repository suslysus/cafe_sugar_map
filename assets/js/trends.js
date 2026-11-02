/* 3페이지 / 현준혁. 실제 수집 데이터·검색 관심도 연결 지점은 CafeAPI. */
(async function () {
  "use strict";
  const api = window.CafeAPI, ui = window.CafeUI;
  const [brands, trends] = await Promise.all([api.getBrands(), api.getTrends()]);
  const select = document.getElementById("new-brand-filter");
  select.innerHTML = '<option value="">전체 브랜드</option>' + brands.map(brand => '<option value="' + ui.escape(brand.id) + '">' + ui.escape(brand.name) + '</option>').join("");
  document.getElementById("trend-list").innerHTML = trends.length ? trends.map(trend => '<a class="trend-card tone-' + ui.tone(trend) + '" href="search.html?q=' + encodeURIComponent(trend.keyword) + '"><span class="trend-symbol" aria-hidden="true">✳</span><p class="eyebrow">' + ui.escape(trend.label) + '</p><h3>' + ui.escape(trend.title) + ' ↗</h3><p>' + ui.escape(trend.description) + '</p><span class="trend-source">예시 콘텐츠 · 출처/집계 기간 연동 예정</span></a>').join("") : ui.empty("확인된 트렌드가 없어요", "출처가 확인된 정보를 연결하면 이곳에 표시됩니다.");
  let version = 0;
  async function renderNewMenus() { const current = ++version; const menus = await api.getMenus({ brandId: select.value, isNew: true }); if (current !== version) return; document.getElementById("new-menu-list").innerHTML = menus.length ? menus.map(menu => ui.card(menu)).join("") : ui.empty("확인된 신메뉴가 없어요", "다른 브랜드를 선택해 보세요."); }
  select.addEventListener("change", renderNewMenus);
  await renderNewMenus();
}());
