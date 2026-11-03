/* 4페이지 / 한정원. Supabase 계정·프로필·즐겨찾기 및 브라우저 권한 상태. */
(function () {
  "use strict";
  const api = window.CafeAPI, ui = window.CafeUI;
  let version = 0;
  let mode = "login";
  let busy = false;
  const byId = id => document.getElementById(id);
  function updateAuthNotice() {
    const status = api.getAuthStatus();
    byId("auth-status").hidden = status.configured && !status.dataError;
    byId("auth-status").textContent = status.error || status.dataError || "로그인 상태를 확인하고 있어요.";
  }
  function feedback(id, message, error) {
    const node = byId(id);
    node.textContent = message;
    node.hidden = !message;
    node.classList.toggle("is-error", Boolean(error));
  }
  function controls() {
    const status = api.getAuthStatus();
    ["auth-submit", "forgot-password", "resend-confirmation"].forEach(id => { byId(id).disabled = busy || !status.initialized || !status.configured; });
    byId("auth-submit").textContent = busy ? "처리 중…" : mode === "signup" ? "회원가입" : "로그인";
  }
  function switchMode(next) {
    if (busy) return;
    mode = next;
    const signup = next === "signup";
    byId("signup-name-group").hidden = !signup;
    byId("signup-confirm-group").hidden = !signup;
    byId("display-name").required = signup;
    byId("confirm-password").required = signup;
    byId("auth-password").minLength = signup ? 8 : 1;
    byId("auth-password").autocomplete = signup ? "new-password" : "current-password";
    byId("auth-password").value = "";
    byId("confirm-password").value = "";
    byId("auth-title").textContent = signup ? "나의 커피 노트 시작하기." : "다시 만나 반가워요.";
    byId("auth-description").textContent = signup ? "계정을 만들고 좋아하는 음료를 모아보세요." : "이메일로 로그인하고 저장한 음료를 확인하세요.";
    byId("forgot-password").hidden = signup;
    document.querySelectorAll("[data-auth-tab]").forEach(tab => { const selected = tab.dataset.authTab === mode; tab.setAttribute("aria-selected", String(selected)); tab.tabIndex = selected ? 0 : -1; });
    byId("login-form").setAttribute("aria-labelledby", signup ? "tab-signup" : "tab-login");
    feedback("form-feedback", "");
    controls();
  }
  async function render() {
    const current = ++version;
    const user = await api.getSession();
    if (current !== version) return;
    const status = api.getAuthStatus();
    updateAuthNotice();
    byId("login-section").hidden = Boolean(user);
    byId("recovery-section").hidden = !(user && status.recovery);
    byId("profile-section").hidden = !user || status.recovery;
    controls();
    if (!user) {
      byId("favorite-list").replaceChildren();
      byId("profile-name").textContent = "";
      byId("profile-email").textContent = "";
      byId("profile-display-name").value = "";
      return;
    }
    byId("profile-name").textContent = user.displayName;
    byId("profile-email").textContent = user.email;
    if (document.activeElement !== byId("profile-display-name")) byId("profile-display-name").value = user.displayName;
    byId("favorite-error").hidden = true;
    byId("favorite-list").innerHTML = ui.empty("저장한 음료를 불러오고 있어요", "잠시만 기다려 주세요.");
    try {
      const menus = await api.getFavorites();
      if (current !== version) return;
      updateAuthNotice();
      byId("favorite-count").textContent = String(menus.length).padStart(2, "0");
      byId("favorite-list").innerHTML = menus.length ? menus.map(menu => ui.card(menu)).join("") : ui.empty("아직 저장한 음료가 없어요", "메뉴에서 하트를 눌러 나만의 목록을 만들어 보세요.", true);
    } catch (error) {
      if (current !== version) return;
      updateAuthNotice();
      byId("favorite-count").textContent = "—";
      byId("favorite-list").replaceChildren();
      byId("favorite-error").hidden = false;
      byId("favorite-error-message").textContent = error.message;
    }
  }
  document.getElementById("login-form").addEventListener("submit", async event => {
    event.preventDefault();
    if (busy) return;
    if (mode === "signup" && byId("auth-password").value !== byId("confirm-password").value) { feedback("form-feedback", "비밀번호 확인이 일치하지 않아요.", true); return; }
    busy = true;
    controls();
    feedback("form-feedback", "");
    try {
      const credentials = { email: byId("auth-email").value, password: byId("auth-password").value, displayName: byId("display-name").value };
      let signedIn = true;
      if (mode === "signup") signedIn = (await api.signUp(credentials)).signedIn;
      else await api.login(credentials);
      byId("auth-password").value = "";
      byId("confirm-password").value = "";
      if (!signedIn) { feedback("form-feedback", "인증 안내 메일을 확인해 주세요. 기존 계정이 있다면 로그인하거나 인증 메일을 다시 요청할 수 있어요."); return; }
      const returnTo = ui.safeReturnUrl(new URLSearchParams(location.search).get("returnTo"));
      if (returnTo) location.href = returnTo;
      else { await render(); ui.toast("로그인했어요."); }
    } catch (error) { feedback("form-feedback", error.message, true); }
    finally { busy = false; controls(); }
  });
  byId("logout-button").addEventListener("click", async function () {
    this.disabled = true;
    try { await api.logout(); await render(); ui.toast("로그아웃했어요."); }
    catch (error) { ui.toast(error.message); }
    finally { this.disabled = false; }
  });
  document.querySelectorAll("[data-auth-tab]").forEach(tab => {
    tab.addEventListener("click", () => switchMode(tab.dataset.authTab));
    tab.addEventListener("keydown", event => { if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return; event.preventDefault(); const next = event.key === "Home" ? "login" : event.key === "End" ? "signup" : mode === "login" ? "signup" : "login"; switchMode(next); byId("tab-" + next).focus(); });
  });
  byId("toggle-password").addEventListener("click", function () { const visible = byId("auth-password").type === "password"; byId("auth-password").type = visible ? "text" : "password"; this.textContent = visible ? "숨기기" : "보기"; this.setAttribute("aria-pressed", String(visible)); this.setAttribute("aria-label", visible ? "비밀번호 숨기기" : "비밀번호 표시"); });
  async function emailAction(action, message) {
    if (busy || !byId("auth-email").reportValidity()) return;
    busy = true; controls();
    try { await action(byId("auth-email").value); feedback("form-feedback", message); }
    catch (error) { feedback("form-feedback", error.message, true); }
    finally { busy = false; controls(); }
  }
  byId("forgot-password").addEventListener("click", () => emailAction(email => api.sendPasswordReset(email), "해당 이메일의 계정이 있다면 비밀번호 재설정 안내가 발송됩니다. 메일의 링크를 같은 브라우저에서 열어 주세요."));
  byId("resend-confirmation").addEventListener("click", () => emailAction(email => api.resendConfirmation(email), "인증 안내를 요청했어요. 받은 편지함과 스팸함을 확인해 주세요."));
  byId("profile-form").addEventListener("submit", async event => {
    event.preventDefault(); const button = event.currentTarget.querySelector("button"); button.disabled = true;
    try { await api.updateProfile(byId("profile-display-name").value); feedback("profile-feedback", "표시 이름을 저장했어요."); }
    catch (error) { feedback("profile-feedback", error.message, true); }
    finally { button.disabled = false; }
  });
  byId("recovery-form").addEventListener("submit", async event => {
    event.preventDefault();
    if (byId("new-password").value !== byId("new-password-confirm").value) { feedback("recovery-feedback", "비밀번호 확인이 일치하지 않아요.", true); return; }
    const button = event.currentTarget.querySelector("button"); button.disabled = true;
    try { await api.updatePassword(byId("new-password").value); event.target.reset(); await render(); ui.toast("비밀번호를 변경했어요."); }
    catch (error) { feedback("recovery-feedback", error.message, true); }
    finally { button.disabled = false; }
  });
  byId("retry-favorites").addEventListener("click", render);
  let permissionStatus = null;
  function updatePermission(status) { const labels = { granted: "허용됨", denied: "거부됨", prompt: "아직 선택하지 않음" }; document.getElementById("location-status").textContent = labels[status.state] || "상태 확인 불가"; }
  document.getElementById("check-permission").addEventListener("click", async () => {
    if (!navigator.permissions || !navigator.permissions.query) { document.getElementById("location-status").textContent = "브라우저 설정에서 확인"; return; }
    try { if (!permissionStatus) { permissionStatus = await navigator.permissions.query({ name: "geolocation" }); permissionStatus.onchange = () => updatePermission(permissionStatus); } updatePermission(permissionStatus); }
    catch (_) { document.getElementById("location-status").textContent = "브라우저 설정에서 확인"; }
  });
  window.addEventListener("cafe:favorites-changed", render);
  window.addEventListener("cafe:session-changed", render);
  window.addEventListener("cafe:auth-ready", render);
  switchMode("login");
  render();
}());
