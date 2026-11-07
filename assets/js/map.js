/* 1페이지 / 강민재.
   카카오 지도 연결판
   - config.js 의 kakaoJavaScriptKey 가 있고 SDK 로드에 성공하면: 카카오 지도 + 카카오 로컬 검색으로
     주변(검색 범위 500m)의 실제 프랜차이즈 매장을 표시합니다. (반경 원은 그리지 않음) (메뉴·가격·영양값은 기존 CafeAPI 예시 데이터)
   - 키가 없거나 SDK 로드에 실패하면: 기존 예시 SVG 지도로 자동 대체합니다. (키 없이도 팀원 누구나 실행 가능) */
(async function () {
  "use strict";
  const api = window.CafeAPI, ui = window.CafeUI;
  const $ = id => document.getElementById(id);

  const SEARCH_RADIUS_M = 500;                           // 매장 검색 범위(m). 지도에 원으로 표시하지는 않음
  const DEFAULT_LEVEL = 4;                               // 카카오 지도 확대 수준(작을수록 확대)
  const MIN_LEVEL = 3;                                   // 이보다 더 확대되지 않도록(매장이 가까이 몰려 있을 때)
  const SOONGSIL = { lat: 37.4963, lng: 126.9568 };      // 위치 허용 안 함/실패 시 기준: 숭실대 정문

  // 지도에서 브랜드를 한눈에 구분하기 위한 마커 색.
  // (이 페이지 전용 색. 전체 색을 바꾸려면 팀 협의 후 mock-data.js 수정)
  const PIN_STYLE = {
    starbucks: { color: "#476953", text: "#ffffff" },
    mega:      { color: "#FDD000", text: "#3d2c2e" },
    compose:   { color: "#FFDE00", text: "#3d2c2e" },
    paik:      { color: "#FFF200", text: "#3d2c2e" }
  };
  function pinStyle(brandId) {
    return PIN_STYLE[brandId] || { color: ui.brand(brandId).color, text: "#ffffff" };
  }

  const brands = await api.getBrands();                  // 공통 브랜드 목록 [{ id, name, ... }] (api.md 계약)
  const demoStores = await api.getStores();              // 예시 매장 (카카오 지도를 못 쓸 때의 대체 화면용)
  let stores = demoStores;
  let selectedId = stores[0] ? stores[0].id : null;
  let renderVersion = 0;                                 // 메뉴 로딩 경쟁 상태 방지
  let searchVersion = 0;                                 // 위치 변경 중 이전 검색 결과 무시용

  let live = false;                                      // true: 카카오 지도 사용 중
  let panelOpen = true;                                  // 오른쪽 메뉴창 열림 여부 (X 버튼으로 닫음)
  let permState = null;                                  // 마지막으로 확인한 위치 권한 상태
  let center = { lat: SOONGSIL.lat, lng: SOONGSIL.lng, mode: "default" };   // mode: default | gps
  let kmap = null, kOrigin = null, kPins = [];

  /* ------------------------------------------------------------------
     1. 오른쪽 카페·메뉴 패널 (지도 종류와 무관)
  ------------------------------------------------------------------ */
  // 매장 설명: 실제 매장은 주소 + 거리, 예시 매장은 기존 description
  function describe(store) {
    if (store.address) return store.address + (typeof store.distanceM === "number" ? " · 약 " + Math.round(store.distanceM) + "m" : "");
    return store.description || "";
  }

  async function renderPanel() {
    const version = ++renderVersion;
    const store = stores.find(item => item.id === selectedId);
    if (!store) {
      $("store-heading").innerHTML = ui.empty("표시할 카페가 없어요", live ? "주변에 대상 카페가 없어요. 위치를 바꿔 보세요." : "매장 데이터 연결 후 표시됩니다.");
      $("store-menu-list").innerHTML = "";
      return;
    }
    const menus = await api.getMenus({ brandId: store.brandId });
    if (version !== renderVersion) return;
    const brand = ui.brand(store.brandId), pin = pinStyle(store.brandId);
    $("store-heading").innerHTML = '<div class="store-header"><span class="store-brand-mark" style="--brand-color:' + pin.color + ';color:' + pin.text + '">' + brand.initial + '</span><div><h2 id="store-title">' + ui.escape(store.name) + '</h2><p>' + ui.escape(describe(store)) + '</p></div></div><div class="store-menu-heading"><strong>이 카페의 메뉴</strong><span>예시 메뉴 ' + menus.length + '개</span></div>';
    $("store-menu-list").innerHTML = menus.map(menu => '<article class="store-menu-row"><div class="mini-art tone-' + ui.tone(menu) + '">' + ui.cup(menu) + '</div><div class="store-menu-info"><button class="menu-title-button" type="button" data-detail="' + ui.escape(menu.id) + '">' + ui.escape(menu.name) + '</button><p class="menu-subtitle">' + ui.escape(menu.temperature) + ' · 최소 사이즈(예시)</p><p class="store-menu-numbers">당류 <strong>' + (menu.sugarG == null ? "확인 중" : ui.number(menu.sugarG) + "g") + '</strong> · ' + (menu.caloriesKcal == null ? "열량 확인 중" : ui.number(menu.caloriesKcal) + "kcal") + '</p><span class="menu-price">' + ui.price(menu.priceKrw) + '</span></div>' + ui.favoriteButton(menu) + '</article>').join("");
  }

  function selectStore(id) {
    selectedId = id;
    setPanelOpen(true);                                  // 닫혀 있었다면 다시 열기
    if (live) updateKakaoPinSelection(); else renderSvgPins();
    renderPanel();
  }

  // 메뉴창 열기/닫기. 지도 영역 크기가 바뀌므로 카카오 지도는 relayout 필요
  function setPanelOpen(open) {
    if (panelOpen === open) return;
    panelOpen = open;
    $("map-workspace").classList.toggle("panel-closed", !open);
    if (live && kmap) { const c = kmap.getCenter(); kmap.relayout(); kmap.setCenter(c); }   // 보던 위치·확대는 그대로 유지
  }

  // X 버튼: 메뉴창을 닫고 지도의 선택 표시도 해제
  function closePanel() {
    const closedId = selectedId;
    selectedId = null;
    renderVersion++;                                     // 진행 중이던 메뉴 로딩 결과는 버림
    if (live) updateKakaoPinSelection(); else renderSvgPins();
    setPanelOpen(false);
    // 키보드 사용자를 위해 방금 보던 핀으로 포커스 이동
    const pin = live ? (kPins.find(item => item.id === closedId) || {}).btn : document.querySelector('[data-store="' + closedId + '"]');
    if (pin && pin.focus) pin.focus();
  }

  /* ------------------------------------------------------------------
     2. 예시(SVG) 지도 - 기존 동작 그대로. 키가 없을 때의 대체 화면
  ------------------------------------------------------------------ */
  function renderSvgPins() {
    $("map-pins").innerHTML = stores.map(item => { const b = ui.brand(item.brandId), pin = pinStyle(item.brandId); return '<button type="button" class="map-pin" data-store="' + ui.escape(item.id) + '" style="left:' + item.x + '%;top:' + item.y + '%;--brand-color:' + pin.color + ';color:' + pin.text + '" aria-label="' + ui.escape(item.name) + ' 선택" aria-pressed="' + (item.id === selectedId) + '">' + b.initial + '<span class="pin-label">' + ui.escape(b.name) + '</span></button>'; }).join("");
  }

  /* ------------------------------------------------------------------
     3. 카카오 SDK 로드 (키는 공용 config.js 에서만 읽음. map.js 에 직접 쓰지 않음)
  ------------------------------------------------------------------ */
  function loadKakaoSdk(appKey) {
    return new Promise((resolve, reject) => {
      const ready = () => window.kakao && window.kakao.maps && window.kakao.maps.services;
      if (ready()) { resolve(); return; }
      const timer = setTimeout(() => reject(new Error("카카오 SDK 로드 시간 초과")), 8000);
      const script = document.createElement("script");
      script.src = "https://dapi.kakao.com/v2/maps/sdk.js?appkey=" + encodeURIComponent(appKey) + "&libraries=services&autoload=false";
      script.onload = () => {
        if (!window.kakao || !window.kakao.maps || !window.kakao.maps.load) { clearTimeout(timer); reject(new Error("카카오 SDK 형식 오류")); return; }
        window.kakao.maps.load(() => { clearTimeout(timer); ready() ? resolve() : reject(new Error("services 라이브러리 없음")); });
      };
      script.onerror = () => { clearTimeout(timer); reject(new Error("카카오 SDK 요청 실패")); };
      document.head.appendChild(script);
    });
  }

  /* ------------------------------------------------------------------
     4. 카카오 지도: 지도 생성, 기준 위치, 매장 핀
  ------------------------------------------------------------------ */
  function createKakaoMap() {
    kmap = new kakao.maps.Map($("kakao-map"), { center: new kakao.maps.LatLng(center.lat, center.lng), level: DEFAULT_LEVEL });
    kmap.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
  }

  function drawCenter() {
    const pos = new kakao.maps.LatLng(center.lat, center.lng);
    if (kOrigin) kOrigin.setMap(null);
    const dot = document.createElement("span");
    dot.className = "map-origin kakao-origin";
    dot.setAttribute("aria-label", center.mode === "gps" ? "현재 위치" : "기본 위치");
    dot.appendChild(document.createElement("span"));
    kOrigin = new kakao.maps.CustomOverlay({ map: kmap, position: pos, content: dot, xAnchor: 0.5, yAnchor: 0.5, zIndex: 5 });
    kmap.setCenter(pos);
    kmap.setLevel(DEFAULT_LEVEL);
  }

  // 기준 위치(내 위치)가 항상 지도 한가운데 오도록 범위 조정:
  // 매장 좌표와 "기준 위치를 중심으로 한 대칭 좌표"를 함께 포함시켜 범위의 중심이 기준 위치가 되게 함
  function fitToStores() {
    const c = new kakao.maps.LatLng(center.lat, center.lng);
    if (!stores.length) { kmap.setCenter(c); kmap.setLevel(DEFAULT_LEVEL); return; }
    const bounds = new kakao.maps.LatLngBounds();
    bounds.extend(c);
    stores.forEach(store => {
      bounds.extend(new kakao.maps.LatLng(store.latitude, store.longitude));
      bounds.extend(new kakao.maps.LatLng(2 * center.lat - store.latitude, 2 * center.lng - store.longitude));
    });
    kmap.setBounds(bounds, 40, 40, 40, 40);
    if (kmap.getLevel() < MIN_LEVEL) kmap.setLevel(MIN_LEVEL);
    kmap.setCenter(c);                                   // 확대 수준을 바꾼 뒤에도 내 위치를 정중앙에
  }

  function clearKakaoPins() {
    kPins.forEach(pin => pin.overlay.setMap(null));
    kPins = [];
  }

  function drawKakaoPins() {
    clearKakaoPins();
    stores.forEach(store => {
      const b = ui.brand(store.brandId), pin = pinStyle(store.brandId);
      const selected = store.id === selectedId;
      const btn = document.createElement("button");           // textContent/setAttribute 만 사용 → 외부 문자열이 HTML로 해석되지 않음
      btn.type = "button";
      btn.className = "map-pin kakao-pin";
      btn.style.setProperty("--brand-color", pin.color);
      btn.style.color = pin.text;
      btn.setAttribute("aria-label", store.name + " 선택");
      btn.setAttribute("aria-pressed", String(selected));
      btn.textContent = b.initial;
      const label = document.createElement("span");
      label.className = "pin-label";
      label.textContent = b.name;
      btn.appendChild(label);
      btn.addEventListener("click", () => selectStore(store.id));
      const overlay = new kakao.maps.CustomOverlay({ map: kmap, position: new kakao.maps.LatLng(store.latitude, store.longitude), content: btn, xAnchor: 0.5, yAnchor: 1, zIndex: selected ? 20 : 10, clickable: true });
      kPins.push({ id: store.id, btn: btn, overlay: overlay });
    });
  }

  function updateKakaoPinSelection() {
    kPins.forEach(pin => {
      const on = pin.id === selectedId;
      pin.btn.setAttribute("aria-pressed", String(on));
      pin.overlay.setZIndex(on ? 20 : 10);
    });
  }

  function updateToolbar(searching) {
    $("map-place").textContent = center.mode === "gps" ? "내 위치 주변" : "숭실대학교 주변";
    $("map-source").textContent = (center.mode === "gps" ? "현재 위치" : "기본 위치") + " · " + (searching ? "카페 찾는 중..." : "주변 " + stores.length + "곳");
  }

  /* ------------------------------------------------------------------
     5. 주변(검색 범위 500m) 실제 매장 검색 (카카오 로컬 / services 라이브러리)
        ※ 반환하는 매장 모양은 docs/api.md 의 매장 DTO({ id, brandId, name, latitude, longitude })를 따릅니다.
          나중에 서버 API(GET /stores?lat&lng&radiusM)가 생기면 fetchNearbyStores() 안만
          api.getStores({ lat, lng, radiusM }) 호출로 바꾸면 됩니다. (address, distanceM 는 선택 필드)
  ------------------------------------------------------------------ */
  // 브랜드 표시 이름 → 카카오 검색어 / 상호 판별어. 규칙에 없는 브랜드는 이름 그대로 검색
  const SEARCH_RULES = [
    { test: /스타벅스/, keywords: ["스타벅스"], nameKeys: ["스타벅스"] },
    { test: /메가/,     keywords: ["메가MGC커피", "메가커피"], nameKeys: ["메가MGC커피", "메가커피", "메가엠지씨"] },
    { test: /컴포즈/,   keywords: ["컴포즈커피"], nameKeys: ["컴포즈"] },
    { test: /빽다방/,   keywords: ["빽다방"], nameKeys: ["빽다방"] }
  ];
  function searchSpecFor(brandName) {
    return SEARCH_RULES.find(rule => rule.test.test(brandName)) || { keywords: [brandName], nameKeys: [brandName] };
  }

  function distanceM(a, b) {
    const R = 6371000, rad = Math.PI / 180;
    const dLat = (b.lat - a.lat) * rad, dLng = (b.lng - a.lng) * rad;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  }

  // 키워드 하나를 검색 범위 안에서 검색 (최대 3페이지 = 45건)
  function searchPlaces(keyword, c) {
    return new Promise(resolve => {
      const Status = kakao.maps.services.Status;
      const items = [];
      new kakao.maps.services.Places().keywordSearch(keyword, (data, status, pagination) => {
        if (status === Status.OK) {
          items.push(...data);
          if (pagination.hasNextPage && pagination.current < 3) { pagination.nextPage(); return; }   // 같은 콜백이 다음 페이지로 다시 호출됨
          resolve({ items: items, error: false });
        } else {
          resolve({ items: items, error: status === Status.ERROR });
        }
      }, { location: new kakao.maps.LatLng(c.lat, c.lng), radius: SEARCH_RADIUS_M, sort: kakao.maps.services.SortBy.DISTANCE, size: 15 });
    });
  }

  async function fetchNearbyStores(c) {
    const found = new Map();
    let failed = 0;
    await Promise.all(brands.map(async brand => {
      const spec = searchSpecFor(brand.name);
      for (const keyword of spec.keywords) {
        const result = await searchPlaces(keyword, c);
        if (result.error) failed++;
        result.items.forEach(place => {
          const isCafe = place.category_group_code === "CE7";                         // 카카오 '카페' 카테고리
          const nameOk = spec.nameKeys.some(key => place.place_name.includes(key));   // 상호에 브랜드명 포함
          if (!isCafe || !nameOk || found.has(place.id)) return;
          const lat = parseFloat(place.y), lng = parseFloat(place.x);
          const d = distanceM(c, { lat: lat, lng: lng });
          if (d > SEARCH_RADIUS_M) return;                                                   // 안전장치: 검색 범위 초과 제외
          found.set(place.id, {
            id: "kakao-" + place.id,
            brandId: brand.id,
            name: place.place_name,
            latitude: lat, longitude: lng,
            address: place.road_address_name || place.address_name || "주소 정보 없음",
            distanceM: d
          });
        });
      }
    }));
    return { stores: Array.from(found.values()).sort((a, b) => a.distanceM - b.distanceM), failed: failed };
  }

  async function loadLiveStores() {
    const version = ++searchVersion;
    clearKakaoPins();                                    // 이전 위치의 핀 제거
    updateToolbar(true);
    const result = await fetchNearbyStores(center);
    if (version !== searchVersion) return;               // 그 사이 위치가 또 바뀌었으면 무시
    stores = result.stores;
    selectedId = panelOpen && stores[0] ? stores[0].id : null;   // 가장 가까운 매장을 기본 선택 (메뉴창을 닫아 둔 경우는 선택 없음)
    drawKakaoPins();
    fitToStores();
    updateToolbar(false);
    renderPanel();
    if (!stores.length) {
      ui.toast(result.failed ? "주변 카페를 불러오지 못했어요. 카카오 앱의 카카오맵 사용 설정과 도메인 등록을 확인해 주세요." : "주변에 대상 카페가 없어요.");
    }
  }

  function defaultCenter() { return { lat: SOONGSIL.lat, lng: SOONGSIL.lng, mode: "default" }; }

  function moveTo(next) {
    center = next;
    drawCenter();
    loadLiveStores();
  }

  /* ------------------------------------------------------------------
     6. 현재 위치: 허용 → 내 위치 / 거부·실패 → 숭실대 기준 유지
  ------------------------------------------------------------------ */
  // auto=true: 페이지에 들어오자마자 자동 요청. 허용하면 안내 없이 내 위치로 이동, 거부/실패하면 안내 후 숭실대 기준으로 표시
  // 내 위치(gps)를 보던 중 재조회가 실패하면(권한 거부 1 · 위치 확인 불가 2 · 시간 초과 3 · 기타) 오류 종류와 관계없이 숭실대로 복귀
  // 모바일 대응: 카톡·인스타 등 앱 내장 브라우저는 위치 권한 창이 막히는 경우가 많아 안내한다
  const IN_APP_BROWSER = /KAKAOTALK|NAVER\(inapp|Instagram|FBAN|FBAV|Line\/|DaumApps/i.test(navigator.userAgent);

  // 1차: 네트워크·Wi-Fi 기반(빠르고 실내에서도 잘 됨), 2차: 1차가 위치 확인 불가·시간 초과일 때만 GPS(고정밀)로 재시도
  // (이전에는 처음부터 GPS 고정밀 + 10초 제한이라 모바일 실내에서 시간 초과가 잦았음)
  function getPosition(fresh) {   // fresh=true: 캐시 없이 새로 측정(사용자가 ⌖를 직접 누른 경우), false: 1분 이내 캐시 허용(자동 요청)
    const ask = options => new Promise((resolve, reject) => navigator.geolocation.getCurrentPosition(resolve, reject, options));
    return ask({ enableHighAccuracy: false, timeout: 15000, maximumAge: fresh ? 0 : 60000 }).catch(error => {
      if (error && error.code === 1) throw error;        // 권한 거부는 재시도해도 같으므로 바로 실패 처리
      return ask({ enableHighAccuracy: true, timeout: 20000, maximumAge: 0 });
    });
  }

  // 안내 문구는 PC·모바일을 구분하지 않고 공통 표현을 쓴다(앱 내장 브라우저만 별도 안내)
  function locationHelp(code) {
    if (code === 1) return IN_APP_BROWSER
      ? " 앱 안의 브라우저에서는 위치 권한이 막힐 수 있어요. 우측 메뉴에서 'Chrome/Safari로 열기'를 이용해 주세요."
      : " 브라우저의 사이트 설정에서 위치 권한을 '허용'으로 바꿔 주세요.";
    if (code === 2 || code === 3) return " 기기의 위치 서비스가 켜져 있는지, 네트워크에 연결되어 있는지 확인해 주세요.";
    return "";
  }

  function locate(auto) {
    if (!live) { ui.toast("실제 지도 연결 전에는 기본 위치(숭실대)로 표시됩니다."); return; }
    if (!window.isSecureContext) { ui.toast("현재 위치는 localhost 또는 HTTPS 주소에서만 사용할 수 있어요. 숭실대 기준으로 보여드려요."); return; }
    if (!navigator.geolocation) { ui.toast("이 브라우저는 위치 기능을 지원하지 않아요. 숭실대 기준으로 보여드려요."); return; }
    const button = $("locate-button");
    button.disabled = true;
    getPosition(!auto).then(
      position => {
        button.disabled = false;
        moveTo({ lat: position.coords.latitude, lng: position.coords.longitude, mode: "gps" });   // 내 위치를 중심으로 이동 + 주변 재검색
        if (!auto) ui.toast("현재 위치로 이동했어요.");
      },
      error => {
        button.disabled = false;
        const reason = { 1: "위치 권한이 허용되지 않아", 2: "현재 위치를 확인할 수 없어", 3: "위치 조회 시간이 초과되어" }[error.code] || "위치를 가져오지 못해";
        const wasGps = center.mode === "gps";
        if (wasGps) moveTo(defaultCenter());                                      // 내 위치를 보던 중 어떤 이유로든 실패하면 안내 문구대로 숭실대로 복귀 (오류 1·2·3 공통)
        ui.toast(reason + (wasGps ? " 숭실대 기준으로 돌아왔어요." : " 숭실대 기준으로 보여드려요.") + locationHelp(error.code));
      }
    );
  }

  // 브라우저에서 위치 권한을 나중에 바꿔도 따라가기: 차단하면 숭실대로 복귀, 다시 허용하면 내 위치로 이동
  function applyPermission(state) {
    const prev = permState;
    permState = state;
    if (!live || state === prev) return;
    if (state === "denied" && center.mode === "gps") {
      moveTo(defaultCenter());
      ui.toast("위치 권한이 차단되어 숭실대 기준으로 돌아왔어요.");
    } else if (state === "granted" && center.mode === "default") {
      locate(false);
    }
  }

  function watchLocationPermission() {
    if (!window.isSecureContext || !navigator.permissions || !navigator.permissions.query) return;
    const query = () => navigator.permissions.query({ name: "geolocation" });
    query().then(status => {
      permState = status.state;
      status.addEventListener("change", () => applyPermission(status.state));          // 대부분의 브라우저: 권한 변경 이벤트
    }).catch(() => {});
    // 일부 브라우저는 change 이벤트가 없어서, 설정을 바꾸고 돌아왔을 때 다시 확인
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) query().then(status => applyPermission(status.state)).catch(() => {});
    });
  }

  /* ------------------------------------------------------------------
     7. 시작
  ------------------------------------------------------------------ */
  function startDemo() {
    live = false;
    stores = demoStores;
    selectedId = stores[0] ? stores[0].id : null;
    renderSvgPins();
    renderPanel();
  }

  async function startLive() {
    live = true;
    stores = [];
    selectedId = null;
    $("map-canvas").classList.add("is-live");
    $("kakao-map").hidden = false;                       // 크기가 있는 상태에서 지도를 만들어야 함
    createKakaoMap();
    drawCenter();
    $("demo-notice").textContent = "지도와 매장 위치는 카카오 지도 기준 실제 정보입니다. 메뉴·가격·영양값은 예시이며 실제 정보가 아닙니다.";
    watchLocationPermission();
    locate(true);                                        // 위치 허용 요청 (숭실대 주변 검색과 동시에 진행)
    await loadLiveStores();
  }

  function stopLive() {                                  // 카카오 쪽 초기화에 실패했을 때 예시 지도로 되돌림
    live = false;
    searchVersion++;
    clearKakaoPins();
    $("map-canvas").classList.remove("is-live");
    $("kakao-map").hidden = true;
    $("map-place").textContent = "숭실대학교 주변";
    $("map-source").textContent = "기본 위치 · 예시 지도";
  }

  $("map-pins").addEventListener("click", event => { const pin = event.target.closest("[data-store]"); if (pin) selectStore(pin.dataset.store); });
  $("locate-button").addEventListener("click", () => locate(false));
  $("store-close").addEventListener("click", closePanel);

  const key = window.CafeConfig && window.CafeConfig.kakaoJavaScriptKey;   // 공용 assets/js/config.js 의 공개 브라우저 키
  if (key && !String(key).startsWith("여기에")) {
    try {
      await loadKakaoSdk(key);
      await startLive();
      return;
    } catch (error) {
      console.warn("[map] 카카오 지도를 사용할 수 없어 예시 지도로 대체합니다:", error);
      stopLive();
      ui.toast("카카오 지도를 불러오지 못해 예시 지도로 표시해요. (키·도메인 등록을 확인해 주세요)");
    }
  } else {
    console.info("[map] config.js 의 kakaoJavaScriptKey 가 비어 있어 예시 지도로 표시합니다.");
  }
  startDemo();
}());