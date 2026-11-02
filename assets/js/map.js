/* 1페이지 / 강민재. 실제 지도·위치 요청은 아직 연결하지 않음. */
(async function () {
  "use strict";
  const api = window.CafeAPI, ui = window.CafeUI;
  const stores = await api.getStores();
  let selectedId = stores[0] ? stores[0].id : null;
  let renderVersion = 0;
  async function renderStore() {
    const version = ++renderVersion;
    const store = stores.find(item => item.id === selectedId);
    if (!store) { document.getElementById("store-heading").innerHTML = ui.empty("표시할 카페가 없어요", "매장 데이터 연결 후 표시됩니다."); return; }
    const menus = await api.getMenus({ brandId: store.brandId });
    if (version !== renderVersion) return;
    const brand = ui.brand(store.brandId);
    document.getElementById("map-pins").innerHTML = stores.map(item => { const b = ui.brand(item.brandId); return '<button type="button" class="map-pin" data-store="' + ui.escape(item.id) + '" style="left:' + item.x + '%;top:' + item.y + '%;--brand-color:' + b.color + '" aria-label="' + ui.escape(item.name) + ' 선택" aria-pressed="' + (item.id === selectedId) + '">' + b.initial + '<span class="pin-label">' + ui.escape(b.name) + '</span></button>'; }).join("");
    document.getElementById("store-heading").innerHTML = '<div class="store-header"><span class="store-brand-mark" style="--brand-color:' + brand.color + '">' + brand.initial + '</span><div><h2 id="store-title">' + ui.escape(store.name) + '</h2><p>' + ui.escape(store.description) + '</p></div></div><div class="store-menu-heading"><strong>이 카페의 메뉴</strong><span>예시 메뉴 ' + menus.length + '개</span></div>';
    document.getElementById("store-menu-list").innerHTML = menus.map(menu => '<article class="store-menu-row"><div class="mini-art tone-' + ui.tone(menu) + '">' + ui.cup(menu) + '</div><div class="store-menu-info"><button class="menu-title-button" type="button" data-detail="' + ui.escape(menu.id) + '">' + ui.escape(menu.name) + '</button><p class="menu-subtitle">' + ui.escape(menu.temperature) + ' · 최소 사이즈(예시)</p><p class="store-menu-numbers">당류 <strong>' + (menu.sugarG == null ? "확인 중" : ui.number(menu.sugarG) + "g") + '</strong> · ' + (menu.caloriesKcal == null ? "열량 확인 중" : ui.number(menu.caloriesKcal) + "kcal") + '</p><span class="menu-price">' + ui.price(menu.priceKrw) + '</span></div>' + ui.favoriteButton(menu) + '</article>').join("");
  }
  document.getElementById("map-pins").addEventListener("click", event => { const pin = event.target.closest("[data-store]"); if (pin) { selectedId = pin.dataset.store; renderStore(); } });
  document.getElementById("locate-button").addEventListener("click", () => ui.toast("현재 위치와 실제 지도는 담당 페이지 개발 시 연결합니다. 기본 위치는 숭실대입니다."));
  await renderStore();
}());
