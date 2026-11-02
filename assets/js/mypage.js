/* 4페이지 / 한정원. 데모 세션은 실제 인증이 아니며 비밀번호를 수집하지 않음. */
(function () {
  "use strict";
  const api = window.CafeAPI, ui = window.CafeUI;
  let version = 0;
  async function render() {
    const current = ++version;
    const user = await api.getSession();
    const menus = user ? await api.getFavorites() : [];
    if (current !== version) return;
    document.getElementById("login-section").hidden = Boolean(user);
    document.getElementById("profile-section").hidden = !user;
    document.getElementById("profile-name").textContent = user ? user.displayName : "";
    document.getElementById("favorite-count").textContent = String(menus.length).padStart(2, "0");
    document.getElementById("favorite-list").innerHTML = menus.length ? menus.map(menu => ui.card(menu)).join("") : ui.empty("아직 저장한 음료가 없어요", "메뉴에서 하트를 눌러 나만의 목록을 만들어 보세요.", true);
  }
  document.getElementById("login-form").addEventListener("submit", async event => {
    event.preventDefault();
    try { await api.login({ displayName: document.getElementById("display-name").value }); const returnTo = ui.safeReturnUrl(new URLSearchParams(location.search).get("returnTo")); if (returnTo) location.href = returnTo; else { await render(); ui.toast("데모 로그인했어요. 실제 인증은 연결되지 않았습니다."); } }
    catch (error) { ui.toast(error.message); }
  });
  document.getElementById("logout-button").addEventListener("click", async () => { await api.logout(); await render(); ui.toast("로그아웃했어요. 이 브라우저의 데모 저장 목록은 유지됩니다."); });
  let permissionStatus = null;
  function updatePermission(status) { const labels = { granted: "허용됨", denied: "거부됨", prompt: "아직 선택하지 않음" }; document.getElementById("location-status").textContent = labels[status.state] || "상태 확인 불가"; }
  document.getElementById("check-permission").addEventListener("click", async () => {
    if (!navigator.permissions || !navigator.permissions.query) { document.getElementById("location-status").textContent = "브라우저 설정에서 확인"; return; }
    try { if (!permissionStatus) { permissionStatus = await navigator.permissions.query({ name: "geolocation" }); permissionStatus.onchange = () => updatePermission(permissionStatus); } updatePermission(permissionStatus); }
    catch (_) { document.getElementById("location-status").textContent = "브라우저 설정에서 확인"; }
  });
  window.addEventListener("cafe:favorites-changed", render);
  window.addEventListener("cafe:session-changed", render);
  render();
}());
