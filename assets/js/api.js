/* 공통 데이터 접근 경계. 실제 서버 연결 시 이 파일을 교체하고 화면의 함수 계약은 유지한다. */
(function () {
  "use strict";
  const data = window.CafeMock;
  const keys = { session: "csm.demo.session.v1", favorites: "csm.demo.favorites.v1", compare: "csm.demo.compare.v1" };
  const memory = {};
  let storageWarning = false;
  function read(key, fallback, session) {
    try { const value = (session ? sessionStorage : localStorage).getItem(key); return value ? JSON.parse(value) : fallback; }
    catch (_) { return memory[key] || fallback; }
  }
  function write(key, value, session) {
    memory[key] = value;
    try { (session ? sessionStorage : localStorage).setItem(key, JSON.stringify(value)); }
    catch (_) { if (!storageWarning) { storageWarning = true; window.dispatchEvent(new CustomEvent("cafe:storage-unavailable")); } }
  }
  function validIds(value) { return Array.isArray(value) ? Array.from(new Set(value.filter(id => data.menus.some(m => m.id === id)))) : []; }
  function favorites() { return validIds(read(keys.favorites, [])); }
  function session() { const user = read(keys.session, null, true); return user && user.id === "demo-user" && typeof user.displayName === "string" ? user : null; }
  function notify(event) { window.dispatchEvent(new CustomEvent(event)); }
  window.CafeAPI = {
    mode: "mock",
    getBrands: async () => data.brands,
    getCategories: async () => data.categories,
    getStores: async () => data.stores,
    getMenus: async function (filters = {}) {
      const q = String(filters.q || "").trim().toLocaleLowerCase();
      return data.menus.filter(m => (!filters.brandId || m.brandId === filters.brandId) && (!filters.category || m.categoryTags.includes(filters.category)) && (!q || m.name.toLocaleLowerCase().includes(q)) && (!filters.isNew || m.isNew));
    },
    getMenu: async id => data.menus.find(m => m.id === id) || null,
    getTrends: async () => data.trends,
    getSession: async () => session(),
    login: async function ({ displayName }) {
      const name = String(displayName || "").trim();
      if (!name || name.length > 24) throw new Error("표시 이름을 1~24자로 입력해 주세요.");
      const user = { id: "demo-user", displayName: name, isDemo: true };
      write(keys.session, user, true); notify("cafe:session-changed"); return user;
    },
    logout: async function () { write(keys.session, null, true); notify("cafe:session-changed"); },
    getFavorites: async () => session() ? data.menus.filter(m => favorites().includes(m.id)) : [],
    isFavorite: id => Boolean(session() && favorites().includes(id)),
    toggleFavorite: async function (id) {
      if (!session()) { const error = new Error("즐겨찾기는 데모 로그인 후 사용할 수 있어요."); error.code = "AUTH_REQUIRED"; throw error; }
      if (!data.menus.some(m => m.id === id)) throw new Error("메뉴를 찾을 수 없습니다.");
      const ids = favorites(); const next = ids.includes(id) ? ids.filter(item => item !== id) : ids.concat(id);
      write(keys.favorites, next); notify("cafe:favorites-changed"); return next.includes(id);
    },
    getCompare: () => validIds(read(keys.compare, [])),
    toggleCompare: function (id) {
      if (!data.menus.some(m => m.id === id)) return;
      const ids = this.getCompare();
      write(keys.compare, ids.includes(id) ? ids.filter(item => item !== id) : ids.concat(id)); notify("cafe:compare-changed");
    },
    clearCompare: function () { write(keys.compare, []); notify("cafe:compare-changed"); }
  };
}());
