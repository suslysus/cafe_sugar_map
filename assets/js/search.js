/* 2페이지 / 강다은. 필터 조건은 URL에, 비교 선택은 공통 API 경계에 보관. */
(async function () {
  "use strict";
  const api = window.CafeAPI, ui = window.CafeUI;
  const [brands, categories] = await Promise.all([api.getBrands(), api.getCategories()]);
  const params = new URLSearchParams(location.search);
  let brandId = brands.some(b => b.id === params.get("brand")) ? params.get("brand") : "";
  let category = categories.some(c => c.id === params.get("category")) ? params.get("category") : "";
  let q = (params.get("q") || "").slice(0, 80);
  const sortSelect = document.getElementById("menu-sort");
  sortSelect.value = params.get("sort") || "";
  if (sortSelect.selectedIndex < 0) sortSelect.value = "";
  function sortMenus(menus) {
    const order = sortSelect.value;
    if (!order) return menus;
    const field = order === "sugar-asc" ? "sugarG" : "priceKrw";
    return [...menus].sort((a, b) => {
      const left = a[field], right = b[field];
      if (!Number.isFinite(left)) return Number.isFinite(right) ? 1 : 0;
      if (!Number.isFinite(right)) return -1;
      return order === "price-desc" ? right - left : left - right;
    });
  }
  let version = 0;
  document.getElementById("menu-query").value = q;
  function chip(id, label, type, active) { return '<button type="button" class="filter-chip" data-filter-type="' + type + '" data-value="' + ui.escape(id) + '" aria-pressed="' + active + '">' + ui.escape(label) + '</button>'; }
  function renderFilters() {
    document.getElementById("brand-filters").innerHTML = chip("", "전체", "brand", !brandId) + brands.map(b => chip(b.id, b.name, "brand", brandId === b.id)).join("");
    document.getElementById("category-filters").innerHTML = chip("", "전체", "category", !category) + categories.map(c => chip(c.id, c.name, "category", category === c.id)).join("");
  }
  function updateUrl() { const next = new URLSearchParams(); if (q) next.set("q", q); if (brandId) next.set("brand", brandId); if (category) next.set("category", category); if (sortSelect.value) next.set("sort", sortSelect.value); try { history.replaceState(null, "", location.pathname + (next.size ? "?" + next.toString() : "")); } catch (_) { /* file:// 환경에서는 URL 동기화만 생략 */ } }
  async function render() {
    const current = ++version;
    const menus = await api.getMenus({ brandId, category, q });
    if (current !== version) return;
    renderFilters(); updateUrl();
    document.getElementById("result-count").textContent = String(menus.length).padStart(2, "0");
    document.getElementById("search-results").innerHTML = menus.length ? sortMenus(menus).map(menu => ui.card(menu, { compare: true })).join("") : ui.empty("조건에 맞는 메뉴가 없어요", "다른 브랜드나 카테고리를 선택하거나 검색 조건을 초기화해 보세요.");
  }
  async function renderCompare() {
    const ids = api.getCompare();
    document.getElementById("compare-tray").hidden = !ids.length;
    document.getElementById("compare-count").textContent = ids.length;
    const menus = (await Promise.all(ids.map(id => api.getMenu(id)))).filter(Boolean);
    document.getElementById("compare-items").innerHTML = menus.map(menu => '<span class="compare-item">' + ui.escape(menu.name) + '<button type="button" data-compare="' + ui.escape(menu.id) + '" aria-label="' + ui.escape(menu.name) + ' 비교 선택 해제">×</button></span>').join("");
    document.querySelectorAll(".compare-button").forEach(button => { const selected = ids.includes(button.dataset.compare); button.setAttribute("aria-pressed", String(selected)); button.textContent = selected ? "✓ 비교 선택됨" : "+ 비교에 추가"; });
  }
  sortSelect.addEventListener("change", render);
  document.getElementById("search-form").addEventListener("submit", event => { event.preventDefault(); q = document.getElementById("menu-query").value.trim(); render(); });
  document.querySelector(".filter-panel").addEventListener("click", event => { const button = event.target.closest("[data-filter-type]"); if (!button) return; if (button.dataset.filterType === "brand") brandId = button.dataset.value; else category = button.dataset.value; render(); });
  document.getElementById("reset-filters").addEventListener("click", () => { brandId = ""; category = ""; q = ""; sortSelect.value = ""; document.getElementById("menu-query").value = ""; render(); });
  document.getElementById("clear-compare").addEventListener("click", () => api.clearCompare());
  window.addEventListener("cafe:compare-changed", renderCompare);
  await render(); await renderCompare();
}());
