/* 공통 계약: 메뉴·지도는 기존 예시, 인증·즐겨찾기는 Supabase. */
(function () {
  "use strict";
  const data = window.CafeMock;
  const auth = window.CafeAuth;
  const keys = { compare: "csm.demo.compare.v1" };
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
  function notify(event) { window.dispatchEvent(new CustomEvent(event)); }
  window.CafeAPI = {
    mode: "supabase-auth/mock-catalog",
    authReady: auth.ready,
    getAuthStatus: () => auth.status(),
    getBrands: async () => data.brands,
    getCategories: async () => data.categories,
    getStores: async () => data.stores,
    getMenus: async function (filters = {}) {
      const q = String(filters.q || "").trim().toLocaleLowerCase();
      return data.menus.filter(m => (!filters.brandId || m.brandId === filters.brandId) && (!filters.category || m.categoryTags.includes(filters.category)) && (!q || m.name.toLocaleLowerCase().includes(q)) && (!filters.isNew || m.isNew));
    },
    getMenu: async id => data.menus.find(m => m.id === id) || null,
    getTrends: async () => data.trends,
    getSession: () => auth.getSession(),
    login: credentials => auth.signIn(credentials),
    signUp: credentials => auth.signUp(credentials),
    requestSignupVerification: email => auth.requestSignupVerification(email),
    completeSignup: details => auth.completeSignup(details),
    logout: () => auth.signOut(),
    updateProfile: name => auth.updateProfile(name),
    resendConfirmation: email => auth.resendConfirmation(email),
    sendPasswordReset: email => auth.sendPasswordReset(email),
    updatePassword: password => auth.updatePassword(password),
    getFavorites: async function () {
      if (!await auth.getSession()) return [];
      const ids = await auth.getFavoriteIds();
      return ids.map(id => data.menus.find(menu => menu.id === id)).filter(Boolean);
    },
    isFavorite: id => auth.isFavorite(id),
    toggleFavorite: async function (id) {
      if (!data.menus.some(m => m.id === id)) throw new Error("메뉴를 찾을 수 없습니다.");
      return auth.toggleFavorite(id);
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
